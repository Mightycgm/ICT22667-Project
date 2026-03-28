import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'apartment_project.settings')
django.setup()

from django.contrib.auth.models import User, Group
from apartment.models import UserProfile

# Ensure groups exist
manager_group, _ = Group.objects.get_or_create(name='MANAGER')
meter_group,   _ = Group.objects.get_or_create(name='METER')

# Manager และ Meter — 4 คนต่อ role
roles = [
    ('manager', manager_group),
    ('meter',   meter_group),
]

for role, group in roles:
    for i in range(1, 5):
        username = f"{role}{i}"
        user, created = User.objects.get_or_create(username=username)
        user.set_password('pass1234')
        user.is_staff = True
        user.save()
        user.groups.set([group])

        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.Building_No = str(i)
        profile.save()

        status = 'สร้างใหม่' if created else 'อัปเดตแล้ว'
        print(f"  ✅ {username} ({group.name}) — {status}")

print("\nสรุป user ทั้งหมด:")
for u in User.objects.all():
    groups = list(u.groups.values_list('name', flat=True))
    role = groups[0] if groups else '(no group)'
    print(f"  {u.username} → {role}")
