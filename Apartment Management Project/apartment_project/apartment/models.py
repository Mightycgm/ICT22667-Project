from django.db import models


# ตาราง 1: ผู้เช่า
class Tenant(models.Model):
    Tenant_ID   = models.AutoField(primary_key=True)
    First_Name  = models.CharField(max_length=50)
    Last_Name   = models.CharField(max_length=50)
    ID_Card     = models.CharField(max_length=13, unique=True)
    Phone       = models.CharField(max_length=20)
    Email       = models.EmailField(max_length=50, null=True, blank=True)
    Line_ID     = models.CharField(max_length=50, null=True, blank=True)   # เพิ่มใหม่
    Address     = models.CharField(max_length=255, null=True, blank=True)  # เพิ่มใหม่

    class Meta:
        db_table = 'TENANT'

    def __str__(self):
        return f"{self.First_Name} {self.Last_Name}"


# ตาราง 2: ห้องพัก
class Room(models.Model):
    STATUS_CHOICES = [
        ('ว่าง',       'ว่าง'),
        ('มีผู้เช่า',  'มีผู้เช่า'),
        ('ซ่อมบำรุง',  'ซ่อมบำรุง'),
    ]
    FLAG_CHOICES = [
        ('ปกติ',              'ปกติ'),
        ('แจ้งย้ายออก',       'แจ้งย้ายออก'),
        ('จอง',               'จอง'),
        ('รอทำความสะอาด',     'รอทำความสะอาด'),
    ]
    Room_ID     = models.AutoField(primary_key=True)
    Room_Number = models.CharField(max_length=4, unique=True)
    Building_No = models.CharField(max_length=1)
    Floor       = models.CharField(max_length=1)
    Status      = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ว่าง')
    Status_Flag = models.CharField(max_length=20, choices=FLAG_CHOICES, default='ปกติ')  # เพิ่มใหม่

    class Meta:
        db_table = 'ROOM'

    def __str__(self):
        return f"ห้อง {self.Room_Number}"


# ตาราง 3: สัญญาเช่า
class Contract(models.Model):
    STATUS_CHOICES = [
        ('ใช้งาน', 'ใช้งาน'),
        ('หมดอายุ', 'หมดอายุ'),
        ('ยกเลิก',  'ยกเลิก'),
    ]
    Contract_ID      = models.AutoField(primary_key=True)
    Tenant_ID        = models.ForeignKey(Tenant, on_delete=models.PROTECT, db_column='Tenant_ID')
    Room_ID          = models.ForeignKey(Room, on_delete=models.PROTECT, db_column='Room_ID')
    Start_Date       = models.DateField()
    End_Date         = models.DateField()
    Deposit          = models.DecimalField(max_digits=10, decimal_places=2)
    Deposit_Advance  = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # เงินมัดจำ
    Rent_Price       = models.DecimalField(max_digits=8,  decimal_places=2)
    Water_Cost_Unit  = models.IntegerField(default=18)   # ค่าน้ำ/หน่วย
    Elec_Cost_Unit   = models.IntegerField(default=8)    # ค่าไฟ/หน่วย
    Water_Meter_Start = models.DecimalField(max_digits=8, decimal_places=2, default=0)  # มิเตอร์น้ำเริ่มต้น
    Elec_Meter_Start  = models.DecimalField(max_digits=8, decimal_places=2, default=0)  # มิเตอร์ไฟเริ่มต้น
    Status           = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ใช้งาน')

    class Meta:
        db_table = 'CONTRACT'

    def __str__(self):
        return f"สัญญา #{self.Contract_ID} - {self.Tenant_ID}"


# ตาราง 4: ใบแจ้งหนี้
class Invoice(models.Model):
    STATUS_CHOICES = [
        ('รอชำระ', 'รอชำระ'),
        ('ชำระแล้ว', 'ชำระแล้ว'),
        ('เกินกำหนด', 'เกินกำหนด'),
    ]
    Invoice_ID   = models.AutoField(primary_key=True)
    Contract_ID  = models.ForeignKey(Contract, on_delete=models.PROTECT, db_column='Contract_ID')
    Billing_Date = models.DateField()
    Due_Date     = models.DateField()
    Grand_Total  = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    Status       = models.CharField(max_length=20, choices=STATUS_CHOICES, default='รอชำระ')
    Paid_Date    = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'INVOICE'
        unique_together = [['Contract_ID', 'Billing_Date']]

    def __str__(self):
        return f"Invoice #{self.Invoice_ID}"


