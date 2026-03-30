from django import forms
from .models import Tenant, Room, Contract, Invoice, MonthlyBill, Utility, Fine, Maintenance, Booking, EmployeeSalary


# ฟอร์มผู้เช่า
class TenantForm(forms.ModelForm):
    Email = forms.EmailField(
        label='อีเมล',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'example@email.com'}),
        required=True
    )

    class Meta:
        model  = Tenant
        fields = ['First_Name', 'Last_Name', 'ID_Card', 'Phone', 'Email', 'Line_ID', 'Address']
        labels = {
            'First_Name': 'ชื่อ',
            'Last_Name':  'นามสกุล',
            'ID_Card':    'เลขบัตรประชาชน',
            'Phone':      'เบอร์โทรติดต่อ',
            'Line_ID':    'Line ID',
            'Address':    'ที่อยู่',
        }
        widgets = {
            'First_Name': forms.TextInput(attrs={'class': 'form-control'}),
            'Last_Name':  forms.TextInput(attrs={'class': 'form-control'}),
            'ID_Card':    forms.TextInput(attrs={'class': 'form-control', 'maxlength': '13'}),
            'Phone':      forms.TextInput(attrs={'class': 'form-control'}),
            'Line_ID':    forms.TextInput(attrs={'class': 'form-control'}),
            'Address':    forms.TextInput(attrs={'class': 'form-control'}),
        }


# ฟอร์มห้องพัก
class RoomForm(forms.ModelForm):
    class Meta:
        model  = Room
        fields = ['Room_Number', 'Building_No', 'Floor', 'Status', 'Status_Flag']
        labels = {
            'Room_Number': 'เลขห้อง',
            'Building_No': 'อาคาร',
            'Floor':       'ชั้น',
            'Status':      'สถานะหลัก',
            'Status_Flag': 'สถานะเสริม',
        }
        widgets = {
            'Room_Number': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '4'}),
            'Building_No': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '1'}),
            'Floor':       forms.TextInput(attrs={'class': 'form-control', 'maxlength': '1'}),
            'Status':      forms.Select(attrs={'class': 'form-select'}),
            'Status_Flag': forms.Select(attrs={'class': 'form-select'}),
        }


# ฟอร์มสัญญาเช่า
class ContractForm(forms.ModelForm):
    # dropdown ระยะเวลา 1-24 เดือน
    duration_months = forms.ChoiceField(
        choices=[(i, f'{i} เดือน') for i in range(1, 25)],
        label='ระยะเวลาเข้าพัก',
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_duration'}),
        required=False,
    )

    class Meta:
        model  = Contract
        fields = [
            'Room_ID', 'Tenant_ID',
            'Start_Date', 'End_Date',
            'Rent_Price', 'Deposit', 'Deposit_Advance',
            'Water_Cost_Unit', 'Elec_Cost_Unit',
            'Water_Meter_Start', 'Elec_Meter_Start',
            'Status',
        ]
        labels = {
            'Room_ID':           'ห้องพัก',
            'Tenant_ID':         'ผู้เช่า',
            'Start_Date':        'วันที่เริ่มสัญญา',
            'End_Date':          'วันที่สิ้นสุดสัญญา',
            'Rent_Price':        'ค่าเช่าห้องต่อเดือน',
            'Deposit':           'เงินประกันห้อง',
            'Deposit_Advance':   'เงินมัดจำ',
            'Water_Cost_Unit':   'ค่าน้ำต่อหน่วย (บาท)',
            'Elec_Cost_Unit':    'ค่าไฟต่อหน่วย (บาท)',
            'Water_Meter_Start': 'หมายเลขมิเตอร์น้ำเริ่มต้น',
            'Elec_Meter_Start':  'หมายเลขมิเตอร์ไฟเริ่มต้น',
            'Status':            'สถานะสัญญา',
        }
        widgets = {
            'Room_ID':           forms.Select(attrs={'class': 'form-select select2'}),
            'Tenant_ID':         forms.Select(attrs={'class': 'form-select select2'}),
            'Start_Date':        forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'id': 'id_start_date'}),
            'End_Date':          forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'id': 'id_end_date'}),
            'Rent_Price':        forms.TextInput(attrs={'class': 'form-control money-input'}),
            'Deposit':           forms.TextInput(attrs={'class': 'form-control money-input'}),
            'Deposit_Advance':   forms.TextInput(attrs={'class': 'form-control money-input'}),
            'Water_Cost_Unit':   forms.NumberInput(attrs={'class': 'form-control'}),
            'Elec_Cost_Unit':    forms.NumberInput(attrs={'class': 'form-control'}),
            'Water_Meter_Start': forms.NumberInput(attrs={'class': 'form-control'}),
            'Elec_Meter_Start':  forms.NumberInput(attrs={'class': 'form-control'}),
            'Status':            forms.Select(attrs={'class': 'form-select'}),
        }
