import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'apartment_project.settings')
django.setup()

from django.contrib.auth.models import User, Group

users_to_create = [
    ('admin',      'pass1234', 'ADMIN'),
    ('manager01',  'pass1234', 'MANAGER'),
    ('staff01',    'pass1234', 'STAFF'),
    ('readonly01', 'pass1234', 'READONLY'),
    ('meter01',    'pass1234', 'METER'),
]

for username, password, group_name in users_to_create:
    try:
        group = Group.objects.get(name=group_name)
    except Group.DoesNotExist:
        print(f"  ❌ ไม่พบ Group '{group_name}' กรุณารัน setup_groups.py ก่อน")
        continue

    user, created = User.objects.get_or_create(username=username)
    user.set_password(password)
    user.is_staff = True
    user.save()
    user.groups.set([group])

    status = 'สร้างใหม่' if created else 'อัปเดตแล้ว'
    print(f"  ✅ {username} ({group_name}) — {status}")

print("\nสรุป user ทั้งหมด:")
for u in User.objects.all():
    groups = list(u.groups.values_list('name', flat=True))
    role   = groups[0] if groups else 'ADMIN (superuser)'
    print(f"  {u.username} → {role}")