from datetime import date
from pumba_framework.templator import render
from patterns.creational_patterns import Engine, Logger

site = Engine()
logger = Logger('main')
routes = {}


def route(url):
    def decorator(cls):
        routes[url] = cls()
        return cls
    return decorator


@route('/')
class Index:
    """Главная страница"""
    def __call__(self, request):
        return '200 OK', render('index.html', data=request)


@route('/about/')
class About:
    """О проекте"""
    def __call__(self, request):
        return '200 OK', render('about.html', data=request)


@route('/study_programs/')
class StudyPrograms:
    """Расписания"""
    def __call__(self, request):
        return '200 OK', render('study-programs.html', data=request)


@route('/courses-list/')
class CoursesList:
    """Список курсов"""
    def __call__(self, request):
        logger.log('Список курсов')
        try:
            category = site.find_category_by_id(
                int(request['request_params']['id']))
            return '200 OK', render('course_list.html',
                                    objects_list=category.courses,
                                    name=category.name, id=category.id)
        except KeyError:
            return '200 OK', 'No courses have been added yet'


@route('/create-course/')
class CreateCourse:
    """Создать курс"""
    category_id = -1

    def __call__(self, request):
        if request['method'] == 'POST':
            # метод пост
            data = request['data']

            name = data['name']
            name = site.decode_value(name)

            category = None
            if self.category_id != -1:
                category = site.find_category_by_id(int(self.category_id))

                course = site.create_course('record', '/site-link/', name, category)
                site.courses.append(course)

            return '200 OK', render('course_list.html',
                                    objects_list=category.courses,
                                    name=category.name,
                                    id=category.id)

        else:
            try:
                self.category_id = int(request['request_params']['id'])
                category = site.find_category_by_id(int(self.category_id))

                return '200 OK', render('create_course.html',
                                        name=category.name,
                                        id=category.id)
            except KeyError:
                return '200 OK', 'No categories have been added yet'


@route('/edit-course/')
class EditCourse:
    """Редактировать курс"""
    def __call__(self, request):
        if request['method'] == 'POST':
            data = request['data']

            name = data['name']
            name = site.decode_value(name)
            link = data['link']
            course_id = int(data['id'])
            category_id = int(data['category'])
            category = site.find_category_by_id(category_id)
            course = site.find_course_by_id(course_id)

            old_category_id = course.category.id
            old_category = site.find_category_by_id(old_category_id)
            old_category.courses.remove(course)

            course.name = name
            course.link = link
            course.category = category
            category.courses.append(course)

            return '200 OK', render('course_list.html',
                                    objects_list=category.courses,
                                    name=category.name,
                                    id=category.id)
        else:
            try:
                course_id = int(request['request_params']['id'])
                course = site.find_course_by_id(course_id)
                return '200 OK', render('course_edit.html',
                                        categories=site.categories,
                                        course=course)
            except KeyError:
                return '200 OK', 'No categories have been added yet'


@route('/create-category/')
class CreateCategory:
    """Создать категорию"""
    def __call__(self, request):

        if request['method'] == 'POST':
            # метод пост

            data = request['data']

            name = data['name']
            name = site.decode_value(name)

            category_id = data.get('category_id')

            category = None
            if category_id:
                category = site.find_category_by_id(int(category_id))

            new_category = site.create_category(name, category)

            site.categories.append(new_category)

            return '200 OK', render('index.html', objects_list=site.categories)
        else:
            categories = site.categories
            return '200 OK', render('create_category.html',
                                    categories=categories)


@route('/category-list/')
class CategoryList:
    """Список категорий"""
    def __call__(self, request):
        logger.log('Список категорий')
        return '200 OK', render('category_list.html', objects_list=site.categories)


@route('/copy-course/')
class CopyCourse:
    """Копировать курс"""
    def __call__(self, request):
        request_params = request['request_params']

        try:
            id = int(request_params['id'])

            old_course = site.find_course_by_id(id)
            if old_course:
                new_name = f'copy_{old_course.name}'
                new_course = old_course.clone()
                new_course.name = new_name
                # new_course.category.courses.append(new_course)
                site.courses.append(new_course)

            return '200 OK', render('course_list.html',
                                    objects_list=new_course.category.courses,
                                    name=new_course.category.name)
        except KeyError:
            return '200 OK', 'No courses have been added yet'
