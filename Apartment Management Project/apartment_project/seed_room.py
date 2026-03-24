import os, django, random, datetime
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'apartment_project.settings')
django.setup()

from apartment.models import Fine, Utility, MonthlyBill, Maintenance, Invoice, Contract, Tenant, Room, Booking

print("ลบข้อมูลเดิม...")
Fine.objects.all().delete()
Utility.objects.all().delete()
MonthlyBill.objects.all().delete()
Maintenance.objects.all().delete()
Invoice.objects.all().delete()
Contract.objects.all().delete()
Booking.objects.all().delete()
Tenant.objects.all().delete()
Room.objects.all().delete()
print("  เรียบร้อย")

today = datetime.date.today()

# ========== สร้างห้อง ==========
print("สร้างห้อง...")
rooms_to_create = []
for building in range(1, 5):
    for floor in range(2, 8):
        for room_num in range(1, 16):
            rooms_to_create.append(Room(
                Room_Number = f"{building}{floor}{room_num:02d}",
                Building_No = str(building),
                Floor       = str(floor),
                Status      = 'มีผู้เช่า',
                Status_Flag = 'ปกติ',
            ))
Room.objects.bulk_create(rooms_to_create)
all_rooms = list(Room.objects.all().order_by('Building_No', 'Floor', 'Room_Number'))
print(f"  สร้างห้อง {len(all_rooms)} ห้อง")

# ========== กำหนดสถานะห้อง ==========
print("กำหนดสถานะห้อง...")
vacant_rooms      = []
repair_rooms      = []
notify_out_rooms  = []
clean_rooms       = []
maintenance_rooms = []

for building in range(1, 5):
    b_rooms = [r for r in all_rooms if r.Building_No == str(building)]

    chosen = random.sample(b_rooms, 5)
    for r in chosen:
        r.Status = 'ว่าง'
        r.Status_Flag = 'ปกติ'
        vacant_rooms.append(r)
    b_rooms = [r for r in b_rooms if r not in chosen]

    chosen = random.sample(b_rooms, 3)
    for r in chosen:
        r.Status = 'ซ่อมบำรุง'
        r.Status_Flag = 'ปกติ'
        repair_rooms.append(r)
    b_rooms = [r for r in b_rooms if r not in chosen]

    chosen = random.sample(b_rooms, random.randint(2, 3))
    for r in chosen:
        r.Status_Flag = 'แจ้งย้ายออก'
        notify_out_rooms.append(r)
    b_rooms = [r for r in b_rooms if r not in chosen]

    chosen = random.sample(b_rooms, random.randint(2, 3))
    for r in chosen:
        r.Status_Flag = 'รอทำความสะอาด'
        clean_rooms.append(r)
    b_rooms = [r for r in b_rooms if r not in chosen]

    chosen = random.sample(b_rooms, 5)
    maintenance_rooms.extend(chosen)

for r in all_rooms:
    r.save()
print(f"  ว่าง:{len(vacant_rooms)} ซ่อมบำรุง:{len(repair_rooms)} แจ้งย้ายออก:{len(notify_out_rooms)}")

# ========== สร้าง Tenant + Contract ==========
print("สร้างผู้เช่าและสัญญา...")
first_names = ['สมชาย','สมหญิง','วิชัย','นภา','ประเสริฐ','มาลี','สุรชัย','นงลักษณ์',
               'อนุชา','พิมพ์ใจ','ธนกร','ชลิตา','วรวิทย์','สุภาพร','ณัฐพล',
               'กนกวรรณ','ภานุวัฒน์','ศิริพร','จักรพงษ์','ลลิตา']
last_names  = ['ใจดี','รักไทย','สุขสม','มีทรัพย์','ทองคำ','ศรีสุข','บุญมาก',
               'พันธุ์ดี','วงศ์งาม','ชัยมงคล','ทองอินคำ','บุญช่วย']

occupied_rooms = [r for r in all_rooms if r.Status == 'มีผู้เช่า']
contract_map   = {}

