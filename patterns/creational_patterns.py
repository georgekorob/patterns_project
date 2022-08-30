from quopri import decodestring
from patterns.mappers import MapperRegistry
from patterns.behavioral_patterns import ConsoleWriter, Subject
from patterns.unit_of_work import DomainObject, UnitOfWork


class User(DomainObject):
    """Абстрактный пользователь"""
    fields = 'first_name', 'last_name'

    def __init__(self, first_name, last_name):
        self.first_name = first_name
        self.last_name = last_name
        self.courses = []


class Teacher(User):
    """Преподаватель"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class Student(User):
    """Студент"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class UserFactory:
    types = {
        'student': Student,
        'teacher': Teacher
    }

    @classmethod
    def create(cls, type_, *args, **kwargs):
        """Фабричный метод - порождающий паттерн"""
        return cls.types[type_](*args, **kwargs)


# class CoursePrototype:
#     """Прототип - порождающий паттерн курсов обучения"""
# Паттерн прототип в данном случае не подходит, потому что у курса есть поле
# category, которое в свою очередь имеет список курсов, на них нужны те же
# ссылки, а не новые


class Course(Subject, DomainObject):
    """Курс"""
    # auto_id = 0

    def __init__(self, name, type='record', link='/site_link/'):
        # self.id = Course.auto_id
        # Course.auto_id += 1
        self.name = name
        self.link = link
        self.type = type
        # self.category = category
        # self.category.courses.append(self)
        self.students = []
        super().__init__()

    def __getitem__(self, item):
        """Обращение к курсу как к массиву, получение студента."""
        return self.students[item]

    def add_student(self, student: Student):
        self.students.append(student)
        student.courses.append(self)
        # Оповещение пользователей
        self.notify()

    def clone(self):
        return Course(self.name, self.type, self.link)


class Category(DomainObject):
    """Категория"""
    # auto_id = 0

    def __init__(self, name):
        self.child_categories = []
        # self.id = Category.auto_id
        # Category.auto_id += 1
        self.name = name
        self.category = None
        # if category:
        #     category.child_categories.append(self)
        self.courses = []

    def __getitem__(self, item):
        """Обращение к категории как к массиву, получение курса."""
        return self.courses[item]

    def course_count(self):
        result = len(self.courses)
        for category in self.child_categories:
            result += category.course_count()
        return result


class Engine:
    """Основной интерфейс проекта"""

    def __init__(self, notifiers=None):
        self.teachers = []
        self.students = []
        self.categories = []
        self.courses = []
        if notifiers is None:
            notifiers = []
        self.make_data(notifiers)

    def make_data(self, notifiers, fill=False):
        if fill:
            teachers = [('John', 'Wick'), ('Peter', 'Dinklage'), ('Emilia', 'Clarke')]
            students = [('Angela', 'Moss'), ('Jill', 'Lawson'), ('Steve', 'Ray')]
            categories_and_courses = [('Programmers', ['Python', 'Java']),
                                      ('Sport', ['Power', 'Run', 'Tennis', 'Soccer']),
                                      ('Life Ballance', ['Time']),
                                      ('Spirit', ['First course', 'Second course'])]
            for t in teachers:
                self.teachers.append(self.create_user('teacher', *t))
                self.teachers[-1].mark_new()
            for s in students:
                self.students.append(self.create_user('student', *s))
                self.students[-1].mark_new()
            for cat, cs in categories_and_courses:
                self.create_category(cat)
                for c in cs:
                    self.create_course(c)
            UnitOfWork.get_current().commit()
        self.students = MapperRegistry.get_mapper(Student).all()
        self.courses = MapperRegistry.get_mapper(Course).all()
        self.categories = MapperRegistry.get_mapper(Category).all()
        if fill:
            for cat, cs in categories_and_courses:
                for category in self.categories:
                    if category.name == cat:
                        for c in cs:
                            for course in self.courses:
                                if course.name == c:
                                    MapperRegistry.get_mapper(course).add_parent(course, category)
                                    break
        for category in self.categories:
            category.courses = MapperRegistry.get_mapper(Category).get_related(category, Course, 'child')
        if fill:
            for course in self.categories[0]:
                course.add_student(self.students[0])
                MapperRegistry.get_mapper(self.students[0]).add_parent(self.students[0], course)
        for course in self.courses:
            course.students = MapperRegistry.get_mapper(Course).get_related(course, Student,  'child')
        for course in self.courses:
            for n in notifiers:
                course.observers.append(n)

    def get_categories(self):
        categories = MapperRegistry.get_mapper(Category).all()
        for category in categories:
            category.courses = MapperRegistry.get_mapper(Category).get_related(category, Course, 'child')
            category.child_categories = MapperRegistry.get_mapper(Category).get_related(category, Category, 'child')
            for cat in category.child_categories:
                for c in categories:
                    if c.id == cat.id:
                        c.category = category
        return categories

    def create_user(self, type_, *args, **kwargs):
        return UserFactory.create(type_, *args, **kwargs)

    def create_category(self, name, *args, **kwargs):
        category = Category(name, *args, **kwargs)
        self.categories.append(category)
        category.mark_new()
        return category

    def create_course(self, type_, *args, **kwargs):
        course = Course(type_, *args, **kwargs)
        self.courses.append(course)
        course.mark_new()
        return course

    def find_category_by_id(self, id):
        category = self.find_in_all_category(self.categories, id)
        if category:
            return category
        raise Exception(f'Нет категории с id = {id}')

    @classmethod
    def find_in_all_category(cls, categories, id):
        for category in categories:
            print('category', category.id)
            if category.id == id:
                return category
            category = cls.find_in_all_category(category.child_categories, id)
            if category:
                return category

    def get_all_categories(self, categories):
        cats = categories.copy()
        for cat in categories:
            cats += self.get_all_categories(cat.child_categories)
        return cats

    def find_course_by_id(self, id):
        for item in self.courses:
            print('item', item.id)
            if item.id == id:
                return item
        raise Exception(f'Нет курса с id = {id}')

    def get_course(self, name):
        for item in self.courses:
            if item.name == name:
                return item
        return None

    def get_student(self, name) -> Student:
        first_name, last_name = name.split(' ')
        for item in self.students:
            if item.first_name == first_name and item.last_name == last_name:
                return item

    @staticmethod
    def decode_value(val):
        val_b = bytes(val.replace('%', '=').replace("+", " "), 'UTF-8')
        val_decode_str = decodestring(val_b)
        return val_decode_str.decode('UTF-8')


class SingletonByName(type):
    """Синглтон - порождающий паттерн"""

    def __init__(cls, name, bases, attrs, **kwargs):
        super().__init__(name, bases, attrs)
        cls.__instance = {}

    def __call__(cls, *args, **kwargs):
        if args:
            name = args[0]
        if kwargs:
            name = kwargs['name']

        if name in cls.__instance:
            return cls.__instance[name]
        else:
            cls.__instance[name] = super().__call__(*args, **kwargs)
            return cls.__instance[name]


class Logger(metaclass=SingletonByName):
    """Логгер"""

    def __init__(self, name, writer=ConsoleWriter()):
        self.name = name
        self.writer = writer

    def log(self, text):
        text = f'log---> {text}'
        self.writer.write(text)
