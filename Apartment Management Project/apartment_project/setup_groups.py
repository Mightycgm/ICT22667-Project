import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'apartment_project.settings')
django.setup()

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from apartment.models import Room, Tenant, Contract, Invoice, Maintenance, Booking

# ลบ group เดิมถ้ามี แล้วสร้างใหม่
Group.objects.all().delete()

# --- ADMIN: ทุกอย่าง (จัดการผ่าน Django Admin) ---
admin_group, _ = Group.objects.get_or_create(name='ADMIN')

# --- MANAGER: ดู/แก้ไขได้ทุกอย่าง ยกเว้น User ---
manager_group, _ = Group.objects.get_or_create(name='MANAGER')
manager_perms = Permission.objects.filter(
    content_type__app_label='apartment'
)
manager_group.permissions.set(manager_perms)

# --- STAFF: เฉพาะงานประจำวัน ---
staff_group, _ = Group.objects.get_or_create(name='STAFF')
staff_models   = [Room, Tenant, Maintenance, Booking]
staff_perms    = []
for model in staff_models:
    ct = ContentType.objects.get_for_model(model)
    # view + add เท่านั้น ไม่มี delete
    perms = Permission.objects.filter(content_type=ct, codename__in=[
        f'view_{model.__name__.lower()}',
        f'add_{model.__name__.lower()}',
        f'change_{model.__name__.lower()}',
    ])
    staff_perms.extend(perms)
staff_group.permissions.set(staff_perms)

# --- READONLY: ดูได้อย่างเดียว ---
readonly_group, _ = Group.objects.get_or_create(name='READONLY')
readonly_perms = Permission.objects.filter(
    content_type__app_label='apartment',
    codename__startswith='view_'
)
readonly_group.permissions.set(readonly_perms)

print("สร้าง Groups เรียบร้อย:")
for g in Group.objects.all():
    print(f"  {g.name}: {g.permissions.count()} permissions")

meter_group, _ = Group.objects.get_or_create(name='METER')
# กรอกมิเตอร์ได้อย่างเดียว ไม่เห็นข้อมูลอื่น
meter_perms = Permission.objects.filter(
    content_type__app_label='apartment',
    codename__in=['view_room', 'view_utility', 'add_utility', 'change_utility']
)
meter_group.permissions.set(meter_perms)