import os, django, random, datetime, calendar
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'apartment_project.settings')
django.setup()

from apartment.models import Fine, Utility, MonthlyBill, Maintenance, Invoice, Contract, Tenant, Room, Booking

# ========== ลบข้อมูลเดิม ==========
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

today        = datetime.date.today()
PERIOD_START = datetime.date(2024, 6, 1)  # เริ่มสร้าง Invoice ตั้งแต่เดือนนี้

# ========== Helpers ==========
def next_month(d):
    if d.month == 12:
        return datetime.date(d.year + 1, 1, 1)
    return datetime.date(d.year, d.month + 1, 1)

def add_months(d, n):
    m  = d.month - 1 + n
    yr = d.year + m // 12
    mo = m % 12 + 1
    day = min(d.day, calendar.monthrange(yr, mo)[1])
    return datetime.date(yr, mo, day)

def month_range(start, end_incl):
    """List of 1st-of-month dates from start to end_incl (inclusive)."""
    result, cur = [], start.replace(day=1)
    end = end_incl.replace(day=1)
    while cur <= end:
        result.append(cur)
        cur = next_month(cur)
    return result

first_names = [
    'สมชาย','สมหญิง','วิชัย','นภา','ประเสริฐ','มาลี','สุรชัย','นงลักษณ์',
    'อนุชา','พิมพ์ใจ','ธนกร','ชลิตา','วรวิทย์','สุภาพร','ณัฐพล',
    'กนกวรรณ','ภานุวัฒน์','ศิริพร','จักรพงษ์','ลลิตา','กิตติ','วิภา',
    'ชัยวัฒน์','นิภา','สมศักดิ์','รัตนา','บุญส่ง','ศิริลักษณ์','ธีรพงษ์','วันดี',
]
last_names = [
    'ใจดี','รักไทย','สุขสม','มีทรัพย์','ทองคำ','ศรีสุข','บุญมาก',
    'พันธุ์ดี','วงศ์งาม','ชัยมงคล','ทองอินคำ','บุญช่วย','สมบูรณ์','มั่งมี',
    'ดีงาม','สุขใจ','พัฒนา','รุ่งเรือง','ทองแดง','สีดา',
]

RENT = Decimal('4000')

_tc = [0]
def make_tenant(tag='t'):
    i = _tc[0]; _tc[0] += 1
    return Tenant.objects.create(
        First_Name = random.choice(first_names),
        Last_Name  = random.choice(last_names),
        ID_Card    = f"{random.randint(1000000000000, 9999999999999)}",
        Phone      = f"08{random.randint(10000000, 99999999)}",
        Email      = f"{tag}_{i}@example.com",
        Line_ID    = f"line_{tag}_{i}",
    )

def make_contract(tenant, room, start, end, status='ใช้งาน', w_start=None, e_start=None):
    if w_start is None: w_start = Decimal(str(random.randint(100, 500)))
    if e_start is None: e_start = Decimal(str(random.randint(100, 500)))
    return Contract.objects.create(
        Tenant_ID         = tenant,
        Room_ID           = room,
        Start_Date        = start,
        End_Date          = end,
        Deposit           = RENT,
        Deposit_Advance   = RENT / 2,
        Rent_Price        = RENT,
        Water_Cost_Unit   = 18,
        Elec_Cost_Unit    = 8,
        Water_Meter_Start = w_start,
        Elec_Meter_Start  = e_start,
        Status            = status,
    )

