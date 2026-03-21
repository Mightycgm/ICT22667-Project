from .middleware import get_user_role
from django.conf import settings as django_settings

def user_role(request):
    # ส่ง role เข้าทุก template อัตโนมัติ
    return {
        'user_role': get_user_role(request.user),
        'bank_info': getattr(django_settings, 'BANK_INFO', {}),
    }