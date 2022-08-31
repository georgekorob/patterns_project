import sqlite3
import inspect


class Mapper:
    """architectural_system_pattern"""

    def __init__(self, connection, obj_class):
        # super().__init__(connection)
        self.connection = connection
        self.cursor = connection.cursor()
        self.tablename = obj_class.tablename
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

    def last(self):
        statement = f'SELECT * from {self.tablename} ' \
                    f'ORDER BY id DESC LIMIT 1'
        self.cursor.execute(statement)
        item = self.cursor.fetchone()
        id, item = item[0], item[1:]
        obj = self.obj_class(*item)
        obj.id = id
        return obj

    def find_by_id(self, id):
        statement = f"SELECT id, {', '.join(self.obj_class.fields)} " \
                    f"FROM {self.tablename} " \
                    f"WHERE id=?"
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
        statement = f"INSERT INTO {self.tablename} " \
                    f"({', '.join(fields)}) " \
                    f"VALUES ({', '.join('?' for _ in fields)})"
        self.cursor.execute(statement, (*obj.get_from_fields(),))
        try:
            self.connection.commit()
        except Exception as e:
            raise DbCommitException(e.args)

    def update(self, obj):
        set_string = ', '.join([f'{f}=?' for f in self.obj_class.fields])
        statement = f"UPDATE {self.tablename} " \
                    f"SET {set_string} " \
                    f"WHERE id=?"
        self.cursor.execute(statement, (*obj.get_from_fields(), obj.id))
        try:
            self.connection.commit()
        except Exception as e:
            raise DbUpdateException(e.args)

    def delete(self, id):
        statement = f"DELETE FROM {self.tablename} " \
                    f"WHERE id=?"
        self.cursor.execute(statement, (id,))
        try:
            self.connection.commit()
        except Exception as e:
            raise DbDeleteException(e.args)


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
    # mappers_relation = {}

    @staticmethod
    def get_mapper(obj):
        name = obj.tablename
        try:
            return MapperRegistry.mappers[name](connection, obj)
        except Exception:
            MapperRegistry.mappers[name] = Mapper
            return MapperRegistry.mappers[name](connection, obj)
        # elif len(obj) == 2:
        #     class1, class2 = [q if inspect.isclass(q) else q for q in obj]
        #     name = f'{class1.__name__.lower()}_{class2.__name__.lower()}'
        #     try:
        #         return MapperRegistry.mappers_relation[name](connection, *obj)
        #     except Exception:
        #         MapperRegistry.mappers_relation[name] = MapperRelation
        #         return MapperRegistry.mappers_relation[name](connection, *obj)
        # else:
        #     raise Exception("Неверное количество аргументов")