# ตาราง 5: ค่าเช่ารายเดือน
class MonthlyBill(models.Model):
    Monthly_Bill_ID = models.AutoField(primary_key=True)
    Invoice_ID      = models.OneToOneField(Invoice, on_delete=models.PROTECT, db_column='Invoice_ID')
    Bill_Month      = models.DateField()   # เก็บเป็น YYYY-MM-01
    Amount          = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'MONTHLY_BILL'

    def __str__(self):
        return f"Bill #{self.Monthly_Bill_ID}"


# ตาราง 6: ค่าน้ำ/ไฟ
class Utility(models.Model):
    Utility_ID        = models.AutoField(primary_key=True)
    Invoice_ID        = models.OneToOneField(Invoice, on_delete=models.PROTECT, db_column='Invoice_ID')
    Room_ID           = models.ForeignKey(Room, on_delete=models.PROTECT, db_column='Room_ID')
    Bill_Month        = models.DateField()
    Water_Unit_Before = models.DecimalField(max_digits=5, decimal_places=2)
    Water_Unit_After  = models.DecimalField(max_digits=5, decimal_places=2)
    Water_Unit_Used   = models.DecimalField(max_digits=5, decimal_places=2)   # After - Before
    Elec_Unit_Used    = models.DecimalField(max_digits=6, decimal_places=2)
    Water_Cost_Unit   = models.IntegerField()
    Elec_Cost_Unit    = models.IntegerField()
    Water_Total       = models.DecimalField(max_digits=10, decimal_places=2)  # Water_Unit_Used × Water_Cost_Unit
    Elec_Total        = models.DecimalField(max_digits=10, decimal_places=2)  # Elec_Unit_Used × Elec_Cost_Unit

    class Meta:
        db_table = 'UTILITY'

    def __str__(self):
        return f"Utility #{self.Utility_ID}"


# ตาราง 7: แจ้งซ่อม
class Maintenance(models.Model):
    STATUS_CHOICES = [
        ('รอดำเนินการ', 'รอดำเนินการ'),
        ('กำลังซ่อม', 'กำลังซ่อม'),
        ('ซ่อมเสร็จ', 'ซ่อมเสร็จ'),
    ]
    Maintenance_ID = models.AutoField(primary_key=True)
    Invoice_ID     = models.ForeignKey(Invoice, on_delete=models.SET_NULL, null=True, blank=True, db_column='Invoice_ID')
    Room_ID        = models.ForeignKey(Room, on_delete=models.PROTECT, db_column='Room_ID')
    Problem_Detail = models.CharField(max_length=255)
    Report_Date    = models.DateField()
    Status         = models.CharField(max_length=50, choices=STATUS_CHOICES, default='รอดำเนินการ')
    Resolved_Date  = models.DateField(null=True, blank=True)
    Repair_Cost    = models.IntegerField(default=0)

    class Meta:
        db_table = 'MAINTENANCE'

    def __str__(self):
        return f"แจ้งซ่อม #{self.Maintenance_ID} ห้อง {self.Room_ID}"


# ตาราง 8: ค่าปรับ
class Fine(models.Model):
    Fine_ID    = models.AutoField(primary_key=True)
    Invoice_ID = models.ForeignKey(Invoice, on_delete=models.PROTECT, db_column='Invoice_ID')
    Reason     = models.CharField(max_length=100)
    Amount     = models.DecimalField(max_digits=10, decimal_places=2)
    Fine_Date  = models.DateField()

    class Meta:
        db_table = 'FINE'

    def __str__(self):
        return f"ค่าปรับ #{self.Fine_ID}"

# ตาราง: การจองห้อง
class Booking(models.Model):
    Booking_ID   = models.AutoField(primary_key=True)
    Room_ID      = models.ForeignKey(Room, on_delete=models.PROTECT, db_column='Room_ID')
    # ข้อมูลผู้จอง (เก็บไว้ก่อน ยังไม่ได้เป็น Tenant)
    First_Name   = models.CharField(max_length=50)
    Last_Name    = models.CharField(max_length=50)
    ID_Card      = models.CharField(max_length=13)
    Phone        = models.CharField(max_length=20)
    Email        = models.EmailField(max_length=50, null=True, blank=True)
    Line_ID      = models.CharField(max_length=50, null=True, blank=True)
    Address      = models.CharField(max_length=255, null=True, blank=True)
    # ข้อมูลห้องที่ต้องการ
    Note         = models.CharField(max_length=255, null=True, blank=True)
    Booking_Date = models.DateField(auto_now_add=True)
    Status       = models.CharField(max_length=20, default='รอยืนยัน')
    # ค่า: รอยืนยัน / ยืนยันแล้ว / ยกเลิก

    class Meta:
        db_table = 'BOOKING'

    def __str__(self):
        return f"จอง #{self.Booking_ID} - {self.First_Name} {self.Last_Name} ห้อง {self.Room_ID}"