def create_invoices(contract, months, w0, e0, overdue_ids=None):
    """
    สร้าง Invoice + MonthlyBill + Utility สำหรับ contract ในรายการ months ที่กำหนด
    คืนค่า (water_final, elec_final)
    """
    w, e = float(w0), float(e0)
    is_overdue_room = bool(overdue_ids and contract.Room_ID_id in overdue_ids)
    # overdue rooms: ยังไม่จ่าย 1–2 เดือนล่าสุด
    unpaid_from = add_months(today.replace(day=1), -random.randint(1, 2)) if is_overdue_room else None

    for bm in months:
        bill_date = datetime.date(bm.year, bm.month, 25)  # ออกบิลวันที่ 25 เสมอ
        if bill_date > today:
            break

        due_date = next_month(bm).replace(day=5)  # กำหนดชำระวันที่ 5 เดือนถัดไป

        # มิเตอร์
        wa = w + random.randint(8, 25)
        ea = e + random.randint(50, 200)
        wu = wa - w;  eu = ea - e
        wt = Decimal(str(wu)) * Decimal(str(contract.Water_Cost_Unit))
        et = Decimal(str(eu)) * Decimal(str(contract.Elec_Cost_Unit))
        gt = contract.Rent_Price + wt + et

        # สถานะ invoice
        if due_date > today:
            # ยังไม่ถึงกำหนดชำระ → รอชำระ
            status = 'รอชำระ'; paid_date = None
        elif is_overdue_room and bm >= unpaid_from:
            # เดือนที่ยังไม่จ่าย + เลย due_date แล้ว → รอชำระ (bulk update จะเปลี่ยนเป็น เกินกำหนด)
            status = 'รอชำระ'; paid_date = None
        else:
            # ชำระแล้ว (จ่ายภายในวันที่ 25–5 ของเดือนถัดไป)
            status    = 'ชำระแล้ว'
            paid_date = bill_date + datetime.timedelta(days=random.randint(1, 10))

        inv = Invoice.objects.create(
            Contract_ID  = contract,
            Billing_Date = bill_date,
            Due_Date     = due_date,
            Grand_Total  = gt,
            Status       = status,
            Paid_Date    = paid_date if status == 'ชำระแล้ว' else None,
        )
        MonthlyBill.objects.create(Invoice_ID=inv, Bill_Month=bm, Amount=contract.Rent_Price)
        Utility.objects.create(
            Invoice_ID        = inv,
            Room_ID           = contract.Room_ID,
            Bill_Month        = bm,
            Water_Unit_Before = Decimal(str(w)),
            Water_Unit_After  = Decimal(str(wa)),
            Water_Unit_Used   = Decimal(str(wu)),
            Elec_Unit_Before  = Decimal(str(e)),
            Elec_Unit_After   = Decimal(str(ea)),
            Elec_Unit_Used    = Decimal(str(eu)),
            Water_Cost_Unit   = contract.Water_Cost_Unit,
            Elec_Cost_Unit    = contract.Elec_Cost_Unit,
            Water_Total       = wt,
            Elec_Total        = et,
        )
        w = wa; e = ea

    return w, e

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
vacant_rooms = []; repair_rooms = []; notify_out_rooms = []
clean_rooms  = []; maintenance_rooms = []

for building in range(1, 5):
    b_rooms = [r for r in all_rooms if r.Building_No == str(building)]

    chosen = random.sample(b_rooms, 5)
    for r in chosen: r.Status = 'ว่าง'; r.Status_Flag = 'ปกติ'; vacant_rooms.append(r)
    b_rooms = [r for r in b_rooms if r not in chosen]

    chosen = random.sample(b_rooms, 3)
    for r in chosen: r.Status = 'ซ่อมบำรุง'; r.Status_Flag = 'ปกติ'; repair_rooms.append(r)
    b_rooms = [r for r in b_rooms if r not in chosen]

    chosen = random.sample(b_rooms, random.randint(2, 3))
    for r in chosen: r.Status_Flag = 'แจ้งย้ายออก'; notify_out_rooms.append(r)
    b_rooms = [r for r in b_rooms if r not in chosen]

    chosen = random.sample(b_rooms, random.randint(2, 3))
    for r in chosen: r.Status_Flag = 'รอทำความสะอาด'; clean_rooms.append(r)
    b_rooms = [r for r in b_rooms if r not in chosen]

    maintenance_rooms.extend(random.sample(b_rooms, 5))

for r in all_rooms:
    r.save()

occupied_rooms = [r for r in all_rooms if r.Status == 'มีผู้เช่า']
print(f"  ว่าง:{len(vacant_rooms)} ซ่อม:{len(repair_rooms)} "
      f"แจ้งย้ายออก:{len(notify_out_rooms)} รอทำความสะอาด:{len(clean_rooms)} "
      f"มีผู้เช่า:{len(occupied_rooms)}")

