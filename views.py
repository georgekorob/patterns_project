from pumba_framework.templator import render
routes = {}


def route(url):
    def decorator(cls):
        routes[url] = cls()
        return cls
    return decorator


@route('/')
class Index:
    def __call__(self, request):
        return '200 OK', render('index.html', data=request)


@route('/about/')
class About:
    def __call__(self, request):
        return '200 OK', render('about.html', data=request)


@route('/course/')
class Course:
    def __call__(self, request):
        return '200 OK', 'one course'