for i, room in enumerate(occupied_rooms):
    tenant = Tenant.objects.create(
        First_Name = random.choice(first_names),
        Last_Name  = random.choice(last_names),
        ID_Card    = f"{random.randint(1000000000000, 9999999999999)}",
        Phone      = f"08{random.randint(10000000, 99999999)}",
        Email      = f"tenant{i}@example.com",
        Line_ID    = f"line_{i}",
    )
    duration    = random.choices([12, 6, 3], weights=[75, 15, 10])[0]
    months_ago  = random.randint(1, 10)
    start_date  = (today.replace(day=1) - datetime.timedelta(days=months_ago * 30)).replace(day=1)
    end_date    = (start_date + datetime.timedelta(days=duration * 30)).replace(day=1)

    contract = Contract.objects.create(
        Tenant_ID         = tenant,
        Room_ID           = room,
        Start_Date        = start_date,
        End_Date          = end_date,
        Deposit           = Decimal('4000'),
        Deposit_Advance   = Decimal('2000'),
        Rent_Price        = Decimal('4000'),
        Water_Cost_Unit   = 18,
        Elec_Cost_Unit    = 8,
        Water_Meter_Start = Decimal(str(random.randint(100, 500))),
        Elec_Meter_Start  = Decimal(str(random.randint(100, 500))),
        Status            = 'ใช้งาน',
    )
    contract_map[room.Room_ID] = contract

print(f"  สร้าง {len(occupied_rooms)} สัญญา")

# ========== สร้าง Invoice ตั้งแต่ มิถุนายน 2567 – มีนาคม 2569 ==========
# กำหนดช่วงที่ต้องการ: มิ.ย. 2024 → มี.ค. 2026
print("สร้าง invoice และมิเตอร์ (มิ.ย. 2024 – มี.ค. 2026)...")

# รายชื่อเดือนที่จะสร้าง (bill_date = วันที่ 25 ของแต่ละเดือน)
bill_months = []
current = datetime.date(2024, 6, 1)
end     = datetime.date(2026, 3, 1)
while current <= end:
    bill_months.append(current)
    # ไปเดือนถัดไป
    if current.month == 12:
        current = datetime.date(current.year + 1, 1, 1)
    else:
        current = datetime.date(current.year, current.month + 1, 1)

# เดือนปัจจุบัน (วันที่ 1)
this_month = today.replace(day=1)

# เตรียม running meter ต่อห้อง
water_running = {r.Room_ID: float(contract_map[r.Room_ID].Water_Meter_Start)
                 for r in occupied_rooms}
elec_running  = {r.Room_ID: float(contract_map[r.Room_ID].Elec_Meter_Start)
                 for r in occupied_rooms}

# เดือนที่เกินกำหนด (10% จากเดือนล่าสุดที่ผ่านมาแล้ว)
overdue_room_ids = set(random.sample(
    [r.Room_ID for r in occupied_rooms],
    max(1, int(len(occupied_rooms) * 0.10))
))

for bill_month_start in bill_months:
    bill_date = bill_month_start.replace(day=25)
    next_m    = (bill_date + datetime.timedelta(days=10)).replace(day=1)
    base_due  = next_m.replace(day=5)

    # เดือนในอนาคต → ข้าม (ยังไม่ถึงวันออกบิล)
    if bill_date > today:
        break

    # เดือนนี้ (วันปัจจุบัน < 25) → ยังไม่ถึงรอบออกบิล → ข้าม
    if bill_month_start == this_month and today.day < 25:
        break

    is_last_closed_month = (bill_month_start == this_month and today.day >= 25)
    is_prev_month        = (
        bill_month_start.year == (this_month - datetime.timedelta(days=1)).replace(day=1).year and
        bill_month_start.month == (this_month - datetime.timedelta(days=1)).replace(day=1).month
    )

    for room in occupied_rooms:
        contract = contract_map[room.Room_ID]

        water_before = water_running[room.Room_ID]
        elec_before  = elec_running[room.Room_ID]
        water_after  = water_before + random.randint(8, 25)
        elec_after   = elec_before  + random.randint(50, 200)
        water_used   = water_after  - water_before
        elec_used    = elec_after   - elec_before
        water_total  = Decimal(str(water_used)) * Decimal(str(contract.Water_Cost_Unit))
        elec_total   = Decimal(str(elec_used))  * Decimal(str(contract.Elec_Cost_Unit))
        grand_total  = contract.Rent_Price + water_total + elec_total

        water_running[room.Room_ID] = water_after
        elec_running[room.Room_ID]  = elec_after

        # กำหนดสถานะ
        if is_last_closed_month:
            # เดือนปัจจุบัน (วันนี้ >= 25) → รอชำระ
            status    = 'รอชำระ'
            paid_date = None
            due_date  = base_due
        elif is_prev_month:
            # เดือนก่อนหน้า → 10% เกินกำหนด, ที่เหลือชำระแล้ว
            if room.Room_ID in overdue_room_ids:
                days_past = random.randint(10, 20)
                due_date  = base_due - datetime.timedelta(days=days_past)
                status    = 'รอชำระ'   # จะถูก update เป็นเกินกำหนดทีหลัง
                paid_date = None
            else:
                due_date  = base_due
                status    = 'ชำระแล้ว'
                paid_date = bill_date + datetime.timedelta(days=random.randint(1, 9))
        else:
            # เดือนย้อนหลัง → ชำระแล้วทั้งหมด
            due_date  = base_due
            status    = 'ชำระแล้ว'
            paid_date = bill_date + datetime.timedelta(days=random.randint(1, 9))

        invoice = Invoice.objects.create(
            Contract_ID  = contract,
            Billing_Date = bill_date,
            Due_Date     = due_date,
            Grand_Total  = grand_total,
            Status       = status,
            Paid_Date    = paid_date if status == 'ชำระแล้ว' else None,
        )
        bill_month = bill_month_start
        MonthlyBill.objects.create(
            Invoice_ID = invoice,
            Bill_Month = bill_month,
            Amount     = contract.Rent_Price,
        )
        Utility.objects.create(
            Invoice_ID        = invoice,
            Room_ID           = room,
            Bill_Month        = bill_month,
            Water_Unit_Before = Decimal(str(water_before)),
            Water_Unit_After  = Decimal(str(water_after)),
            Water_Unit_Used   = Decimal(str(water_used)),
            Elec_Unit_Used    = Decimal(str(elec_used)),
            Water_Cost_Unit   = contract.Water_Cost_Unit,
            Elec_Cost_Unit    = contract.Elec_Cost_Unit,
            Water_Total       = water_total,
            Elec_Total        = elec_total,
        )

