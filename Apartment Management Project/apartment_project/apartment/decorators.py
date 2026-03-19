from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from .middleware import get_user_role


def role_required(*allowed_roles):
    # ใช้คลุม view ที่ต้องการจำกัดสิทธิ์
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            role = get_user_role(request.user)
            if role not in allowed_roles:
                messages.error(request, f'คุณไม่มีสิทธิ์เข้าถึงส่วนนี้ (ต้องการ: {", ".join(allowed_roles)})')
                return redirect('dashboard')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def not_readonly(view_func):
    # ป้องกัน READONLY จากการแก้ไขข้อมูล
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        role = get_user_role(request.user)
        if role == 'READONLY':
            messages.error(request, 'คุณมีสิทธิ์ดูข้อมูลเท่านั้น')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper