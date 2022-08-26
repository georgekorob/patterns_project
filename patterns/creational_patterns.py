from quopri import decodestring
from patterns.behavioral_patterns import ConsoleWriter, Subject


class User:
    """Абстрактный пользователь"""

    def __init__(self, first_name, last_name):
        self.first_name = first_name
        self.last_name = last_name
        self.birthday = None


class Teacher(User):
    """Преподаватель"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class Student(User):
    """Студент"""

    def __init__(self, *args, **kwargs):
        self.courses = []
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


class Course(Subject):
    """Курс"""
    auto_id = 0

    def __init__(self, name, category):
        self.id = Course.auto_id
        Course.auto_id += 1
        self.name = name
        self.category = category
        self.category.courses.append(self)
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
        return Course(self.name, self.category)


class InteractiveCourse(Course):
    """Интерактивный курс"""
    def __init__(self, addr, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.addr = addr


class RecordCourse(Course):
    """Курс в записи"""
    def __init__(self, link, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.link = link


class CourseFactory:
    types = {
        'interactive': InteractiveCourse,
        'record': RecordCourse
    }

    @classmethod
    def create(cls, type_, addr, name, category):
        """Фабричный метод - порождающий паттерн"""
        return cls.types[type_](addr, name, category)


class Category:
    """Категория"""
    auto_id = 0

    def __init__(self, name, category):
        self.child_categories = []
        self.id = Category.auto_id
        Category.auto_id += 1
        self.name = name
        self.category = category
        if category:
            category.child_categories.append(self)
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

    def make_data(self, notifiers):
        for t in [('John', 'Wick'), ('Peter', 'Dinklage'),
                  ('Emilia', 'Clarke')]:
            self.teachers.append(self.create_user('teacher', *t))
        for s in [('Angela', 'Moss'), ('Jill', 'Lawson'), ('Steve', 'Ray')]:
            self.students.append(self.create_user('student', *s))
        for cat, cs in [('Programmers', ['Python', 'Java']),
                        ('Sport', ['Power', 'Run', 'Tennis', 'Soccer']),
                        ('Life Ballance', ['Time']),
                        ('Spirit', ['First course', 'Second course'])]:
            cat = self.create_category(cat)
            self.categories.append(cat)
            for c in cs:
                course = self.create_course('record', '/site_link/', c, cat)
                for n in notifiers:
                    course.observers.append(n)
                self.courses.append(course)
        last_category = self.categories[-1]
        for cat, cs in [('first_sub_category', ['First course in first', 'Second course in first']),
                        ('second_sub_category', ['First course in second', 'Second course in second'])]:
            cat = self.create_category(cat, last_category)
            self.courses += [self.create_course('record',
                                                '/site_link/',
                                                c, cat) for c in cs]
        for c in self.categories[0]:
            c.add_student(self.students[0])

    @staticmethod
    def create_user(type_, *args, **kwargs):
        return UserFactory.create(type_, *args, **kwargs)

    @staticmethod
    def create_category(name, category=None):
        return Category(name, category)

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

    @staticmethod
    def create_course(type_, addr, name, category):
        return CourseFactory.create(type_, addr, name, category)

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
