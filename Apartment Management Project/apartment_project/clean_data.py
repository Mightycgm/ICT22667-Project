import os
import django

# ตั้งค่า Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'apartment_project.settings')
django.setup()

from apartment.models import Tenant, Room, Contract, Invoice, MonthlyBill, Utility, Fine, Maintenance, Booking

def clean_all_data():
    print("--- เริ่มกระบวนการล้างข้อมูล ---")
    
    # ลบข้อมูลในตารางที่มีความสัมพันธ์ก่อน (Foreign Key)
    print("ลบข้อมูล Utility...")
    Utility.objects.all().delete()
    
    print("ลบข้อมูล MonthlyBill...")
    MonthlyBill.objects.all().delete()
    
    print("ลบข้อมูล Fine...")
    Fine.objects.all().delete()
    
    print("ลบข้อมูล Maintenance...")
    Maintenance.objects.all().delete()
    
    print("ลบข้อมูล Invoice...")
    Invoice.objects.all().delete()
    
    print("ลบข้อมูล Contract...")
    Contract.objects.all().delete()
    
    print("ลบข้อมูล Booking...")
    Booking.objects.all().delete()
    
    # ลบข้อมูลหลัก
    print("ลบข้อมูล Tenant...")
    Tenant.objects.all().delete()
    
    print("ลบข้อมูล Room...")
    Room.objects.all().delete()
    
    print("--- ล้างข้อมูลเสร็จสมบูรณ์! ---")

if __name__ == '__main__':
    clean_all_data()
