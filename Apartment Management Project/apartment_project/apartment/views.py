from django.shortcuts import render, get_object_or_404, redirect
from django.db import models as django_models
from django.db.models import Sum, Count, Q
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.template.loader import render_to_string
from decimal import Decimal
from .models import Tenant, Room, Contract, Invoice, MonthlyBill, Utility, Fine, Maintenance, Booking
from .forms  import TenantForm, RoomForm, ContractForm, InvoiceForm, UtilityForm, PaymentForm, FineForm, MaintenanceForm, BookingForm
from .decorators import role_required, not_readonly
import datetime
from django.core.mail import send_mass_mail
import time


# ==================== DASHBOARD ====================

@login_required
@role_required('ADMIN', 'MANAGER', 'STAFF', 'READONLY', 'METER')
def dashboard(request):
    from .middleware import get_user_role
    if get_user_role(request.user) == 'METER':
        return redirect('meter_input')
    import datetime
    today = datetime.date.today()
    rooms = Room.objects.all().order_by('Building_No', 'Floor', 'Room_Number')

    Invoice.objects.filter(
        Status='รอชำระ',
        Due_Date__lt=today
    ).update(Status='เกินกำหนด')

    # ห้องที่มี invoice เกินกำหนด → สีแดง
    overdue_room_ids = list(Invoice.objects.filter(
        Status='เกินกำหนด'
    ).values_list('Contract_ID__Room_ID', flat=True))

    # ห้องที่มี invoice รอชำระ (ยังไม่เกิน) → แสดง $
    unpaid_room_ids = list(Invoice.objects.filter(
        Status='รอชำระ'
    ).values_list('Contract_ID__Room_ID', flat=True))

    # ห้องที่มีแจ้งซ่อมค้าง → แสดง 🔧
    repair_room_ids = list(Maintenance.objects.exclude(
        Status='ซ่อมเสร็จ'
    ).values_list('Room_ID', flat=True))

    # Auto-generate invoice ถ้าวันที่ >= 25
    if today.day >= 25:
        auto_generate_invoices()

    # --- นับตาม "สีจริง" ที่แสดงใน badge ---
    count_white    = rooms.filter(Status='ว่าง', Status_Flag='ปกติ').count()
    count_pin      = rooms.filter(Status='ว่าง', Status_Flag='จอง').count()
    count_broom    = rooms.filter(Status='ว่าง', Status_Flag='รอทำความสะอาด').count()
    count_blue     = rooms.filter(Status='มีผู้เช่า', Status_Flag='ปกติ').exclude(
                         Room_ID__in=overdue_room_ids).count()
    count_yellow   = rooms.filter(Status='มีผู้เช่า', Status_Flag='แจ้งย้ายออก').count()
    count_red      = rooms.filter(Room_ID__in=overdue_room_ids).count()
    count_black    = rooms.filter(Status='ซ่อมบำรุง').count()
    count_repair   = len(set(repair_room_ids))
    count_unpaid   = len(set(unpaid_room_ids))

    context = {
        'rooms':            rooms,
        'overdue_room_ids': overdue_room_ids,
        'unpaid_room_ids':  unpaid_room_ids,
        'repair_room_ids':  repair_room_ids,
        # summary cards
        'total_rooms':   rooms.count(),
        'count_white':   count_white,
        'count_pin':     count_pin,
        'count_broom':   count_broom,
        'count_blue':    count_blue,
        'count_yellow':  count_yellow,
        'count_red':     count_red,
        'count_black':   count_black,
        'count_repair':  count_repair,
        'count_unpaid':  count_unpaid,
    }
    return render(request, 'apartment/dashboard.html', context)


# ==================== TENANT ====================

@login_required
@role_required('ADMIN', 'MANAGER', 'STAFF', 'READONLY')
def tenant_list(request):
    # ค้นหาผู้เช่าด้วยชื่อหรือนามสกุล
    query   = request.GET.get('q', '')
    tenants = Tenant.objects.all()
    if query:
        tenants = tenants.filter(First_Name__icontains=query) | tenants.filter(Last_Name__icontains=query)
    return render(request, 'apartment/tenant/list.html', {'tenants': tenants, 'query': query})

@login_required
@role_required('ADMIN', 'MANAGER')
def tenant_create(request):
    form = TenantForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('tenant_list')
    return render(request, 'apartment/tenant/form.html', {'form': form, 'title': 'เพิ่มผู้เช่า'})

@login_required
@role_required('ADMIN', 'MANAGER')
def tenant_edit(request, pk):
    tenant = get_object_or_404(Tenant, pk=pk)
    form   = TenantForm(request.POST or None, instance=tenant)
    if form.is_valid():
        form.save()
        return redirect('tenant_list')
    return render(request, 'apartment/tenant/form.html', {'form': form, 'title': 'แก้ไขผู้เช่า'})

@login_required
@role_required('ADMIN')
def tenant_delete(request, pk):
    tenant = get_object_or_404(Tenant, pk=pk)
    if request.method == 'POST':
        tenant.delete()
        return redirect('tenant_list')
    return render(request, 'apartment/tenant/confirm_delete.html', {'object': tenant, 'title': 'ลบผู้เช่า'})


# ==================== ROOM ====================

@login_required
@role_required('ADMIN', 'MANAGER', 'STAFF', 'READONLY')
def room_list(request):
    rooms = Room.objects.all().order_by('Room_Number')
    return render(request, 'apartment/room/list.html', {'rooms': rooms})

@login_required
@role_required('ADMIN', 'MANAGER')
def room_create(request):
    form = RoomForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('room_list')
    return render(request, 'apartment/room/form.html', {'form': form, 'title': 'เพิ่มห้องพัก'})