# ========== แบ่งห้อง: moveout vs simple ==========
# moveout_rooms → มีประวัติย้ายออก/เข้าช่วง มิ.ย. 2024–มี.ค. 2026
# simple_rooms  → ผู้เช่าต่อเนื่อง ไม่ได้ย้าย
MOVEOUT_SINGLE = 70   # ห้องที่ย้ายออก 1 รอบ
MOVEOUT_DOUBLE = 35   # ห้องที่ย้ายออก 2 รอบ (ผ่านผู้เช่า 2–3 คน)
MOVEOUT_COUNT  = MOVEOUT_SINGLE + MOVEOUT_DOUBLE

moveout_rooms_all = random.sample(occupied_rooms, MOVEOUT_COUNT)
random.shuffle(moveout_rooms_all)
double_moveout_rooms = moveout_rooms_all[:MOVEOUT_DOUBLE]
single_moveout_rooms = moveout_rooms_all[MOVEOUT_DOUBLE:]
simple_rooms = [r for r in occupied_rooms if r not in set(moveout_rooms_all)]

# กำหนด 10% ของ simple + new-tenant rooms ให้เป็น overdue
overdue_ids = set(random.sample(
    [r.Room_ID for r in simple_rooms],
    max(1, len(simple_rooms) // 10)
))

# ========== Helper: สร้างผู้เช่า 1 รายพร้อม invoice ==========
def seed_tenant(room, start_m, exit_m, w0, e0, is_current=False, overdue_ids=None):
    """
    สร้าง Tenant + Contract + Invoice สำหรับ 1 ช่วงเวลา
    start_m, exit_m = datetime.date (วันที่ 1 ของเดือน)
    คืนค่า (w_final, e_final)
    """
    start   = datetime.date(start_m.year, start_m.month, random.randint(1, 15))
    start   = max(start, datetime.date(2022, 1, 1))
    last_d  = calendar.monthrange(exit_m.year, exit_m.month)[1]
    end     = datetime.date(exit_m.year, exit_m.month, random.randint(25, last_d))
    status  = 'ใช้งาน' if is_current else 'สิ้นสุด'
    tag     = 'cur' if is_current else 'hist'

    tenant   = make_tenant(tag)
    contract = make_contract(tenant, room, start, end, status=status,
                             w_start=Decimal(str(round(w0))),
                             e_start=Decimal(str(round(e0))))

    inv_start = max(PERIOD_START, start_m)
    inv_end   = today.replace(day=1) if is_current else exit_m
    w_fin, e_fin = float(contract.Water_Meter_Start), float(contract.Elec_Meter_Start)
    if inv_start <= inv_end:
        months = month_range(inv_start, inv_end)
        oids   = overdue_ids if is_current else None
        w_fin, e_fin = create_invoices(contract, months, contract.Water_Meter_Start, contract.Elec_Meter_Start, oids)

    return w_fin, e_fin

# ========== Simple rooms: สัญญาต่อเนื่อง ==========
print(f"สร้างผู้เช่า simple {len(simple_rooms)} ห้อง...")
for room in simple_rooms:
    months_ago = random.randint(2, 30)
    s_base     = add_months(today.replace(day=1), -months_ago)
    start_date = datetime.date(s_base.year, s_base.month, random.randint(1, 15))
    start_date = max(start_date, datetime.date(2022, 6, 1))
    end_date   = add_months(start_date, random.choices([12, 18, 24, 6], weights=[35, 30, 25, 10])[0])
    tenant     = make_tenant('s')
    contract   = make_contract(tenant, room, start_date, end_date)
    inv_start  = max(PERIOD_START, start_date.replace(day=1))
    create_invoices(contract, month_range(inv_start, today.replace(day=1)),
                    contract.Water_Meter_Start, contract.Elec_Meter_Start, overdue_ids)
print(f"  เสร็จสิ้น")

# ========== Single moveout rooms: ย้ายออก 1 รอบ ==========
print(f"สร้างประวัติย้ายออก 1 รอบ ({len(single_moveout_rooms)} ห้อง)...")
exit_pool = month_range(PERIOD_START, datetime.date(2026, 2, 1))

for room in single_moveout_rooms:
    exit_m = random.choice(exit_pool)
    dur    = random.randint(4, 20)
    start_m = add_months(exit_m, -dur)

    w, e = seed_tenant(room, start_m, exit_m,
                       random.randint(100, 500), random.randint(100, 500))

    gap_m      = add_months(exit_m, random.randint(1, 3))
    has_new    = gap_m <= today.replace(day=1) and random.random() < 0.75
    if has_new:
        new_end_m = add_months(gap_m, random.randint(12, 24))
        seed_tenant(room, gap_m, new_end_m, w, e, is_current=True, overdue_ids=overdue_ids)
    else:
        room.Status      = 'ว่าง'
        room.Status_Flag = random.choice(['ปกติ', 'รอทำความสะอาด'])
        room.save()
print(f"  เสร็จสิ้น")

# ========== Double moveout rooms: ย้ายออก 2 รอบ ==========
print(f"สร้างประวัติย้ายออก 2 รอบ ({len(double_moveout_rooms)} ห้อง)...")
# รอบแรกต้องออกก่อน ส.ค. 2025 เพื่อให้มีพื้นที่รอบสอง
exit_pool_early = month_range(PERIOD_START, datetime.date(2025, 8, 1))

for room in double_moveout_rooms:
    # ---- รอบที่ 1 ----
    exit_m1  = random.choice(exit_pool_early)
    dur1     = random.randint(4, 14)
    start_m1 = add_months(exit_m1, -dur1)

    w, e = seed_tenant(room, start_m1, exit_m1,
                       random.randint(100, 500), random.randint(100, 500))

    # ---- รอบที่ 2 ----
    gap2    = random.randint(1, 2)
    start_m2 = add_months(exit_m1, gap2)
    # อยู่นานแค่ไหน (ต้องออกก่อน today อย่างน้อย 1 เดือน)
    max_stay2 = max(4, (today.year - start_m2.year) * 12 + (today.month - start_m2.month) - 1)
    dur2     = random.randint(4, max(4, min(12, max_stay2)))
    exit_m2  = add_months(start_m2, dur2)

    if start_m2 > today.replace(day=1):
        # ไม่มีพื้นที่ → ห้องว่าง
        room.Status      = 'ว่าง'
        room.Status_Flag = 'รอทำความสะอาด'
        room.save()
        continue

    exit_m2 = min(exit_m2, add_months(today.replace(day=1), -1))
    w, e = seed_tenant(room, start_m2, exit_m2, w, e)

    # ---- รอบที่ 3 (ผู้เช่าปัจจุบัน, 70% โอกาส) ----
    gap3    = random.randint(1, 2)
    start_m3 = add_months(exit_m2, gap3)
    has_cur  = start_m3 <= today.replace(day=1) and random.random() < 0.70
    if has_cur:
        cur_end_m = add_months(start_m3, random.randint(12, 24))
        seed_tenant(room, start_m3, cur_end_m, w, e, is_current=True, overdue_ids=overdue_ids)
    else:
        room.Status      = 'ว่าง'
        room.Status_Flag = random.choice(['ปกติ', 'รอทำความสะอาด'])
        room.save()
print(f"  เสร็จสิ้น")

# ========== อัปเดต invoice เกินกำหนด ==========
updated = Invoice.objects.filter(Status='รอชำระ', Due_Date__lt=today).update(Status='เกินกำหนด')
print(f"  อัปเดต {updated} invoices เป็น เกินกำหนด")

# ========== Booking ==========
print("สร้างการจอง...")
bookable = list(Room.objects.filter(Status='ว่าง', Status_Flag='ปกติ'))
booking_rooms = random.sample(bookable, min(6, len(bookable)))
for i, room in enumerate(booking_rooms):
    Booking.objects.create(
        Room_ID    = room,
        First_Name = random.choice(first_names),
        Last_Name  = random.choice(last_names),
        ID_Card    = f"{random.randint(1000000000000, 9999999999999)}",
        Phone      = f"08{random.randint(10000000, 99999999)}",
        Email      = f"booking{i}@example.com",
        Status     = 'รอยืนยัน',
    )
    room.Status_Flag = 'จอง'; room.save()
print(f"  สร้าง {Booking.objects.count()} การจอง")

# ========== Maintenance ==========
print("สร้างแจ้งซ่อม...")
problems = [
    'ก๊อกน้ำรั่ว','แอร์ไม่เย็น','ไฟฟ้าขัดข้อง','ประตูล็อคไม่ได้',
    'ท่อน้ำตัน','หลอดไฟขาด','หน้าต่างปิดไม่สนิท','ฝักบัวชำรุด',
    'พัดลมไม่หมุน','เพดานรั่ว','โถสุขภัณฑ์ชำรุด','ราวระเบียงชำรุด',
]

# รายการที่ยังค้างอยู่ (รอดำเนินการ / กำลังซ่อม)
for room in maintenance_rooms:
    Maintenance.objects.create(
        Room_ID        = room,
        Problem_Detail = random.choice(problems),
        Report_Date    = today - datetime.timedelta(days=random.randint(1, 30)),
        Status         = random.choice(['รอดำเนินการ', 'กำลังซ่อม']),
        Repair_Cost    = random.choice([0, 0, 500, 800, 1000]),
    )

# ประวัติที่ซ่อมเสร็จแล้ว (เพื่อให้มีข้อมูลย้อนหลัง)
done_pool = [r for r in all_rooms if r not in maintenance_rooms]
done_rooms = random.sample(done_pool, min(20, len(done_pool)))
for room in done_rooms:
    report_date = today - datetime.timedelta(days=random.randint(14, 300))
    Maintenance.objects.create(
        Room_ID        = room,
        Problem_Detail = random.choice(problems),
        Report_Date    = report_date,
        Status         = 'ซ่อมเสร็จ',
        Repair_Cost    = random.choice([300, 500, 800, 1000, 1500, 2000, 3000]),
    )

print(f"  รอดำเนินการ/กำลังซ่อม : {Maintenance.objects.filter(Status__in=['รอดำเนินการ','กำลังซ่อม']).count()}")
print(f"  ซ่อมเสร็จ             : {Maintenance.objects.filter(Status='ซ่อมเสร็จ').count()}")

# ========== สรุป ==========
print(f"\n{'='*52}")
print(f"ห้องทั้งหมด               : {Room.objects.count()}")
print(f"  มีผู้เช่า (ปกติ)        : {Room.objects.filter(Status='มีผู้เช่า', Status_Flag='ปกติ').count()}")
print(f"  แจ้งย้ายออก             : {Room.objects.filter(Status_Flag='แจ้งย้ายออก').count()}")
print(f"  รอทำความสะอาด           : {Room.objects.filter(Status_Flag='รอทำความสะอาด').count()}")
print(f"  ว่าง                    : {Room.objects.filter(Status='ว่าง').count()}")
print(f"  ซ่อมบำรุง               : {Room.objects.filter(Status='ซ่อมบำรุง').count()}")
print(f"────────────────────────────────────────────────────")
print(f"Contract ใช้งาน           : {Contract.objects.filter(Status='ใช้งาน').count()}")
print(f"Contract สิ้นสุด          : {Contract.objects.filter(Status='สิ้นสุด').count()}")
print(f"────────────────────────────────────────────────────")
print(f"การจอง (รอยืนยัน)         : {Booking.objects.filter(Status='รอยืนยัน').count()}")
print(f"────────────────────────────────────────────────────")
print(f"Invoice รวมทั้งหมด         : {Invoice.objects.count()}")
print(f"  ชำระแล้ว                : {Invoice.objects.filter(Status='ชำระแล้ว').count()}")
print(f"  รอชำระ                  : {Invoice.objects.filter(Status='รอชำระ').count()}")
print(f"  เกินกำหนด               : {Invoice.objects.filter(Status='เกินกำหนด').count()}")
print(f"────────────────────────────────────────────────────")
print(f"แจ้งซ่อมทั้งหมด            : {Maintenance.objects.count()}")
print(f"{'='*52}")
