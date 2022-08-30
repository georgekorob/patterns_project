from patterns.mappers import MapperRegistry
from patterns.creational_patterns import Engine, Logger, Student, Course, Category
from patterns.structural_patterns import route, Debug
from pumba_framework.templator import render
from patterns.behavioral_patterns import EmailNotifier, SmsNotifier, \
    TemplateView, ListView, CreateView, BaseSerializer
from patterns.unit_of_work import UnitOfWork

logger = Logger('main')
UnitOfWork.new_current()
UnitOfWork.get_current().set_mapper_registry(MapperRegistry)
email_notifier = EmailNotifier()
# sms_notifier = SmsNotifier()
site = Engine([email_notifier])


@route('/')
class Index(TemplateView):
    """Главная страница"""
    template_name = 'index.html'


@route('/about/')
class About(TemplateView):
    """О проекте"""
    template_name = 'about.html'


@route('/study_programs/')
class StudyPrograms(TemplateView):
    """Расписания"""
    template_name = 'programs.html'


@route('/courses-list/')
class CoursesList(TemplateView):
    """Список курсов"""
    template_name = 'course_list.html'

    def get_context_data(self):
        try:
            category = MapperRegistry.get_mapper(Category).find_by_id(int(self.request['request_params']['id']))
            category.courses = MapperRegistry.get_mapper(Category).get_related(category, Course, 'child')
            category.child_categories = MapperRegistry.get_mapper(Category).get_related(category, Category, 'child')
            return {'category': category}
        except KeyError:
            return '200 OK', 'No courses have been added yet'


@route('/create-course/')
class CreateCourse(CreateView):
    """Создать курс"""
    category_id = -1
    category = None

    def get_context_data(self):
        if self.request['method'] == 'POST':
            self.template_name = 'course_list.html'
            return {'category': self.category}
        else:
            self.template_name = 'create_course.html'
            try:
                self.category_id = int(self.request['request_params']['id'])
                self.category = site.find_category_by_id(int(self.category_id))
                return {'category': self.category}
            except KeyError:
                return '200 OK', 'No categories have been added yet'

    def create_obj(self, data):
        name = site.decode_value(data['name'])
        self.category = None
        if self.category_id != -1:
            self.category = site.find_category_by_id(int(self.category_id))

            course = site.create_course('record', '/site-link/', name, self.category)
            # Добавляем наблюдателей на курс
            course.observers.append(email_notifier)
            # course.observers.append(sms_notifier)
            site.courses.append(course)


@route('/edit-course/')
class EditCourse(CreateView):
    """Редактировать курс"""
    category = None

    def get_context_data(self):
        if self.request['method'] == 'POST':
            self.template_name = 'course_list.html'
            return {'category': self.category}
        else:
            self.template_name = 'course_edit.html'
            try:
                course_id = int(self.request['request_params']['id'])
                course = MapperRegistry.get_mapper(Course).find_by_id(course_id)
                return {'categories': MapperRegistry.get_mapper(Category).all(),
                        'course': course}
            except KeyError:
                return '200 OK', 'No categories have been added yet'

    def create_obj(self, data):
        name = site.decode_value(data['name'])
        link = data['link']
        course_id = int(data['id'])
        category_id = int(data['category'])
        self.category = MapperRegistry.get_mapper(Category).find_by_id(category_id)
        course = MapperRegistry.get_mapper(Course).find_by_id(course_id)
        course.category

        old_category_id = course.category.id
        old_category = site.find_category_by_id(old_category_id)
        old_category.courses.remove(course)

        course.name = name
        course.link = link
        course.category = self.category
        self.category.courses.append(course)


@route('/create-category/')
class CreateCategory(CreateView):
    """Создать категорию"""
    category_id = -1
    category = None

    def get_context_data(self):
        if self.request['method'] == 'POST':
            if self.category_id == -1:
                self.template_name = 'category_list.html'
                return {'objects_list': site.get_categories()}
            else:
                self.template_name = 'course_list.html'
                return {'category': self.category}
        else:
            self.template_name = 'create_category.html'
            try:
                id = int(self.request['request_params']['id'])
            except Exception:
                id = -1
            return {'id': id}

    def create_obj(self, data):
        name = site.decode_value(data['name'])
        new_category = Category(name)
        new_category.mark_new()
        UnitOfWork.get_current().commit()
        new_category = MapperRegistry.get_mapper(Category).all()[-1]
        self.category_id = int(data.get('id'))
        if self.category_id != -1:
            self.category = MapperRegistry.get_mapper(Category).find_by_id(self.category_id)
            MapperRegistry.get_mapper(Category).add_parent(new_category, self.category)
            self.category.child_categories = MapperRegistry.get_mapper(Category).get_related(self.category, Category, 'child')


@route('/category-list/')
class CategoryList(ListView):
    """Список категорий"""
    template_name = 'category_list.html'
    # queryset = site.get_categories()

    def get_queryset(self):
        return [c for c in site.get_categories() if c.category is None]


@route('/copy-course/')
class CopyCourse:
    """Копировать курс"""
    @Debug(name='CopyCourse')
    def __call__(self, request):
        request_params = request['request_params']

        try:
            id = int(request_params['id'])
            cid = int(request_params['cid'])

            old_course = MapperRegistry.get_mapper(Course).find_by_id(id)
            category = MapperRegistry.get_mapper(Category).find_by_id(cid)

            if old_course:
                new_name = f'copy_{old_course.name}'
                course = old_course.clone()
                course.name = new_name
                course.mark_new()
                UnitOfWork.get_current().commit()
                course = MapperRegistry.get_mapper(Course).all()[-1]
                MapperRegistry.get_mapper(course).add_parent(course, category)

            category.courses = MapperRegistry.get_mapper(Category).get_related(category, Course, 'child')

            return '200 OK', render('course_list.html', category=category)
        except KeyError:
            return '200 OK', 'No courses have been added yet'


@route('/student-list/')
class StudentListView(ListView):
    queryset = site.students
    template_name = 'student_list.html'

    def get_queryset(self):
        students = MapperRegistry.get_mapper(Student).all()
        for student in students:
            student.courses = MapperRegistry.get_mapper(Student).get_related(student, Course, 'parent')
        return students


@route('/create-student/')
class StudentCreateView(CreateView):
    template_name = 'create_student.html'

    def create_obj(self, data: dict):
        first_name = site.decode_value(data['first_name'])
        last_name = site.decode_value(data['last_name'])
        user = site.create_user('student', first_name, last_name)
        user.mark_new()
        UnitOfWork.get_current().commit()


@route('/add-student/')
class AddStudentByCourseCreateView(CreateView):
    template_name = 'add_student.html'

    def get_context_data(self):
        context = super().get_context_data()
        context['courses'] = MapperRegistry.get_mapper(Course).all()
        context['students'] = MapperRegistry.get_mapper(Student).all()
        return context

    def create_obj(self, data: dict):
        course = MapperRegistry.get_mapper(Course).find_by_id(int(data['course_id']))
        student = MapperRegistry.get_mapper(Student).find_by_id(int(data['student_id']))
        MapperRegistry.get_mapper(student).add_parent(student, course)


@route('/api/')
class CourseApi:
    @Debug(name='CourseApi')
    def __call__(self, request):
        return '200 OK', BaseSerializer(site.courses).save()
