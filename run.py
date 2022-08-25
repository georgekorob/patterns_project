from pumba_framework.main import Framework
from urls import routes, fronts
from wsgiref.simple_server import make_server

application = Framework(routes, fronts)
port = 8001
addr = ''

with make_server(addr, port, application) as httpd:
    addr = addr if addr else '127.0.0.1'
    print(f"Запуск на порту {port}...\nhttp://{addr}:{port}")
    httpd.serve_forever()
