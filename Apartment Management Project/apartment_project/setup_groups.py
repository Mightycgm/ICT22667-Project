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