@login_required
@role_required('ADMIN', 'MANAGER')
def room_edit(request, pk):
    room = get_object_or_404(Room, pk=pk)
    form = RoomForm(request.POST or None, instance=room)
    if form.is_valid():
        form.save()
        return redirect('room_list')
    return render(request, 'apartment/room/form.html', {'form': form, 'title': 'แก้ไขห้องพัก'})

@login_required
@role_required('ADMIN')
def room_delete(request, pk):
    room = get_object_or_404(Room, pk=pk)
    if request.method == 'POST':
        room.delete()
        return redirect('room_list')
    return render(request, 'apartment/room/confirm_delete.html', {'object': room, 'title': 'ลบห้องพัก'})

@login_required
@role_required('ADMIN', 'MANAGER', 'STAFF', 'READONLY')
def room_detail(request, pk):
    room     = get_object_or_404(Room, pk=pk)

    # ดึงสัญญาที่ใช้งานอยู่ของห้องนี้
    contract = Contract.objects.filter(
        Room_ID=room, Status='ใช้งาน'
    ).select_related('Tenant_ID').first()

    # ดึง invoice ของสัญญานี้
    invoices = Invoice.objects.filter(
        Contract_ID=contract
    ).order_by('-Billing_Date') if contract else []

    # ดึงแจ้งซ่อมของห้องนี้
    maintenances = Maintenance.objects.filter(
        Room_ID=room
    ).order_by('-Report_Date')

    # ดึงการจองที่รอยืนยัน
    booking = Booking.objects.filter(
        Room_ID=room, Status='รอยืนยัน'
    ).first()

    return render(request, 'apartment/room/detail.html', {
        'room':         room,
        'contract':     contract,
        'invoices':     invoices,
        'maintenances': maintenances,
        'booking':      booking,
    })
# ==================== CONTRACT ====================

@login_required
@role_required('ADMIN', 'MANAGER', 'STAFF', 'READONLY')
def contract_list(request):
    contracts = Contract.objects.select_related('Tenant_ID', 'Room_ID').all()
    return render(request, 'apartment/contract/list.html', {'contracts': contracts})

@login_required
@role_required('ADMIN', 'MANAGER')
def contract_create(request):
    # ดึงห้องว่างเท่านั้น
    form = ContractForm(request.POST or None)
    form.fields['Room_ID'].queryset = Room.objects.filter(Status='ว่าง')

    if form.is_valid():
        contract = form.save(commit=False)
        contract.save()
        # อัปเดตสถานะห้องเป็น "มีผู้เช่า"
        room        = contract.Room_ID
        room.Status = 'มีผู้เช่า'
        room.save()
        return redirect('contract_print', pk=contract.Contract_ID)  # ไปหน้าพิมพ์สัญญาเลย

    return render(request, 'apartment/contract/form.html', {
        'form':  form,
        'title': 'สร้างสัญญาเข้าพัก',
    })


@login_required
@role_required('ADMIN', 'MANAGER')
def contract_edit(request, pk):
    contract = get_object_or_404(Contract, pk=pk)
    form     = ContractForm(request.POST or None, instance=contract)
    if form.is_valid():
        form.save()
        return redirect('contract_list')
    return render(request, 'apartment/contract/form.html', {
        'form':  form,
        'title': 'แก้ไขสัญญาเข้าพัก',
    })


@login_required
@role_required('ADMIN', 'MANAGER', 'STAFF', 'READONLY')
def contract_print(request, pk):
    # หน้าพิมพ์สัญญา
    contract = get_object_or_404(Contract, pk=pk)
    return render(request, 'apartment/contract/print.html', {'contract': contract})

@login_required
@role_required('ADMIN')
def contract_delete(request, pk):
    contract = get_object_or_404(Contract, pk=pk)
    if request.method == 'POST':
        contract.delete()
        return redirect('contract_list')
    return render(request, 'apartment/contract/confirm_delete.html', {'object': contract, 'title': 'ลบสัญญาเช่า'})
# ==================== INVOICE ====================

@login_required
@role_required('ADMIN', 'MANAGER', 'STAFF', 'READONLY')
def invoice_list(request):
    import datetime
    today = datetime.date.today()

    # อัปเดตสถานะเกินกำหนดอัตโนมัติ
    Invoice.objects.filter(
        Status='รอชำระ', Due_Date__lt=today
    ).update(Status='เกินกำหนด')

    invoices = Invoice.objects.select_related(
        'Contract_ID__Tenant_ID', 'Contract_ID__Room_ID'
    ).all()

    # --- Filter ---
    q        = request.GET.get('q', '')
    month    = request.GET.get('month', '')
    year     = request.GET.get('year', str(today.year))
    status   = request.GET.get('status', '')
    building = request.GET.get('building', '')
    sort     = request.GET.get('sort', 'room')

    if q:
        invoices = invoices.filter(
            Q(Contract_ID__Tenant_ID__First_Name__icontains=q) |
            Q(Contract_ID__Tenant_ID__Last_Name__icontains=q)  |
            Q(Contract_ID__Room_ID__Room_Number__icontains=q)
        )
    if month:
        invoices = invoices.filter(Billing_Date__month=month)
    if year:
        invoices = invoices.filter(Billing_Date__year=year)
    if status:
        invoices = invoices.filter(Status=status)
    if building:
        invoices = invoices.filter(Contract_ID__Room_ID__Building_No=building)

    # --- Sort ---
    if sort == 'amount_desc':
        invoices = invoices.order_by('-Grand_Total')
    elif sort == 'amount_asc':
        invoices = invoices.order_by('Grand_Total')
    elif sort == 'paid_date':
        invoices = invoices.order_by('-Paid_Date')
    else:
        invoices = invoices.order_by('Contract_ID__Room_ID__Room_Number')

    # dropdown เดือน/ปี
    months_th = [
        (1,'มกราคม'),(2,'กุมภาพันธ์'),(3,'มีนาคม'),(4,'เมษายน'),
        (5,'พฤษภาคม'),(6,'มิถุนายน'),(7,'กรกฎาคม'),(8,'สิงหาคม'),
        (9,'กันยายน'),(10,'ตุลาคม'),(11,'พฤศจิกายน'),(12,'ธันวาคม'),
    ]
    years = Invoice.objects.dates('Billing_Date', 'year', order='DESC')

    return render(request, 'apartment/invoice/list.html', {
        'invoices':   invoices,
        'q':          q,
        'month':      int(month) if month else '',
        'year':       int(year)  if year  else '',
        'status':     status,
        'building':   building,
        'sort':       sort,
        'months_th':  months_th,
        'years':      [y.year for y in years],
    })


