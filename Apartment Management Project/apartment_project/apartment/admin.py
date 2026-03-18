from django.contrib import admin
from .models import Tenant, Room, Contract, Invoice, MonthlyBill, Utility, Maintenance, Fine

# ลงทะเบียนทุก model เพื่อจัดการผ่าน Django Admin
admin.site.register(Tenant)
admin.site.register(Room)
admin.site.register(Contract)
admin.site.register(Invoice)
admin.site.register(MonthlyBill)
admin.site.register(Utility)
admin.site.register(Maintenance)
admin.site.register(Fine)