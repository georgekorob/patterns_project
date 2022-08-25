class ReqM:
    @staticmethod
    def parse_input_data(data: str):
        result = {}
        if data:
            # делим параметры через &, а словарь через =
            vals = [item.split('=')[:2] for item in data.split('&')]
            result = {v[0]: v[1] for v in vals}
        return result

    @staticmethod
    def get_request_params(environ):
        pass


# get requests
class GetRequests(ReqM):
    @staticmethod
    def get_request_params(environ):
        # получаем параметры запроса
        query_string = environ['QUERY_STRING']
        # превращаем параметры в словарь
        request_params = GetRequests.parse_input_data(query_string)
        return request_params


# post requests
class PostRequests(ReqM):
    @staticmethod
    def get_wsgi_input_data(env) -> bytes:
        # получаем длину тела
        content_length_data = env.get('CONTENT_LENGTH')
        # приводим к int
        content_length = int(content_length_data) if content_length_data else 0
        print(content_length)
        # считываем данные, если они есть
        data = env['wsgi.input'].read(content_length) if content_length > 0 else b''
        return data

    def parse_wsgi_input_data(self, data: bytes) -> dict:
        result = {}
        if data:
            data_str = data.decode(encoding='utf-8')
            print(f'Строка после декодирования - {data_str}')
            result = self.parse_input_data(data_str)
        return result

    def get_request_params(self, environ):
        # получаем данные и превращаем данные в словарь
        data = self.get_wsgi_input_data(environ)
        return self.parse_wsgi_input_data(data)
