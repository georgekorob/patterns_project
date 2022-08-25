from datetime import date


# front controller
def secret_front(request):
    request['date'] = date.today()


def user_front(request):
    request['user'] = 'noname'


def other_front(request):
    request['key'] = 'key'


# что-то вроде middleware в django
fronts = [secret_front, user_front, other_front]