print(f"  สร้าง {Invoice.objects.count()} invoices")

# อัปเดต invoice ที่เลย due_date → เกินกำหนด
updated = Invoice.objects.filter(
    Status='รอชำระ', Due_Date__lt=today
).update(Status='เกินกำหนด')
print(f"  อัปเดต {updated} invoices เป็น เกินกำหนด")

# ========== สร้างประวัติย้ายออก + ผู้เช่าใหม่ ==========
# เลือกห้องที่มีผู้เช่าแบบสุ่ม 8 ห้อง → จำลองว่ามีผู้เช่าเก่าย้ายออก + คนใหม่เข้าแทน
print("สร้างประวัติย้ายออก + ผู้เช่าใหม่...")

MOVEOUT_ROOMS = 8
moveout_candidates = random.sample(occupied_rooms, MOVEOUT_ROOMS)

moveout_water = {}
moveout_elec  = {}

for room in moveout_candidates:
    # ---- ผู้เช่าเก่า (ย้ายออก ธ.ค. 2024) ----
    old_tenant = Tenant.objects.create(
        First_Name = random.choice(first_names),
        Last_Name  = random.choice(last_names),
        ID_Card    = f"{random.randint(1000000000000, 9999999999999)}",
        Phone      = f"08{random.randint(10000000, 99999999)}",
        Email      = f"old_tenant_{room.Room_ID}@example.com",
        Line_ID    = f"old_{room.Room_ID}",
    )
    old_water_start = Decimal(str(random.randint(100, 300)))
    old_elec_start  = Decimal(str(random.randint(100, 300)))
    old_contract = Contract.objects.create(
        Tenant_ID         = old_tenant,
        Room_ID           = room,
        Start_Date        = datetime.date(2024, 6, 1),
        End_Date          = datetime.date(2024, 12, 31),
        Deposit           = Decimal('4000'),
        Deposit_Advance   = Decimal('2000'),
        Rent_Price        = Decimal('4000'),
        Water_Cost_Unit   = 18,
        Elec_Cost_Unit    = 8,
        Water_Meter_Start = old_water_start,
        Elec_Meter_Start  = old_elec_start,
        Status            = 'สิ้นสุด',
    )

    # สร้าง invoice ผู้เช่าเก่า มิ.ย. – ธ.ค. 2024 (7 เดือน) → ชำระแล้วทั้งหมด
    w_run = float(old_water_start)
    e_run = float(old_elec_start)
    for yr, mo in [(2024,6),(2024,7),(2024,8),(2024,9),(2024,10),(2024,11),(2024,12)]:
        bd        = datetime.date(yr, mo, 25)
        bm        = datetime.date(yr, mo, 1)
        next_m    = (bd + datetime.timedelta(days=10)).replace(day=1)
        due       = next_m.replace(day=5)
        wa        = w_run + random.randint(8, 25)
        ea        = e_run + random.randint(50, 200)
        wu        = wa - w_run;  eu = ea - e_run
        wt        = Decimal(str(wu)) * 18;  et = Decimal(str(eu)) * 8
        gt        = Decimal('4000') + wt + et
        inv = Invoice.objects.create(
            Contract_ID  = old_contract,
            Billing_Date = bd,
            Due_Date     = due,
            Grand_Total  = gt,
            Status       = 'ชำระแล้ว',
            Paid_Date    = bd + datetime.timedelta(days=random.randint(1,9)),
        )
        MonthlyBill.objects.create(Invoice_ID=inv, Bill_Month=bm, Amount=Decimal('4000'))
        Utility.objects.create(
            Invoice_ID        = inv, Room_ID=room, Bill_Month=bm,
            Water_Unit_Before = Decimal(str(w_run)), Water_Unit_After=Decimal(str(wa)),
            Water_Unit_Used   = Decimal(str(wu)),    Elec_Unit_Used  = Decimal(str(eu)),
            Water_Cost_Unit   = 18, Elec_Cost_Unit=8,
            Water_Total=wt, Elec_Total=et,
        )
        w_run = wa;  e_run = ea

    # บันทึก meter สุดท้ายของผู้เช่าเก่า → ใช้เป็นจุดเริ่มต้นของผู้เช่าใหม่
    moveout_water[room.Room_ID] = w_run
    moveout_elec[room.Room_ID]  = e_run

    # ---- ผู้เช่าใหม่ (เข้ามา ม.ค. 2025) ----
    new_tenant = Tenant.objects.create(
        First_Name = random.choice(first_names),
        Last_Name  = random.choice(last_names),
        ID_Card    = f"{random.randint(1000000000000, 9999999999999)}",
        Phone      = f"08{random.randint(10000000, 99999999)}",
        Email      = f"new_tenant_{room.Room_ID}@example.com",
        Line_ID    = f"new_{room.Room_ID}",
    )
    new_water_start = Decimal(str(round(w_run)))
    new_elec_start  = Decimal(str(round(e_run)))
    new_contract = Contract.objects.create(
        Tenant_ID         = new_tenant,
        Room_ID           = room,
        Start_Date        = datetime.date(2025, 1, 1),
        End_Date          = datetime.date(2026, 6, 30),
        Deposit           = Decimal('4000'),
        Deposit_Advance   = Decimal('2000'),
        Rent_Price        = Decimal('4000'),
        Water_Cost_Unit   = 18,
        Elec_Cost_Unit    = 8,
        Water_Meter_Start = new_water_start,
        Elec_Meter_Start  = new_elec_start,
        Status            = 'ใช้งาน',
    )

    # สร้าง invoice ผู้เช่าใหม่ ม.ค. 2025 → เดือนล่าสุด
    nw_run = float(new_water_start)
    ne_run = float(new_elec_start)
    new_bill_months = []
    nc = datetime.date(2025, 1, 1)
    ne = this_month if today.day < 25 else today.replace(day=1)
    while nc <= ne:
        new_bill_months.append(nc)
        nc = (nc.replace(day=28) + datetime.timedelta(days=4)).replace(day=1)

    for bm_s in new_bill_months:
        bd     = bm_s.replace(day=25)
        if bd > today:
            break
        bm     = bm_s
        next_m = (bd + datetime.timedelta(days=10)).replace(day=1)
        due    = next_m.replace(day=5)
        wa     = nw_run + random.randint(8, 25)
        ea     = ne_run + random.randint(50, 200)
        wu     = wa - nw_run;  eu = ea - ne_run
        wt     = Decimal(str(wu)) * 18;  et = Decimal(str(eu)) * 8
        gt     = Decimal('4000') + wt + et

        # เดือนล่าสุด → รอชำระ, เดือนก่อนหน้า → ชำระแล้ว
        if bm_s == this_month and today.day >= 25:
            st = 'รอชำระ'; pd = None; du = due
        elif bm_s == (this_month.replace(day=1) - datetime.timedelta(days=1)).replace(day=1):
            st = 'ชำระแล้ว'; pd = bd + datetime.timedelta(days=random.randint(1,9)); du = due
        else:
            st = 'ชำระแล้ว'; pd = bd + datetime.timedelta(days=random.randint(1,9)); du = due

        inv = Invoice.objects.create(
            Contract_ID  = new_contract,
            Billing_Date = bd,
            Due_Date     = du,
            Grand_Total  = gt,
            Status       = st,
            Paid_Date    = pd,
        )
        MonthlyBill.objects.create(Invoice_ID=inv, Bill_Month=bm, Amount=Decimal('4000'))
        Utility.objects.create(
            Invoice_ID        = inv, Room_ID=room, Bill_Month=bm,
            Water_Unit_Before = Decimal(str(nw_run)), Water_Unit_After=Decimal(str(wa)),
            Water_Unit_Used   = Decimal(str(wu)),     Elec_Unit_Used  = Decimal(str(eu)),
            Water_Cost_Unit   = 18, Elec_Cost_Unit=8,
            Water_Total=wt, Elec_Total=et,
        )
        nw_run = wa;  ne_run = ea

    # อัปเดต contract_map → ชี้ไปผู้เช่าใหม่
    contract_map[room.Room_ID] = new_contract

