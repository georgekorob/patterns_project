from time import time

routes = {}


def route(url):
    """Декоратор - структурный паттерн"""
    def decorator(cls):
        routes[url] = cls()
        return cls
    return decorator


class Debug:
    """Декоратор - структурный паттерн"""
    def __init__(self, name):
        self.name = name

    def __call__(self, cls):
        """Декоратор"""
        def timeit(method):
            """Декоратор класса обернул в timeit каждый метод декорируемого класса"""
            def timed(*args, **kw):
                ts = time()
                result = method(*args, **kw)
                print(f'debug --> {self.name} выполнялся {time() - ts:2.2f} ms')
                return result
            return timed
        return timeit(cls)