@login_required
@role_required('ADMIN', 'MANAGER')
def invoice_create(request):
    invoice_form = InvoiceForm(request.POST or None)
    utility_form = UtilityForm(request.POST or None)

    # คำนวณ Due_Date อัตโนมัติ = วันที่ 5 ของเดือนถัดไป
    today         = datetime.date.today()
    billing_date  = today.replace(day=25)  # วันที่ 25 ของเดือนนี้
    next_month    = (today.replace(day=1) + datetime.timedelta(days=32)).replace(day=1)
    due_date      = next_month.replace(day=5)

    if request.method == 'POST':
        if invoice_form.is_valid() and utility_form.is_valid():
            # 1. ดึงข้อมูลจาก contract
            contract = invoice_form.cleaned_data['Contract_ID']

            # 2. สร้าง Invoice ก่อน (ยังไม่คำนวณ Grand_Total)
            invoice = invoice_form.save(commit=False)
            invoice.Grand_Total = 0
            invoice.save()

            # 3. สร้าง MonthlyBill (ค่าเช่าจาก contract)
            monthly_bill = MonthlyBill.objects.create(
                Invoice_ID = invoice,
                Bill_Month = invoice_form.cleaned_data['Billing_Date'],
                Amount     = contract.Rent_Price,
            )

            # 4. สร้าง Utility (คำนวณอัตโนมัติ)
            u = utility_form.save(commit=False)
            u.Invoice_ID      = invoice
            u.Room_ID         = contract.Room_ID
            u.Water_Unit_Used = u.Water_Unit_After - u.Water_Unit_Before
            u.Water_Total     = u.Water_Unit_Used * Decimal(u.Water_Cost_Unit)
            u.Elec_Total      = Decimal(u.Elec_Unit_Used) * Decimal(u.Elec_Cost_Unit)
            u.save()

            # 5. คำนวณ Grand_Total แล้ว save กลับ
            invoice.Grand_Total = monthly_bill.Amount + u.Water_Total + u.Elec_Total
            invoice.save()

            return redirect('invoice_detail', pk=invoice.Invoice_ID)

    return render(request, 'apartment/invoice/form.html', {
        'invoice_form': invoice_form,
        'utility_form': utility_form,
        'title': 'ออกใบแจ้งหนี้',
    })


@login_required
@role_required('ADMIN', 'MANAGER', 'STAFF', 'READONLY')
def invoice_detail(request, pk):
    invoice      = get_object_or_404(Invoice, pk=pk)
    monthly_bill = MonthlyBill.objects.filter(Invoice_ID=invoice).first()
    utility      = Utility.objects.filter(Invoice_ID=invoice).first()
    fines        = Fine.objects.filter(Invoice_ID=invoice)
    fine_form    = FineForm(request.POST or None)

    # เพิ่มค่าปรับ
    if request.method == 'POST' and fine_form.is_valid():
        fine            = fine_form.save(commit=False)
        fine.Invoice_ID = invoice
        fine.save()
        # อัปเดต Grand_Total
        fine_total          = fines.aggregate(total=Sum('Amount'))['total'] or 0
        invoice.Grand_Total = (monthly_bill.Amount if monthly_bill else 0) + \
                              (utility.Water_Total + utility.Elec_Total if utility else 0) + \
                              fine_total + fine.Amount
        invoice.save()
        return redirect('invoice_detail', pk=pk)

    return render(request, 'apartment/invoice/detail.html', {
        'invoice':      invoice,
        'monthly_bill': monthly_bill,
        'utility':      utility,
        'fines':        fines,
        'fine_form':    fine_form,
    })


@login_required
@role_required('ADMIN', 'MANAGER')
def invoice_pay(request, pk):
    today   = datetime.date.today()
    invoice = get_object_or_404(Invoice, pk=pk)
    form    = PaymentForm(request.POST or None, instance=invoice)

    if form.is_valid():
        invoice           = form.save(commit=False)
        invoice.Paid_Date = today

        # ถ้าจ่ายหลัง due_date → จ่ายล่าช้า, ปกติ → ชำระแล้ว
        if invoice.Due_Date and today > invoice.Due_Date:
            invoice.Status = 'จ่ายล่าช้า'
        else:
            invoice.Status = 'ชำระแล้ว'

        invoice.save()
        return redirect('invoice_detail', pk=pk)

    return render(request, 'apartment/invoice/pay.html', {
        'form':    form,
        'invoice': invoice,
        'title':   'บันทึกชำระเงิน',
    })