print(f"  ห้องมีประวัติย้ายออก : {MOVEOUT_ROOMS} ห้อง")
print(f"  Contract สิ้นสุด     : {Contract.objects.filter(Status='สิ้นสุด').count()} รายการ")
print(f"  Contract ใช้งาน      : {Contract.objects.filter(Status='ใช้งาน').count()} รายการ")
print(f"  Invoice ทั้งหมด (รวมประวัติ) : {Invoice.objects.count()} ฉบับ")

# ========== Booking ==========
print("สร้างการจอง...")
booking_rooms = random.sample(vacant_rooms, min(4, len(vacant_rooms)))
for room in booking_rooms:
    Booking.objects.create(
        Room_ID    = room,
        First_Name = random.choice(first_names),
        Last_Name  = random.choice(last_names),
        ID_Card    = f"{random.randint(1000000000000, 9999999999999)}",
        Phone      = f"08{random.randint(10000000, 99999999)}",
        Status     = 'รอยืนยัน',
    )
    room.Status_Flag = 'จอง'
    room.save()
print(f"  สร้าง {Booking.objects.count()} การจอง")

# ========== Maintenance ==========
print("สร้างแจ้งซ่อม...")
problems = ['ก๊อกน้ำรั่ว','แอร์ไม่เย็น','ไฟฟ้าขัดข้อง','ประตูล็อคไม่ได้',
            'ท่อน้ำตัน','หลอดไฟขาด','หน้าต่างปิดไม่สนิท','ฝักบัวชำรุด']