# ฟอร์มสร้างใบแจ้งหนี้
class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['Contract_ID', 'Billing_Date', 'Due_Date']
        labels = {
            'Contract_ID':  'รหัสสัญญา',
            'Billing_Date': 'วันที่ออกบิล',
            'Due_Date':     'วันครบกำหนดชำระ',
        }
        widgets = {
            'Contract_ID':  forms.Select(attrs={'class': 'form-select'}),
            'Billing_Date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'Due_Date':     forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        import datetime
        today      = datetime.date.today()
        next_month = (today.replace(day=1) + datetime.timedelta(days=32)).replace(day=1)
        # วันออกบิล = 25 ของเดือนนี้, ครบกำหนด = 5 ของเดือนถัดไป
        self.fields['Billing_Date'].initial = today.replace(day=25).strftime('%Y-%m-%d')
        self.fields['Due_Date'].initial     = next_month.replace(day=5).strftime('%Y-%m-%d')
        self.fields['Contract_ID'].queryset = Contract.objects.filter(Status='ใช้งาน')


# ฟอร์มกรอกค่าน้ำ/ไฟ
class UtilityForm(forms.ModelForm):
    class Meta:
        model  = Utility
        fields = [
            'Bill_Month',
            'Water_Unit_Used',
            'Elec_Unit_Used',
            'Water_Cost_Unit', 'Elec_Cost_Unit',
        ]
        labels = {
            'Bill_Month':        'เดือนที่คิด',
            'Water_Unit_Used':   'หน่วยน้ำที่ใช้',
            'Elec_Unit_Used':    'หน่วยไฟที่ใช้',
            'Water_Cost_Unit':   'ราคาน้ำ/หน่วย (บาท)',
            'Elec_Cost_Unit':    'ราคาไฟ/หน่วย (บาท)',
        }
        widgets = {
            'Bill_Month':        forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'Water_Unit_Used':   forms.NumberInput(attrs={'class': 'form-control'}),
            'Elec_Unit_Used':    forms.NumberInput(attrs={'class': 'form-control'}),
            'Water_Cost_Unit':   forms.NumberInput(attrs={'class': 'form-control'}),
            'Elec_Cost_Unit':    forms.NumberInput(attrs={'class': 'form-control'}),
        }


# ฟอร์มบันทึกการชำระเงิน
class PaymentForm(forms.ModelForm):
    class Meta:
        model  = Invoice
        fields = ['Paid_Date']
        labels = {'Paid_Date': 'วันที่ชำระ'}
        widgets = {
            'Paid_Date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


# ฟอร์มค่าปรับ
class FineForm(forms.ModelForm):
    class Meta:
        model  = Fine
        fields = ['Reason', 'Amount', 'Fine_Date']
        labels = {
            'Reason':    'เหตุผล',
            'Amount':    'จำนวนเงิน',
            'Fine_Date': 'วันที่ปรับ',
        }
        widgets = {
            'Reason':    forms.TextInput(attrs={'class': 'form-control'}),
            'Amount':    forms.NumberInput(attrs={'class': 'form-control'}),
            'Fine_Date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
# ฟอร์มแจ้งซ่อม
class MaintenanceForm(forms.ModelForm):
    class Meta:
        model  = Maintenance
        fields = ['Room_ID', 'Problem_Detail', 'Report_Date', 'Status', 'Resolved_Date', 'Repair_Cost']
        labels = {
            'Room_ID':        'ห้อง',
            'Problem_Detail': 'รายละเอียดปัญหา',
            'Report_Date':    'วันที่แจ้ง',
            'Status':         'สถานะ',
            'Resolved_Date':  'วันที่ซ่อมเสร็จ',
            'Repair_Cost':    'ค่าซ่อม (บาท)',
        }
        widgets = {
            'Room_ID':        forms.Select(attrs={'class': 'form-select'}),
            'Problem_Detail': forms.TextInput(attrs={'class': 'form-control'}),
            'Report_Date':    forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'Status':         forms.Select(attrs={'class': 'form-select'}),
            'Resolved_Date':  forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'Repair_Cost':    forms.TextInput(attrs={'class': 'form-control money-input'}),
        }

class BookingForm(forms.ModelForm):
    class Meta:
        model  = Booking
        fields = ['Room_ID', 'First_Name', 'Last_Name', 'ID_Card', 'Phone', 'Email', 'Line_ID', 'Address', 'Note']
        labels = {
            'Room_ID':    'ห้องที่จอง',
            'First_Name': 'ชื่อ',
            'Last_Name':  'นามสกุล',
            'ID_Card':    'เลขบัตรประชาชน',
            'Phone':      'เบอร์โทรติดต่อ',
            'Email':      'อีเมล',
            'Line_ID':    'Line ID',
            'Address':    'ที่อยู่',
            'Note':       'หมายเหตุ',
        }
        widgets = {
            'Room_ID':    forms.Select(attrs={'class': 'form-select'}),
            'First_Name': forms.TextInput(attrs={'class': 'form-control'}),
            'Last_Name':  forms.TextInput(attrs={'class': 'form-control'}),
            'ID_Card':    forms.TextInput(attrs={'class': 'form-control', 'maxlength': '13'}),
            'Phone':      forms.TextInput(attrs={'class': 'form-control'}),
            'Email':      forms.EmailInput(attrs={'class': 'form-control'}),
            'Line_ID':    forms.TextInput(attrs={'class': 'form-control'}),
            'Address':    forms.TextInput(attrs={'class': 'form-control'}),
            'Note':       forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_ID_Card(self):
        id_card = self.cleaned_data.get('ID_Card')
        from .models import Tenant, Booking
        if Tenant.objects.filter(ID_Card=id_card).exists():
            raise forms.ValidationError("มีเลขบัตรประชาชนนี้อยู่ในระบบแล้ว (เป็นผู้เช่า)")
        if Booking.objects.filter(ID_Card=id_card, Status='รอยืนยัน').exists():
            raise forms.ValidationError("มีเลขบัตรประชาชนนี้อยู่ในระบบแล้ว (กำลังดำเนินการจอง)")
        return id_card


# ฟอร์มเงินเดือนพนักงาน
class EmployeeSalaryForm(forms.ModelForm):
    class Meta:
        model  = EmployeeSalary
        fields = ['First_Name', 'Last_Name', 'ID_Card', 'Role', 'Monthly_Salary', 'Is_Active']
        labels = {
            'First_Name':     'ชื่อ',
            'Last_Name':      'นามสกุล',
            'ID_Card':        'เลขบัตรประชาชน',
            'Role':           'ตำแหน่ง',
            'Monthly_Salary': 'เงินเดือน (บาท)',
            'Is_Active':      'ยังทำงานอยู่',
        }
        widgets = {
            'First_Name':     forms.TextInput(attrs={'class': 'form-control'}),
            'Last_Name':      forms.TextInput(attrs={'class': 'form-control'}),
            'ID_Card':        forms.TextInput(attrs={'class': 'form-control', 'maxlength': '13', 'placeholder': 'กรอกเลข 13 หลัก'}),
            'Role':           forms.Select(attrs={'class': 'form-select'}),
            'Monthly_Salary': forms.TextInput(attrs={'class': 'form-control money-input'}),
            'Is_Active':      forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_ID_Card(self):
        id_card = self.cleaned_data.get('ID_Card')
        if not id_card:
            return id_card
        if len(id_card) != 13 or not id_card.isdigit():
            raise forms.ValidationError('เลขบัตรประชาชนต้องเป็นตัวเลข 13 หลัก')
        qs = EmployeeSalary.objects.filter(ID_Card=id_card)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('มีพนักงานที่ใช้เลขบัตรประชาชนนี้แล้ว')
        return id_card