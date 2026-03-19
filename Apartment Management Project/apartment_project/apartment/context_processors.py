from .middleware import get_user_role

def user_role(request):
    # ส่ง role เข้าทุก template อัตโนมัติ
    return {
        'user_role': get_user_role(request.user)
    }