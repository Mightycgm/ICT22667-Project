from django.shortcuts import redirect
from django.urls import reverse

# URL ที่แต่ละ role ห้ามเข้า
STAFF_BLOCKED = [
    'contract_create', 'contract_edit', 'contract_delete',
    'invoice_create', 'invoice_pay',
    'tenant_delete', 'room_delete',
]

READONLY_BLOCKED_METHODS = ['POST', 'PUT', 'DELETE', 'PATCH']


def get_user_role(user):
    if not user.is_authenticated:
        return None
    if user.is_superuser:
        return 'ADMIN'
    groups = user.groups.values_list('name', flat=True)
    for role in ['ADMIN', 'MANAGER', 'STAFF', 'READONLY']:
        if role in groups:
            return role
    return 'READONLY'  # default ถ้าไม่มี group