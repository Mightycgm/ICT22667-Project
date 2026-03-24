from django.shortcuts import redirect
from django.urls import reverse


def get_user_role(user):
    if not user.is_authenticated:
        return None
    if user.is_superuser:
        return 'ADMIN'
    groups = user.groups.values_list('name', flat=True)
    for role in ['ADMIN', 'MANAGER', 'METER']:
        if role in groups:
            return role
    return 'MANAGER'  # default ถ้าไม่มี group