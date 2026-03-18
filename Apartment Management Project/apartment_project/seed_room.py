import os
import django
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'apartment_project.settings')
django.setup()

from apartment.models import Fine, Utility, MonthlyBill, Maintenance, Invoice, Contract, Tenant, Room
import datetime

print("กำลังลบข้อมูลเดิมทั้งหมด...")
Fine.objects.all().delete()
Utility.objects.all().delete()
MonthlyBill.objects.all().delete()
Maintenance.objects.all().delete()
Invoice.objects.all().delete()
Contract.objects.all().delete()
Tenant.objects.all().delete()
Room.objects.all().delete()
print("  ลบข้อมูลเดิมเรียบร้อย")

print("\nเริ่มสร้างห้องใหม่...")

# --- กำหนดสัดส่วนการสุ่ม ---
# (status_หลัก, status_flag, น้ำหนัก)
ROOM_PROFILES = [
    ('ว่าง',      'ปกติ',           25),   # ว่างธรรมดา
    ('ว่าง',      'รอทำความสะอาด',   8),   # ว่าง + รอทำความสะอาด
    ('ว่าง',      'จอง',             5),   # จองแล้ว
    ('มีผู้เช่า', 'ปกติ',           35),   # มีผู้เช่าปกติ
    ('มีผู้เช่า', 'แจ้งย้ายออก',    10),   # แจ้งย้ายออก
    ('ซ่อมบำรุง', 'ปกติ',           10),   # ซ่อมบำรุง
    ('ว่าง',      'ปกติ',            7),   # เผื่อกระจาย
]

weights  = [p[2] for p in ROOM_PROFILES]
profiles = [(p[0], p[1]) for p in ROOM_PROFILES]

rooms_to_create = []

for building in range(1, 5):
    for floor in range(1, 8):
        if floor == 1:
            continue
        for room_num in range(1, 16):
            room_number        = f"{building}{floor}{room_num:02d}"
            status, status_flag = random.choices(profiles, weights=weights, k=1)[0]
            rooms_to_create.append(Room(
                Room_Number = room_number,
                Building_No = str(building),
                Floor       = str(floor),
                Status      = status,
                Status_Flag = status_flag,
            ))

Room.objects.bulk_create(rooms_to_create)
print(f"  สร้างห้องทั้งหมด {len(rooms_to_create)} ห้องเรียบร้อย")

# --- สร้าง Tenant + Contract ปลอมสำหรับห้อง "มีผู้เช่า" ---
# เพื่อให้มีข้อมูล invoice เกินกำหนด ($) และ invoice รอชำระ
print("\nสร้างข้อมูลผู้เช่าตัวอย่าง...")

occupied_rooms = list(Room.objects.filter(Status='มีผู้เช่า'))
sample_rooms   = random.sample(occupied_rooms, min(30, len(occupied_rooms)))

first_names = ['สมชาย','สมหญิง','วิชัย','นภา','ประเสริฐ','มาลี','สุรชัย','นงลักษณ์','อนุชา','พิมพ์ใจ',
               'ธนกร','ชลิตา','วรวิทย์','สุภาพร','ณัฐพล','กนกวรรณ','ภานุวัฒน์','ศิริพร','จักรพงษ์','ลลิตา']
last_names  = ['ใจดี','รักไทย','สุขสม','มีทรัพย์','ทองคำ','ศรีสุข','บุญมาก','พันธุ์ดี','วงศ์งาม','ชัยมงคล']

today = datetime.date.today()

tenants_created  = 0
contracts_created = 0
overdue_created  = 0
repair_created   = 0

for i, room in enumerate(sample_rooms):
    fn = random.choice(first_names)
    ln = random.choice(last_names)

    # สร้าง Tenant
    tenant = Tenant.objects.create(
        First_Name = fn,
        Last_Name  = ln,
        ID_Card    = f"{random.randint(1000000000000, 9999999999999)}",
        Phone      = f"08{random.randint(10000000, 99999999)}",
        Email      = f"{fn.lower()}{i}@example.com",
    )
    tenants_created += 1

    # วันเริ่มสัญญา 6-18 เดือนที่แล้ว
    months_ago  = random.randint(6, 18)
    start_date  = today.replace(day=1) - datetime.timedelta(days=months_ago * 30)
    end_date    = start_date + datetime.timedelta(days=365)

    contract = Contract.objects.create(
        Tenant_ID        = tenant,
        Room_ID          = room,
        Start_Date       = start_date,
        End_Date         = end_date,
        Deposit          = 3000,
        Deposit_Advance  = 1000,
        Rent_Price       = 3000,
        Water_Cost_Unit  = 18,
        Elec_Cost_Unit   = 8,
        Water_Meter_Start = random.randint(100, 500),
        Elec_Meter_Start  = random.randint(100, 500),
        Status           = 'ใช้งาน',
    )
    contracts_created += 1

    # 30% ของห้องมีผู้เช่า → invoice เกินกำหนด (สีแดง + $)
    if random.random() < 0.30:
        overdue_date = today - datetime.timedelta(days=random.randint(5, 30))
        Invoice.objects.create(
            Contract_ID  = contract,
            Billing_Date = overdue_date - datetime.timedelta(days=30),
            Due_Date     = overdue_date,
            Grand_Total  = 3000 + random.randint(0, 500),
            Status       = 'รอชำระ',
        )
        overdue_created += 1

    # 20% ของห้องมีผู้เช่า → แจ้งซ่อมค้างอยู่ (🔧)
    if random.random() < 0.20:
        problems = ['ก๊อกน้ำรั่ว', 'แอร์ไม่เย็น', 'ไฟฟ้าขัดข้อง', 'ประตูล็อคไม่ได้', 'ท่อน้ำตัน']
        Maintenance.objects.create(
            Room_ID        = room,
            Problem_Detail = random.choice(problems),
            Report_Date    = today - datetime.timedelta(days=random.randint(1, 14)),
            Status         = random.choice(['รอดำเนินการ', 'กำลังซ่อม']),
            Repair_Cost    = 0,
        )
        repair_created += 1

print(f"  สร้าง Tenant    : {tenants_created} คน")
print(f"  สร้าง Contract  : {contracts_created} สัญญา")
print(f"  Invoice เกินกำหนด: {overdue_created} ใบ")
print(f"  แจ้งซ่อมค้าง    : {repair_created} รายการ")

# --- สรุปสุดท้าย ---
print(f"\n{'='*40}")
print(f"สรุปห้องทั้งหมด {Room.objects.count()} ห้อง")
print(f"  ขาว  (ว่าง)           : {Room.objects.filter(Status='ว่าง', Status_Flag='ปกติ').count()}")
print(f"  ขาว🧹 (รอทำความสะอาด) : {Room.objects.filter(Status='ว่าง', Status_Flag='รอทำความสะอาด').count()}")
print(f"  ขาว📌 (จอง)            : {Room.objects.filter(Status='ว่าง', Status_Flag='จอง').count()}")
print(f"  น้ำเงิน (มีผู้เช่า)   : {Room.objects.filter(Status='มีผู้เช่า', Status_Flag='ปกติ').count()}")
print(f"  เหลือง (แจ้งย้ายออก)  : {Room.objects.filter(Status='มีผู้เช่า', Status_Flag='แจ้งย้ายออก').count()}")
print(f"  ดำ  (ซ่อมบำรุง)       : {Room.objects.filter(Status='ซ่อมบำรุง').count()}")
print(f"{'='*40}")