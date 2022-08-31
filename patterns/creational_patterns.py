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
    tablename = 'teacher'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class Student(User):
    """Студент"""
    tablename = 'student'

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
    tablename = 'course'

    def __init__(self, name, type='record', link='/site_link/'):
        # self.id = Course.auto_id
        # Course.auto_id += 1
        self.name = name
        self.link = link
        self.type = type
        self.category = None
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
    tablename = 'category'

    def __init__(self, name, *args, **kwargs):
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


class InitRelMixin:
    def __init__(self, cid, pid):
        self.cid = cid
        self.pid = pid


class CourseCategory(InitRelMixin, DomainObject):
    fields = ('course_id', 'category_pid')
    tablename = 'course_category'


class CategoryCategory(InitRelMixin, DomainObject):
    fields = ('category_id', 'category_pid')
    tablename = 'category_category'


class StudentCourse(InitRelMixin, DomainObject):
    fields = ('student_id', 'course_pid')
    tablename = 'student_course'


class TeacherCourse(InitRelMixin, DomainObject):
    fields = ('teacher_id', 'course_pid')
    tablename = 'teacher_course'


class Engine:
    """Основной интерфейс проекта"""

    def __init__(self, notifiers=None):
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
                self.create_object(UserFactory, 'teacher', *t)
            for s in students:
                self.create_object(UserFactory, 'student', *s)
            for cat, cs in categories_and_courses:
                self.create_object(Category, cat)
                for c in cs:
                    self.create_object(Course, c)
            self.create_object(Category, 'New Life')
            self.create_object(Course, 'New Course')
            UnitOfWork.get_current().commit()
        categories = MapperRegistry.get_mapper(Category).all()
        courses = MapperRegistry.get_mapper(Course).all()
        students = MapperRegistry.get_mapper(Student).all()
        if fill:
            for cat, cs in categories_and_courses:
                for category in categories:
                    if category.name == cat:
                        for c in cs:
                            for course in courses:
                                if course.name == c:
                                    self.create_relation(CourseCategory, course.id, category.id)
                                    # MapperRegistry.get_mapper(CourseCategory).insert(course.id, category.id)
                                    break
            self.create_relation(CourseCategory, courses[-1].id, categories[-1].id)
            self.create_relation(CategoryCategory, categories[-1].id, categories[2].id)
            # MapperRegistry.get_mapper(Course, Category).insert(courses[-1].id, categories[-1].id)
            # MapperRegistry.get_mapper(Category, Category).insert(categories[-1].id, categories[2].id)
            for course in courses[:2]:
                self.create_relation(StudentCourse, students[0].id, course.id)
                # MapperRegistry.get_mapper(Student, Course).insert(students[0].id, course.id)
            UnitOfWork.get_current().commit()
        self.fill_categories(categories, courses)
        self.fill_courses(courses, students)
        for course in courses:
            for n in notifiers:
                course.observers.append(n)

    @staticmethod
    def decode_value(val):
        val_b = bytes(val.replace('%', '=').replace("+", " "), 'UTF-8')
        val_decode_str = decodestring(val_b)
        return val_decode_str.decode('UTF-8')

    @staticmethod
    def create_object(obj_class, *args, **kwargs):
        if 'create' in obj_class.__dict__:
            obj = obj_class.create(*args, **kwargs)
        else:
            obj = obj_class(*args, **kwargs)
        obj.mark_new()
        return obj

    @staticmethod
    def create_relation(rel_class, id, pid):
        rel_obj = rel_class(id, pid)
        rel_obj.mark_new()
        return rel_obj

    @staticmethod
    def fill_categories(categories, courses):
        courses_in_categoties = MapperRegistry.get_mapper(CourseCategory).all()
        categoties_in_categoties = MapperRegistry.get_mapper(CategoryCategory).all()
        for category in categories:
            courses_ids = [q.cid for q in courses_in_categoties if q.pid == category.id]
            # courses_ids = MapperRegistry.get_mapper(Course, Category).find_by_pid(category.id)
            categories_ids = [q.cid for q in categoties_in_categoties if q.pid == category.id]
            # categories_ids = MapperRegistry.get_mapper(Category, Category).find_by_pid(category.id)
            for course_id in courses_ids:
                course = list(filter(lambda x: x.id == course_id, courses))[0]
                category.courses.append(course)
                course.category = category
            for category_id in categories_ids:
                find_category = list(filter(lambda x: x.id == category_id, categories))[0]
                category.child_categories.append(find_category)
                find_category.category = category

    @staticmethod
    def fill_courses(courses, students):
        students_in_courses = MapperRegistry.get_mapper(StudentCourse).all()
        for course in courses:
            students_ids = [q.cid for q in students_in_courses if q.pid == course.id]
            for student_id in students_ids:
                student = list(filter(lambda x: x.id == student_id, students))[0]
                course.students.append(student)
                student.courses.append(course)

    def get_categories(self):
        categories = MapperRegistry.get_mapper(Category).all()
        courses = MapperRegistry.get_mapper(Course).all()
        self.fill_categories(categories, courses)
        return categories

    def get_header_category(self):
        categories = self.get_categories()
        return [c for c in categories if c.category is None]

    def find_category_by_id(self, id):
        try:
            categories = self.get_categories()
            for category in categories:
                if category.id == id:
                    return category
            raise Exception(f'Нет категории с id = {id}')
        except:
            raise Exception(f'Нет категории с id = {id}')

    def get_courses(self):
        categories = MapperRegistry.get_mapper(Category).all()
        courses = MapperRegistry.get_mapper(Course).all()
        self.fill_categories(categories, courses)
        return courses

    def find_course_by_id(self, id):
        try:
            courses = self.get_courses()
            for course in courses:
                if course.id == id:
                    return course
            raise Exception(f'Нет курса с id = {id}')
        except:
            raise Exception(f'Нет курса с id = {id}')

    def get_students(self):
        courses = MapperRegistry.get_mapper(Course).all()
        students = MapperRegistry.get_mapper(Student).all()
        self.fill_courses(courses, students)
        return students

    def get_last(self, obj_class):
        return MapperRegistry.get_mapper(obj_class).last()

    def copy_course(self, id, pid):
        course = self.find_course_by_id(id)
        # courses_in_categoties = MapperRegistry.get_mapper(CourseCategory).all()
        # category_id = list(filter(lambda x: x.cid == id, courses_in_categoties))[0].pid
        new_name = f'copy_{course.name}'
        new_course = course.clone()
        new_course.name = new_name
        new_course.mark_new()
        UnitOfWork.get_current().commit()
        new_course = self.get_last(Course)
        CourseCategory(new_course.id, pid).mark_new()
        UnitOfWork.get_current().commit()

    def update_course(self, cid, pid, name, link):
        try:
            course = self.find_course_by_id(cid)
            course.name = name
            course.link = link
            course.mark_dirty()
            courses_in_categoties = MapperRegistry.get_mapper(CourseCategory).all()
            course_category = list(filter(lambda x: x.cid == course.id, courses_in_categoties))[0]
            course_category.pid = pid
            course_category.mark_dirty()
            UnitOfWork.get_current().commit()
        except:
            raise Exception("Не удалось заменить категорию")

    def add_student_course(self, sid, cid):
        StudentCourse(sid, cid).mark_new()
        UnitOfWork.get_current().commit()


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
