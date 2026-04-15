from django.shortcuts import redirect
from django.contrib import messages

def admin_required(view_func):
    """Декоратор: доступ только для роли 'admin'"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != 'admin':
            messages.error(request, 'Доступ запрещен. Требуется роль Администратор.')
            return redirect('catalog')
        return view_func(request, *args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return wrapper