@login_required
@role_required('ADMIN', 'MANAGER')
def invoice_extend(request, pk):
    today    = datetime.date.today()
    invoice  = get_object_or_404(Invoice, pk=pk)
    contract = invoice.Contract_ID
    tenant   = contract.Tenant_ID

    if request.method == 'POST':
        use_deposit = request.POST.get('use_deposit')

        if use_deposit == 'deposit':
            amount = contract.Deposit
            note   = 'โปะด้วยเงินประกันห้อง'
        else:
            amount = contract.Deposit_Advance
            note   = 'โปะด้วยเงินมัดจำ'

        Fine.objects.create(
            Invoice_ID = invoice,
            Reason     = note,
            Amount     = -amount,
            Fine_Date  = today,
        )

        fine_total   = Fine.objects.filter(
            Invoice_ID=invoice
        ).aggregate(t=Sum('Amount'))['t'] or 0

        monthly_bill = MonthlyBill.objects.filter(Invoice_ID=invoice).first()
        utility      = Utility.objects.filter(Invoice_ID=invoice).first()
        invoice.Grand_Total = (
            (monthly_bill.Amount if monthly_bill else 0) +
            (utility.Water_Total + utility.Elec_Total if utility else 0) +
            fine_total
        )

        # วันครบกำหนดใหม่ = วันที่ 5 ของเดือนถัดไปจากวันนี้
        next_m                    = (today + datetime.timedelta(days=10)).replace(day=1)
        invoice.Due_Date          = next_m.replace(day=5)
        invoice.Extended_Due_Date = invoice.Due_Date  # เก็บไว้ว่าเคยต่อเวลา
        invoice.Status            = 'ต่อเวลาชำระ'
        invoice.Paid_Date         = today              # บันทึกวันที่กดปุ่ม
        invoice.save()

        return redirect('invoice_detail', pk=pk)

    return render(request, 'apartment/invoice/extend.html', {
        'invoice':  invoice,
        'contract': contract,
        'tenant':   tenant,
    })


@login_required
@role_required('ADMIN', 'MANAGER')
def invoice_send_all_email(request):
    today = datetime.date.today()

    if request.method == 'POST':
        month = int(request.POST.get('month', today.month))
        year  = int(request.POST.get('year',  today.year))

        invoices = Invoice.objects.filter(
            Billing_Date__month = month,
            Billing_Date__year  = year,
        ).select_related(
            'Contract_ID__Tenant_ID',
            'Contract_ID__Room_ID'
        )

        sent    = 0
        failed  = 0
        no_mail = 0

        for i, invoice in enumerate(invoices):
            tenant = invoice.Contract_ID.Tenant_ID

            if not tenant.Email:
                no_mail += 1
                continue

            monthly_bill = MonthlyBill.objects.filter(Invoice_ID=invoice).first()
            utility      = Utility.objects.filter(Invoice_ID=invoice).first()
            fines        = Fine.objects.filter(Invoice_ID=invoice)

            try:
                email_body = render_to_string('apartment/invoice/email_body.html', {
                    'invoice':      invoice,
                    'monthly_bill': monthly_bill,
                    'utility':      utility,
                    'fines':        fines,
                    'tenant':       tenant,
                })
                send_mail(
                    subject        = f'ใบแจ้งหนี้ห้อง {invoice.Contract_ID.Room_ID} — {invoice.Billing_Date.strftime("%B %Y")}',
                    message        = '',
                    from_email     = None,
                    recipient_list = [tenant.Email],
                    html_message   = email_body,
                    fail_silently  = False,
                )
                sent += 1

                # พัก 0.5 วิทุก 10 ฉบับ ป้องกัน Gmail rate limit
                if sent % 10 == 0:
                    import time
                    time.sleep(0.5)

            except Exception:
                failed += 1

        return render(request, 'apartment/invoice/send_all_result.html', {
            'sent':    sent,
            'failed':  failed,
            'no_mail': no_mail,
            'month':   month,
            'year':    year,
        })

    # GET: หน้าเลือกเดือน
    months_th = [
        (1,'มกราคม'),(2,'กุมภาพันธ์'),(3,'มีนาคม'),(4,'เมษายน'),
        (5,'พฤษภาคม'),(6,'มิถุนายน'),(7,'กรกฎาคม'),(8,'สิงหาคม'),
        (9,'กันยายน'),(10,'ตุลาคม'),(11,'พฤศจิกายน'),(12,'ธันวาคม'),
    ]
    return render(request, 'apartment/invoice/send_all_confirm.html', {
        'months_th': months_th,
        'month':     today.month,
        'year':      today.year,
    })

def auto_generate_invoices():
    import datetime
    today = datetime.date.today()

    # เงื่อนไข: วันที่ 25 ขึ้นไป และยังไม่ถึงสิ้นเดือน
    if today.day < 25:
        return 0

    bill_month = today.replace(day=1)
    bill_date  = today.replace(day=25)
    next_m     = (today + datetime.timedelta(days=10)).replace(day=1)
    due_date   = next_m.replace(day=5)

    contracts = Contract.objects.filter(
        Status='ใช้งาน'
    ).select_related('Room_ID', 'Tenant_ID')

    created = 0
    for contract in contracts:
        # ข้ามถ้ามี invoice เดือนนี้แล้ว
        if Invoice.objects.filter(
            Contract_ID  = contract,
            Billing_Date = bill_date
        ).exists():
            continue

        # ดึงข้อมูล utility ที่จดไว้แล้ว
        utility = Utility.objects.filter(
            Room_ID    = contract.Room_ID,
            Bill_Month = bill_month
        ).first()

        # ถ้ายังไม่ได้จดมิเตอร์ → ข้ามห้องนี้ไปก่อน
        if not utility:
            continue

        # ดึงค่าปรับของเดือนนี้ (ถ้ามี)
        # fine จะผูกกับ invoice ที่จะสร้าง ยังไม่มีตอนนี้ → fine = 0
        water_total = utility.Water_Total
        elec_total  = utility.Elec_Total
        grand_total = contract.Rent_Price + water_total + elec_total

        invoice = Invoice.objects.create(
            Contract_ID  = contract,
            Billing_Date = bill_date,
            Due_Date     = due_date,
            Grand_Total  = grand_total,
            Status       = 'รอชำระ',
        )
        MonthlyBill.objects.get_or_create(
            Invoice_ID = invoice,
            defaults={
                'Bill_Month': bill_month,
                'Amount':     contract.Rent_Price,
            }
        )
        # ผูก utility เข้ากับ invoice ที่เพิ่งสร้าง
        utility.Invoice_ID = invoice
        utility.save()

        created += 1

    return created
