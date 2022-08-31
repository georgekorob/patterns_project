from patterns.mappers import MapperRegistry
from patterns.creational_patterns import Engine, Logger, Student, Course, Category, CategoryCategory, CourseCategory, \
    UserFactory
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


@route('/category-list/')
class CategoryList(ListView):
    """Список категорий"""
    template_name = 'category_list.html'
    # queryset = site.get_categories()

    def get_queryset(self):
        return site.get_header_category()


@route('/courses-list/')
class CoursesList(TemplateView):
    """Список курсов"""
    template_name = 'course_list.html'

    def get_context_data(self):
        try:
            category_id = int(self.request['request_params']['id'])
            category = site.find_category_by_id(category_id)
            return {'category': category}
        except KeyError:
            return '200 OK', 'No courses have been added yet'


@route('/student-list/')
class StudentList(ListView):
    template_name = 'student_list.html'
    # queryset = site.students

    def get_queryset(self):
        return site.get_students()


@route('/create-category/')
class CreateCategory(CreateView):
    """Создать категорию"""
    category_id = -1
    category = None

    def get_context_data(self):
        if self.request['method'] == 'POST':
            if self.category_id == -1:
                self.template_name = 'category_list.html'
                return {'objects_list': site.get_header_category()}
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
        site.create_object(Category, name)
        UnitOfWork.get_current().commit()
        new_category = site.get_last(Category)
        self.category_id = int(data.get('id'))
        if self.category_id != -1:
            site.create_relation(CategoryCategory, new_category.id, self.category_id)
            UnitOfWork.get_current().commit()
            self.category = site.find_category_by_id(self.category_id)


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
                self.category = site.find_category_by_id(self.category_id)
                return {'category': self.category}
            except KeyError:
                return '200 OK', 'No categories have been added yet'

    def create_obj(self, data):
        name = site.decode_value(data['name'])
        self.category = None
        if self.category_id != -1:
            site.create_object(Course, name, 'record', '/site-link/')
            UnitOfWork.get_current().commit()
            course = site.get_last(Course)
            site.create_relation(CourseCategory, course.id, self.category_id)
            UnitOfWork.get_current().commit()
            self.category = site.find_category_by_id(self.category_id)
            # Добавляем наблюдателей на курс
            course.observers.append(email_notifier)
            # course.observers.append(sms_notifier)


@route('/create-student/')
class CreateStudent(CreateView):
    template_name = 'create_student.html'

    def create_obj(self, data: dict):
        first_name = site.decode_value(data['first_name'])
        last_name = site.decode_value(data['last_name'])
        site.create_object(UserFactory, 'student', first_name, last_name)
        UnitOfWork.get_current().commit()


@route('/copy-course/')
class CopyCourse:
    """Копировать курс"""
    @Debug(name='CopyCourse')
    def __call__(self, request):
        request_params = request['request_params']
        try:
            id = int(request_params['id'])
            pid = int(request_params['cid'])
            site.copy_course(id, pid)
            category = site.find_category_by_id(pid)
            return '200 OK', render('course_list.html', category=category)
        except KeyError:
            return '200 OK', 'No courses have been added yet'


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
                course = site.find_course_by_id(course_id)
                return {'categories': site.get_categories(),
                        'course': course}
            except KeyError:
                return '200 OK', 'No categories have been added yet'

    def create_obj(self, data):
        name = site.decode_value(data['name'])
        link = data['link']
        course_id = int(data['id'])
        category_id = int(data['category'])

        site.update_course(course_id, category_id, name, link)
        self.category = site.find_category_by_id(category_id)


@route('/add-student/')
class AddStudentByCourse(CreateView):
    template_name = 'add_student.html'

    def get_context_data(self):
        context = super().get_context_data()
        context['courses'] = site.get_courses()
        context['students'] = site.get_students()
        return context

    def create_obj(self, data: dict):
        site.add_student_course(int(data['student_id']), int(data['course_id']))


@route('/api/')
class CourseApi:
    @Debug(name='CourseApi')
    def __call__(self, request):
        return '200 OK', BaseSerializer(site.get_courses()).save()
