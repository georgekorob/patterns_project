from quopri import decodestring


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


class Course:
    """Курс"""
    auto_id = 0

    def __init__(self, name, category):
        self.id = Course.auto_id
        Course.auto_id += 1
        self.name = name
        self.category = category
        self.category.courses.append(self)

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
        self.id = Category.auto_id
        Category.auto_id += 1
        self.name = name
        self.category = category
        self.courses = []

    def course_count(self):
        result = len(self.courses)
        if self.category:
            result += self.category.course_count()
        return result


class Engine:
    """Основной интерфейс проекта"""

    def __init__(self):
        self.teachers = []
        self.students = []
        self.categories = []
        self.courses = []
        self.make_data()

    def make_data(self):
        for t in [('John', 'Wick'), ('Peter', 'Dinklage'),
                  ('Emilia', 'Clarke')]:
            self.teachers.append(self.create_user('teacher', *t))
        for s in [('Angela', 'Moss'), ('Jill', 'Lawson'), ('Steve', 'Ray')]:
            self.students.append(self.create_user('student', *s))
        for cat, cs in [('Programmers', ['Python', 'Java']),
                        ('Sport', ['Power', 'Run', 'Tennis', 'Soccer']),
                        ('Life Ballance', ['Time']),
                        ('Spirit', [])]:
            cat = self.create_category(cat)
            self.categories.append(cat)
            self.courses += [self.create_course('record',
                                                '/site_link/',
                                                c, cat) for c in cs]

    @staticmethod
    def create_user(type_, *args, **kwargs):
        return UserFactory.create(type_, *args, **kwargs)

    @staticmethod
    def create_category(name, category=None):
        return Category(name, category)

    def find_category_by_id(self, id):
        for item in self.categories:
            print('item', item.id)
            if item.id == id:
                return item
        raise Exception(f'Нет категории с id = {id}')

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

    def __init__(self, name):
        self.name = name

    @staticmethod
    def log(text):
        print('log--->', text)
