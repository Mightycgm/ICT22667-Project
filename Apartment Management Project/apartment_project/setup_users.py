import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "apartment_project.settings")
django.setup()

from django.contrib.auth.models import User, Group
from apartment.models import UserProfile

manager_group, _ = Group.objects.get_or_create(name='MANAGER')
meter_group, _ = Group.objects.get_or_create(name='METER')

print("Creating 4 managers and 4 meters...")

for i in range(1, 5):
    # Manager
    m_username = f"manager{i}"
    m_user, created = User.objects.get_or_create(username=m_username)
    if created:
        m_user.set_password('pass1234')
        m_user.save()
    m_user.groups.add(manager_group)
    
    m_profile, _ = UserProfile.objects.get_or_create(user=m_user)
    m_profile.Building_No = str(i)
    m_profile.save()
    print(f"User {m_username} assigned building {i}")

    # Meter
    met_username = f"meter{i}"
    met_user, created = User.objects.get_or_create(username=met_username)
    if created:
        met_user.set_password('pass1234')
        met_user.save()
    met_user.groups.add(meter_group)
    
    met_profile, _ = UserProfile.objects.get_or_create(user=met_user)
    met_profile.Building_No = str(i)
    met_profile.save()
    print(f"User {met_username} assigned building {i}")

print("Done creating users!")
