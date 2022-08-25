from pumba_framework.templator import render


class Index:
    def __call__(self, request):
        return '200 OK', render('index.html', data=request)


class About:
    def __call__(self, request):
        return '200 OK', render('about.html', data=request)


class Course:
    def __call__(self, request):
        return '200 OK', 'one course'


class NotFound404:
    def __call__(self, request):
        return '404 WHAT', '404 PAGE Not Found'