# ==================== MAINTENANCE ====================

@login_required
@role_required('ADMIN', 'MANAGER', 'STAFF', 'READONLY')
def maintenance_list(request):
    items = Maintenance.objects.select_related('Room_ID').all().order_by('-Report_Date')
    return render(request, 'apartment/maintenance/list.html', {'items': items})

@login_required
@role_required('ADMIN', 'MANAGER', 'STAFF')
def maintenance_create(request):
    form = MaintenanceForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('maintenance_list')
    return render(request, 'apartment/maintenance/form.html', {'form': form, 'title': 'เพิ่มรายการแจ้งซ่อม'})

@login_required
@role_required('ADMIN', 'MANAGER', 'STAFF')
def maintenance_edit(request, pk):
    item = get_object_or_404(Maintenance, pk=pk)
    form = MaintenanceForm(request.POST or None, instance=item)
    if form.is_valid():
        form.save()
        return redirect('maintenance_list')
    return render(request, 'apartment/maintenance/form.html', {'form': form, 'title': 'อัปเดตการซ่อม'})
# ==================== รายงาน ====================

@login_required
@role_required('ADMIN', 'MANAGER', 'STAFF', 'READONLY')
def invoice_print(request, pk):
    # หน้าพิมพ์ใบแจ้งหนี้ (print-friendly)
    invoice      = get_object_or_404(Invoice, pk=pk)
    monthly_bill = MonthlyBill.objects.filter(Invoice_ID=invoice).first()
    utility      = Utility.objects.filter(Invoice_ID=invoice).first()
    fines        = Fine.objects.filter(Invoice_ID=invoice)
    return render(request, 'apartment/invoice/print.html', {
        'invoice':      invoice,
        'monthly_bill': monthly_bill,
        'utility':      utility,
        'fines':        fines,
    })


@login_required
@role_required('ADMIN', 'MANAGER', 'STAFF', 'READONLY')
def monthly_summary(request):
    from django.db.models.functions import TruncMonth

    invoices = Invoice.objects.select_related(
        'Contract_ID__Tenant_ID', 'Contract_ID__Room_ID'
    ).all().order_by('-Billing_Date')

    summary = (
        Invoice.objects
        .annotate(month=TruncMonth('Billing_Date'))
        .values('month')
        .annotate(
            total=Sum('Grand_Total'),
            count=Count('Invoice_ID'),
            paid=Count('Invoice_ID', filter=Q(Status='ชำระแล้ว')),
        )
        .order_by('-month')
    )

    return render(request, 'apartment/report/summary.html', {
        'invoices': invoices,
        'summary':  summary,
    })

# ==================== BOOKING ====================

@login_required
@role_required('ADMIN', 'MANAGER', 'STAFF', 'READONLY')
def booking_list(request):
    bookings = Booking.objects.select_related('Room_ID').filter(
        Status='รอยืนยัน'
    ).order_by('-Booking_Date')
    return render(request, 'apartment/booking/list.html', {'bookings': bookings})


@login_required
@role_required('ADMIN', 'MANAGER', 'STAFF')
def booking_create(request, room_pk=None):
    initial = {}
    if room_pk:
        room = get_object_or_404(Room, pk=room_pk)
        initial['Room_ID'] = room

    form = BookingForm(request.POST or None, initial=initial)
    # กรองเฉพาะห้องว่าง
    form.fields['Room_ID'].queryset = Room.objects.filter(Status='ว่าง')

    if form.is_valid():
        booking = form.save(commit=False)
        booking.Status = 'รอยืนยัน'
        booking.save()
        # อัปเดตสถานะห้องเป็น จอง
        room             = booking.Room_ID
        room.Status_Flag = 'จอง'
        room.save()
        return redirect('booking_list')

    return render(request, 'apartment/booking/form.html', {
        'form':  form,
        'title': 'บันทึกการจองห้อง',
    })