for room in maintenance_rooms:
    Maintenance.objects.create(
        Room_ID        = room,
        Problem_Detail = random.choice(problems),
        Report_Date    = today - datetime.timedelta(days=random.randint(1, 14)),
        Status         = random.choice(['รอดำเนินการ', 'กำลังซ่อม']),
        Repair_Cost    = 0,
    )
print(f"  สร้าง {Maintenance.objects.count()} รายการแจ้งซ่อม")

# ========== สรุป ==========
print(f"\n{'='*50}")
print(f"ห้องทั้งหมด              : {Room.objects.count()}")
print(f"ว่าง                     : {Room.objects.filter(Status='ว่าง').count()}")
print(f"มีผู้เช่า (ปกติ)         : {Room.objects.filter(Status='มีผู้เช่า', Status_Flag='ปกติ').count()}")
print(f"แจ้งย้ายออก              : {Room.objects.filter(Status_Flag='แจ้งย้ายออก').count()}")
print(f"รอทำความสะอาด            : {Room.objects.filter(Status_Flag='รอทำความสะอาด').count()}")
print(f"ซ่อมบำรุง                : {Room.objects.filter(Status='ซ่อมบำรุง').count()}")
print(f"─────────────────────────────────────────────────")
print(f"Contract ใช้งาน          : {Contract.objects.filter(Status='ใช้งาน').count()}")
print(f"Contract สิ้นสุด (ย้ายออก): {Contract.objects.filter(Status='สิ้นสุด').count()}")
print(f"─────────────────────────────────────────────────")
print(f"การจอง                   : {Booking.objects.filter(Status='รอยืนยัน').count()}")
print(f"─────────────────────────────────────────────────")
print(f"Invoice รวมทั้งหมด        : {Invoice.objects.count()}")
print(f"  ชำระแล้ว               : {Invoice.objects.filter(Status='ชำระแล้ว').count()}")
print(f"  รอชำระ                 : {Invoice.objects.filter(Status='รอชำระ').count()}")
print(f"  เกินกำหนด              : {Invoice.objects.filter(Status='เกินกำหนด').count()}")
print(f"─────────────────────────────────────────────────")
print(f"แจ้งซ่อม                 : {Maintenance.objects.count()}")
print(f"{'='*50}")