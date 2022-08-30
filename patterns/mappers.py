import sqlite3
import inspect


class Mapper:
    """architectural_system_pattern"""

    def __init__(self, connection, obj_class):
        self.connection = connection
        self.cursor = connection.cursor()
        self.tablename = obj_class.__name__.lower()
        self.obj_class = obj_class

    def all(self):
        statement = f'SELECT * from {self.tablename}'
        self.cursor.execute(statement)
        result = []
        for item in self.cursor.fetchall():
            id, item = item[0], item[1:]
            obj = self.obj_class(*item)
            obj.id = id
            result.append(obj)
        return result

    def find_by_id(self, id):
        statement = f"SELECT id, {', '.join(self.obj_class.fields)} FROM {self.tablename} WHERE id=?"
        self.cursor.execute(statement, (id,))
        result = list(self.cursor.fetchone())
        if result:
            obj = self.obj_class(*result[1:len(self.obj_class.fields) + 1])
            obj.id = result[0]
            return obj
        else:
            raise RecordNotFoundException(f'record with id={id} not found')

    def insert(self, obj):
        fields = self.obj_class.fields
        statement = f"INSERT INTO {self.tablename} ({', '.join(fields)}) VALUES ({', '.join('?' for _ in fields)})"
        self.cursor.execute(statement, (*obj.get_from_fields(),))
        try:
            self.connection.commit()
        except Exception as e:
            raise DbCommitException(e.args)

    def update(self, obj):
        set_string = ', '.join([f'{f}=?' for f in self.obj_class.fields])
        statement = f"UPDATE {self.tablename} SET {set_string} WHERE id=?"
        self.cursor.execute(statement, (*obj.get_from_fields(), obj.id))
        try:
            self.connection.commit()
        except Exception as e:
            raise DbUpdateException(e.args)

    def delete(self, obj):
        statement = f"DELETE FROM {self.tablename} WHERE id=?"
        self.cursor.execute(statement, (obj.id,))
        try:
            self.connection.commit()
        except Exception as e:
            raise DbDeleteException(e.args)

    def add_parent(self, obj, obj_p):
        parent_name = obj_p.__class__.__name__.lower()
        statement = f"INSERT INTO {self.tablename}_{parent_name} ({self.tablename}_id, {parent_name}_pid) VALUES (?, ?)"
        self.cursor.execute(statement, (obj.id, obj_p.id))
        try:
            self.connection.commit()
        except Exception as e:
            raise DbCommitException(e.args)

    def get_related(self, obj, other_class, direction):
        class_name = other_class.__name__.lower()
        sel_string = ', '.join([f'O.{f}' for f in other_class.fields])

        if direction == 'child':
            statement = f'SELECT DISTINCT (O.id), {sel_string} from {class_name} O ' \
                        f'JOIN {self.tablename} P ON PO.{self.tablename}_pid = {obj.id} ' \
                        f'JOIN {class_name}_{self.tablename} PO ON PO.{class_name}_id = O.id'
        else:
            statement = f'SELECT DISTINCT (O.id), {sel_string} from {class_name} O ' \
                        f'JOIN {self.tablename} C ON CO.{self.tablename}_id = {obj.id} ' \
                        f'JOIN {self.tablename}_{class_name} CO ON CO.{class_name}_pid = O.id'

        self.cursor.execute(statement)
        result = []
        for obj_ch in self.cursor.fetchall():
            obj = other_class(*obj_ch[1:len(other_class.fields) + 1])
            obj.id = obj_ch[0]
            result.append(obj)
        return result


class DbCommitException(Exception):
    def __init__(self, message):
        super().__init__(f'Db commit error: {message}')


class DbUpdateException(Exception):
    def __init__(self, message):
        super().__init__(f'Db update error: {message}')


class DbDeleteException(Exception):
    def __init__(self, message):
        super().__init__(f'Db delete error: {message}')


class RecordNotFoundException(Exception):
    def __init__(self, message):
        super().__init__(f'Record not found: {message}')


connection = sqlite3.connect('patterns.sqlite')


class MapperRegistry:
    """Data Mapper - архитектурный системный паттерн"""
    mappers = {}

    @staticmethod
    def get_mapper(obj):
        if not inspect.isclass(obj):
            obj = obj.__class__
        name = obj.__name__.lower()
        try:
            return MapperRegistry.mappers[name](connection, obj)
        except Exception as e:
            MapperRegistry.mappers[name] = Mapper
            return MapperRegistry.mappers[name](connection, obj)