@login_required
@role_required('ADMIN', 'MANAGER', 'STAFF')
def booking_cancel(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    if request.method == 'POST':
        # คืนสถานะห้องเป็นปกติ
        room             = booking.Room_ID
        room.Status_Flag = 'ปกติ'
        room.save()
        booking.Status = 'ยกเลิก'
        booking.save()
        return redirect('booking_list')
    return render(request, 'apartment/booking/confirm_cancel.html', {'booking': booking})


@login_required
@role_required('ADMIN', 'MANAGER')
def booking_confirm(request, pk):
    booking = get_object_or_404(Booking, pk=pk)

    if request.method == 'POST':
        contract_form = ContractForm(request.POST)
        contract_form.fields['Room_ID'].queryset = Room.objects.filter(
            Room_ID=booking.Room_ID.Room_ID
        )
        # ลบ Tenant_ID ออกจาก required เพราะเราจะสร้างเองใน code
        contract_form.fields['Tenant_ID'].required = False

        if contract_form.is_valid():
            # 1. สร้าง Tenant จากข้อมูลการจอง
            tenant = Tenant.objects.create(
                First_Name = booking.First_Name,
                Last_Name  = booking.Last_Name,
                ID_Card    = booking.ID_Card,
                Phone      = booking.Phone,
                Email      = booking.Email   or '',
                Line_ID    = booking.Line_ID or '',
                Address    = booking.Address or '',
            )
            # 2. สร้าง Contract แล้วผูก Tenant
            contract           = contract_form.save(commit=False)
            contract.Tenant_ID = tenant
            contract.save()
            # 3. อัปเดตสถานะห้อง
            room             = booking.Room_ID
            room.Status      = 'มีผู้เช่า'
            room.Status_Flag = 'ปกติ'
            room.save()
            # 4. ปิดการจอง
            booking.Status = 'ยืนยันแล้ว'
            booking.save()
            return redirect('contract_print', pk=contract.Contract_ID)
    else:
        contract_form = ContractForm(initial={
            'Room_ID':          booking.Room_ID,
            'Water_Cost_Unit':  18,
            'Elec_Cost_Unit':   8,
            'Deposit_Advance':  2000,
            'Status':           'ใช้งาน',
        })
        contract_form.fields['Room_ID'].queryset = Room.objects.filter(
            Room_ID=booking.Room_ID.Room_ID
        )
        # ซ่อน Tenant_ID ออกจากฟอร์มเลย เพราะไม่ต้องให้ user เลือก
        contract_form.fields['Tenant_ID'].required = False
        contract_form.fields['Tenant_ID'].widget   = contract_form.fields['Tenant_ID'].hidden_widget()
        # ซ่อน Status ด้วย เพราะตั้งค่าเป็น 'ใช้งาน' อัตโนมัติ
        contract_form.fields['Status'].widget = contract_form.fields['Status'].hidden_widget()

    return render(request, 'apartment/booking/confirm.html', {
        'booking':       booking,
        'contract_form': contract_form,
    })

# ==================== METER ====================

@login_required
@role_required('ADMIN', 'MANAGER', 'STAFF', 'READONLY', 'METER')
def meter_index(request):
    from .middleware import get_user_role
    if get_user_role(request.user) == 'METER':
        return redirect('meter_input')
    import datetime
    today = datetime.date.today()

    # รับเดือน/ปีที่เลือก (default = เดือนปัจจุบัน)
    month = int(request.GET.get('month', today.month))
    year  = int(request.GET.get('year',  today.year))
    bill_month = datetime.date(year, month, 1)

    # เดือนก่อนหน้า
    if month == 1:
        prev_month = datetime.date(year - 1, 12, 1)
    else:
        prev_month = datetime.date(year, month - 1, 1)

    # ดึงห้องที่มีผู้เช่าเท่านั้น จัดกลุ่มตามอาคาร/ชั้น
    rooms = Room.objects.filter(
        Status='มีผู้เช่า'
    ).order_by('Building_No', 'Floor', 'Room_Number')

    # ดึง utility เดือนก่อนหน้า → ใช้เป็น "เลขก่อนหน้า"
    prev_utilities = Utility.objects.filter(Bill_Month=prev_month)
    prev_map = {u.Room_ID_id: u for u in prev_utilities}

    # ดึง utility เดือนปัจจุบัน (ถ้าบันทึกไปแล้ว)
    curr_utilities = Utility.objects.filter(Bill_Month=bill_month)
    curr_map = {u.Room_ID_id: u for u in curr_utilities}

    # ดึง contract เพื่อรู้ค่าน้ำ/ไฟต่อหน่วย
    contracts = Contract.objects.filter(
        Status='ใช้งาน'
    ).select_related('Room_ID')
    contract_map = {c.Room_ID_id: c for c in contracts}

    # จัดกลุ่มห้องตามอาคาร→ชั้น
    from itertools import groupby
    buildings = {}
    for room in rooms:
        b = room.Building_No
        f = room.Floor
        if b not in buildings:
            buildings[b] = {}
        if f not in buildings[b]:
            buildings[b][f] = []

        latest_u  = Utility.objects.filter(Room_ID=room).order_by('-Bill_Month').first()
        curr_u    = curr_map.get(room.Room_ID)
        contract  = contract_map.get(room.Room_ID)

        buildings[b][f].append({
            'room':     room,
            'contract': contract,
            'prev_u':   latest_u,
            'curr_u':   curr_u,
            'water_prev': latest_u.Water_Unit_After if latest_u else (contract.Water_Meter_Start if contract else 0),
            'elec_prev':  (latest_u.Elec_Unit_Used + latest_u.Water_Unit_Before) if latest_u else (contract.Elec_Meter_Start if contract else 0),
        })

    # dropdown ตัวเลือก
    months_th = [
        (1,'มกราคม'),(2,'กุมภาพันธ์'),(3,'มีนาคม'),(4,'เมษายน'),
        (5,'พฤษภาคม'),(6,'มิถุนายน'),(7,'กรกฎาคม'),(8,'สิงหาคม'),
        (9,'กันยายน'),(10,'ตุลาคม'),(11,'พฤศจิกายน'),(12,'ธันวาคม'),
    ]
    years     = list(range(today.year - 2, today.year + 2))

    return render(request, 'apartment/meter/index.html', {
        'buildings':  buildings,
        'month':      month,
        'year':       year,
        'bill_month': bill_month,
        'today':      today,
        'months_th':  months_th,
        'years':      years,
    })


@login_required
@role_required('ADMIN', 'MANAGER', 'STAFF')
def meter_save(request):
    import datetime
    if request.method != 'POST':
        return redirect('meter_index')

    month      = int(request.POST.get('month'))
    year       = int(request.POST.get('year'))
    record_date = request.POST.get('record_date')
    bill_month = datetime.date(year, month, 1)

    rooms = Room.objects.filter(Status='มีผู้เช่า')
    contract_map = {
        c.Room_ID_id: c
        for c in Contract.objects.filter(Status='ใช้งาน')
    }

    saved = 0
    for room in rooms:
        water_after_key = f"water_after_{room.Room_ID}"
        elec_after_key  = f"elec_after_{room.Room_ID}"

        water_after = request.POST.get(water_after_key, '').strip()
        elec_after  = request.POST.get(elec_after_key,  '').strip()

        # ข้ามถ้าไม่ได้กรอก
        if not water_after or not elec_after:
            continue

        contract = contract_map.get(room.Room_ID)
        if not contract:
            continue

        # ดึงเลขก่อนหน้า
        if month == 1:
            prev_month = datetime.date(year - 1, 12, 1)
        else:
            prev_month = datetime.date(year, month - 1, 1)

        prev_u = Utility.objects.filter(
            Room_ID=room, Bill_Month=prev_month
        ).first()

        water_before = float(prev_u.Water_Unit_After) if prev_u else float(contract.Water_Meter_Start)
        elec_before  = float(prev_u.Elec_Unit_Used + prev_u.Water_Unit_Before) if prev_u else float(contract.Elec_Meter_Start)

        water_after_f = float(water_after)
        elec_after_f  = float(elec_after)
        water_used    = water_after_f - water_before
        if water_used < 0:
            continue
        elec_used     = elec_after_f  - elec_before

        water_total = water_used * contract.Water_Cost_Unit
        elec_total  = elec_used  * contract.Elec_Cost_Unit

        # สร้าง Invoice สำหรับเดือนนี้ก่อน (ถ้ายังไม่มี)
        invoice, created = Invoice.objects.get_or_create(
            Contract_ID  = contract,
            Billing_Date = bill_month,
            defaults={
                'Due_Date':    bill_month.replace(day=15),
                'Grand_Total': 0,
                'Status':      'รอชำระ',
            }
        )

        # บันทึก/อัปเดต Utility
        Utility.objects.update_or_create(
            Invoice_ID = invoice,
            Room_ID    = room,
            defaults={
                'Bill_Month':        bill_month,
                'Water_Unit_Before': water_before,
                'Water_Unit_After':  water_after_f,
                'Water_Unit_Used':   water_used,
                'Elec_Unit_Used':    elec_used,
                'Water_Cost_Unit':   contract.Water_Cost_Unit,
                'Elec_Cost_Unit':    contract.Elec_Cost_Unit,
                'Water_Total':       water_total,
                'Elec_Total':        elec_total,
            }
        )

        # บันทึก/อัปเดต MonthlyBill
        MonthlyBill.objects.update_or_create(
            Invoice_ID = invoice,
            defaults={
                'Bill_Month': bill_month,
                'Amount':     contract.Rent_Price,
            }
        )

        # อัปเดต Grand_Total ของ Invoice
        fine_total = Fine.objects.filter(
            Invoice_ID=invoice
        ).aggregate(t=Sum('Amount'))['t'] or 0

        invoice.Grand_Total = contract.Rent_Price + water_total + elec_total + fine_total
        invoice.save()
        saved += 1

    return redirect(f"/meter/?month={month}&year={year}&saved={saved}")

@login_required
@role_required('ADMIN', 'MANAGER', 'STAFF', 'METER')
def meter_input(request):
    import datetime
    today = datetime.date.today()
    month = today.month
    year  = today.year
    bill_month = datetime.date(year, month, 1)

    if month == 1:
        prev_month = datetime.date(year - 1, 12, 1)
    else:
        prev_month = datetime.date(year, month - 1, 1)

    rooms        = Room.objects.filter(Status='มีผู้เช่า').order_by('Building_No', 'Floor', 'Room_Number')
    contract_map = {c.Room_ID_id: c for c in Contract.objects.filter(Status='ใช้งาน')}
    prev_map     = {u.Room_ID_id: u for u in Utility.objects.filter(Bill_Month=prev_month)}
    curr_map     = {u.Room_ID_id: u for u in Utility.objects.filter(Bill_Month=bill_month)}

    # จัดกลุ่มตามอาคาร
    buildings = {}
    for room in rooms:
        b = room.Building_No
        if b not in buildings:
            buildings[b] = []
        contract = contract_map.get(room.Room_ID)
        latest_u = Utility.objects.filter(Room_ID=room).order_by('-Bill_Month').first()
        curr_u   = curr_map.get(room.Room_ID)
        buildings[b].append({
            'room':       room,
            'curr_u':     curr_u,
            'water_prev': latest_u.Water_Unit_After if latest_u else (contract.Water_Meter_Start if contract else 0),
            'elec_prev':  (latest_u.Elec_Unit_Used + latest_u.Water_Unit_Before) if latest_u else (contract.Elec_Meter_Start if contract else 0),
        })

    if request.method == 'POST':
        return redirect('meter_save_input')

    return render(request, 'apartment/meter/input.html', {
        'buildings': buildings,
        'month':     month,
        'year':      year,
        'today':     today,
    })

# ==================== ROOM ACTIONS ====================

@login_required
@role_required('ADMIN', 'MANAGER', 'STAFF')
def room_action_moveout(request, pk):
    room     = get_object_or_404(Room, pk=pk)
    contract = Contract.objects.filter(Room_ID=room, Status='ใช้งาน').first()

    # เช็ค invoice ค้างชำระ
    unpaid_count = Invoice.objects.filter(
        Contract_ID=contract, Status='รอชำระ'
    ).count() if contract else 0

    if request.method == 'POST':
        if contract:
            contract.Status = 'หมดอายุ'
            contract.save()
        room.Status      = 'ว่าง'
        room.Status_Flag = 'รอทำความสะอาด'
        room.save()
        return redirect('room_detail', pk=pk)

    return render(request, 'apartment/room/action_confirm.html', {
        'room':      room,
        'action':    'moveout',
        'title':     f'ยืนยันย้ายออก — ห้อง {room.Room_Number}',
        'message':   f'ยืนยันการย้ายออกของห้อง {room.Room_Number} ? สัญญาจะถูกปิด และห้องจะเปลี่ยนเป็น "รอทำความสะอาด"',
        'btn_color': 'danger',
        'warning':   f'ระวัง! มีใบแจ้งหนี้ค้างชำระ {unpaid_count} ใบ กรุณาตรวจสอบก่อนย้ายออก' if unpaid_count > 0 else None,
    })


@login_required
@role_required('ADMIN', 'MANAGER', 'STAFF')
def room_action_notify_out(request, pk):
    # แจ้งย้ายออก: เปลี่ยน Status_Flag เป็น แจ้งย้ายออก
    room = get_object_or_404(Room, pk=pk)

    if request.method == 'POST':
        room.Status_Flag = 'แจ้งย้ายออก'
        room.save()
        return redirect('room_detail', pk=pk)

    return render(request, 'apartment/room/action_confirm.html', {
        'room':    room,
        'action':  'notify_out',
        'title':   f'แจ้งย้ายออก — ห้อง {room.Room_Number}',
        'message': f'บันทึกว่าผู้เช่าห้อง {room.Room_Number} แจ้งความประสงค์จะย้ายออก ?',
        'btn_color': 'warning',
    })


@login_required
@role_required('ADMIN', 'MANAGER', 'STAFF')
def room_action_clean(request, pk):
    # แจ้งทำความสะอาด
    room = get_object_or_404(Room, pk=pk)

    if request.method == 'POST':
        room.Status_Flag = 'รอทำความสะอาด'
        room.save()
        return redirect('room_detail', pk=pk)

    return render(request, 'apartment/room/action_confirm.html', {
        'room':    room,
        'action':  'clean',
        'title':   f'แจ้งทำความสะอาด — ห้อง {room.Room_Number}',
        'message': f'บันทึกว่าห้อง {room.Room_Number} ต้องการทำความสะอาด ?',
        'btn_color': 'info',
    })


@login_required
@role_required('ADMIN', 'MANAGER', 'STAFF')
def room_action_done_clean(request, pk):
    # ทำความสะอาดเสร็จ → คืนสถานะปกติ
    room = get_object_or_404(Room, pk=pk)
    if request.method == 'POST':
        room.Status_Flag = 'ปกติ'
        room.save()
        return redirect('room_detail', pk=pk)
    return render(request, 'apartment/room/action_confirm.html', {
        'room':    room,
        'action':  'done_clean',
        'title':   f'ทำความสะอาดเสร็จ — ห้อง {room.Room_Number}',
        'message': f'ยืนยันว่าห้อง {room.Room_Number} ทำความสะอาดเสร็จแล้ว ?',
        'btn_color': 'success',
    })


@login_required
@role_required('ADMIN', 'MANAGER')
def invoice_send_email(request, pk):
    invoice      = get_object_or_404(Invoice, pk=pk)
    monthly_bill = MonthlyBill.objects.filter(Invoice_ID=invoice).first()
    utility      = Utility.objects.filter(Invoice_ID=invoice).first()
    fines        = Fine.objects.filter(Invoice_ID=invoice)
    tenant       = invoice.Contract_ID.Tenant_ID

    # ตรวจสอบว่ามีอีเมล์ไหม
    if not tenant.Email:
        return render(request, 'apartment/invoice/email_result.html', {
            'success': False,
            'message': f'ผู้เช่า {tenant.First_Name} {tenant.Last_Name} ไม่มีอีเมล์ในระบบ',
            'invoice': invoice,
        })

    if request.method == 'POST':
        # render HTML สำหรับส่งเป็น email body
        email_body = render_to_string('apartment/invoice/email_body.html', {
            'invoice':      invoice,
            'monthly_bill': monthly_bill,
            'utility':      utility,
            'fines':        fines,
            'tenant':       tenant,
        })

        try:
            send_mail(
                subject  = f'ใบแจ้งหนี้ห้อง {invoice.Contract_ID.Room_ID} — เดือน {invoice.Billing_Date.strftime("%B %Y")}',
                message  = '',                  # plain text (เว้นว่างเพราะใช้ html)
                from_email = None,              # ใช้ DEFAULT_FROM_EMAIL
                recipient_list = [tenant.Email],
                html_message = email_body,
                fail_silently = False,
            )
            return render(request, 'apartment/invoice/email_result.html', {
                'success': True,
                'message': f'ส่งอีเมล์ไปที่ {tenant.Email} เรียบร้อยแล้ว',
                'invoice': invoice,
            })
        except Exception as e:
            return render(request, 'apartment/invoice/email_result.html', {
                'success': False,
                'message': f'ส่งอีเมล์ไม่สำเร็จ: {str(e)}',
                'invoice': invoice,
            })

    # GET: หน้ายืนยันก่อนส่ง
    return render(request, 'apartment/invoice/email_confirm.html', {
        'invoice': invoice,
        'tenant':  tenant,
    })
