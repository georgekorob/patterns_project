from quopri import decodestring
from framework_requests import GetRequests, PostRequests
from types_dict import CONTENT_TYPES
import static_settings as static
from os import path


class PageNotFound404:
    def __call__(self, request):
        return '404 WHAT', '404 PAGE Not Found'


class ViewGetStatic:
    def __init__(self, static_dir, file_path):
        self.static_dir = static_dir
        self.file_path = file_path

    def __call__(self, request):
        path_to_file = path.join(self.static_dir, self.file_path)
        with open(path_to_file, 'rb') as f:
            file_content = f.read()
        status_code = '200 OK'
        return status_code, file_content


class Framework:
    """Класс Framework - основа фреймворка"""

    def __init__(self, routes_obj, fronts_obj):
        self.routes_lst = routes_obj
        self.fronts_lst = fronts_obj

    def __call__(self, environ, start_response):
        # получаем адрес, по которому выполнен переход
        path = environ['PATH_INFO']
        if not path.endswith('/'):
            path = f'{path}/'

        method = environ['REQUEST_METHOD']
        request = {'method': method}
        if method == 'POST':
            data = Framework.decode_value(PostRequests().get_request_params(environ))
            request['data'] = data
            print(f'Нам пришёл post-запрос: {data}')
        if method == 'GET':
            request_params = Framework.decode_value(GetRequests().get_request_params(environ))
            request['request_params'] = request_params
            print(f'Нам пришли GET-параметры: {request_params}')

        # отработка паттерна page controller
        _static = False
        if path in self.routes_lst:
            view = self.routes_lst[path]
        elif path.startswith(static.STATIC_URL):
            path = path[len(static.STATIC_URL):len(path) - 1]
            view = ViewGetStatic(static.STATIC_FILES_DIR, path)
            _static = True
        else:
            view = PageNotFound404()

        # отработка паттерна front controller
        for front in self.fronts_lst:
            front(request)

        # запуск контроллера с передачей объекта request
        code, body = view(request)
        body = body if _static else body.encode('utf-8')
        start_response(code, [('Content-Type', self.get_content_type(path))])
        return [body]

    @staticmethod
    def get_content_type(file_path):
        file_name = path.basename(file_path).lower()  # styles.css
        extension = path.splitext(file_name)[1]  # .css
        # print(extension)
        return CONTENT_TYPES.get(extension, "text/html")

    @staticmethod
    def decode_value(data):
        new_data = {}
        for k, v in data.items():
            val = bytes(v.replace('%', '=').replace("+", " "), 'UTF-8')
            val_decode_str = decodestring(val).decode('UTF-8')
            new_data[k] = val_decode_str
        return new_data
