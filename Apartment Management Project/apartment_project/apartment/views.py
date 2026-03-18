from django.shortcuts import render, get_object_or_404, redirect
from django.db import models as django_models
from django.db.models import Sum, Count, Q
from django.contrib.auth.decorators import login_required
from decimal import Decimal
from .models import Tenant, Room, Contract, Invoice, MonthlyBill, Utility, Fine, Maintenance, Booking
from .forms  import TenantForm, RoomForm, ContractForm, InvoiceForm, UtilityForm, PaymentForm, FineForm, MaintenanceForm, BookingForm


# ==================== DASHBOARD ====================

@login_required
def dashboard(request):
    import datetime
    today = datetime.date.today()
    rooms = Room.objects.all().order_by('Building_No', 'Floor', 'Room_Number')

    # ห้องที่มี invoice เกินกำหนด → สีแดง
    overdue_room_ids = list(Invoice.objects.filter(
        Status='รอชำระ', Due_Date__lt=today
    ).values_list('Contract_ID__Room_ID', flat=True))

    # ห้องที่มี invoice รอชำระ (ยังไม่เกิน) → แสดง $
    unpaid_room_ids = list(Invoice.objects.filter(
        Status='รอชำระ'
    ).values_list('Contract_ID__Room_ID', flat=True))

    # ห้องที่มีแจ้งซ่อมค้าง → แสดง 🔧
    repair_room_ids = list(Maintenance.objects.exclude(
        Status='ซ่อมเสร็จ'
    ).values_list('Room_ID', flat=True))

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
def tenant_list(request):
    # ค้นหาผู้เช่าด้วยชื่อหรือนามสกุล
    query   = request.GET.get('q', '')
    tenants = Tenant.objects.all()
    if query:
        tenants = tenants.filter(First_Name__icontains=query) | tenants.filter(Last_Name__icontains=query)
    return render(request, 'apartment/tenant/list.html', {'tenants': tenants, 'query': query})

@login_required
def tenant_create(request):
    form = TenantForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('tenant_list')
    return render(request, 'apartment/tenant/form.html', {'form': form, 'title': 'เพิ่มผู้เช่า'})

@login_required
def tenant_edit(request, pk):
    tenant = get_object_or_404(Tenant, pk=pk)
    form   = TenantForm(request.POST or None, instance=tenant)
    if form.is_valid():
        form.save()
        return redirect('tenant_list')
    return render(request, 'apartment/tenant/form.html', {'form': form, 'title': 'แก้ไขผู้เช่า'})

@login_required
def tenant_delete(request, pk):
    tenant = get_object_or_404(Tenant, pk=pk)
    if request.method == 'POST':
        tenant.delete()
        return redirect('tenant_list')
    return render(request, 'apartment/tenant/confirm_delete.html', {'object': tenant, 'title': 'ลบผู้เช่า'})


# ==================== ROOM ====================

@login_required
def room_list(request):
    rooms = Room.objects.all().order_by('Room_Number')
    return render(request, 'apartment/room/list.html', {'rooms': rooms})

@login_required
def room_create(request):
    form = RoomForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('room_list')
    return render(request, 'apartment/room/form.html', {'form': form, 'title': 'เพิ่มห้องพัก'})

@login_required
def room_edit(request, pk):
    room = get_object_or_404(Room, pk=pk)
    form = RoomForm(request.POST or None, instance=room)
    if form.is_valid():
        form.save()
        return redirect('room_list')
    return render(request, 'apartment/room/form.html', {'form': form, 'title': 'แก้ไขห้องพัก'})

@login_required
def room_delete(request, pk):
    room = get_object_or_404(Room, pk=pk)
    if request.method == 'POST':
        room.delete()
        return redirect('room_list')
    return render(request, 'apartment/room/confirm_delete.html', {'object': room, 'title': 'ลบห้องพัก'})

@login_required
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
def contract_list(request):
    contracts = Contract.objects.select_related('Tenant_ID', 'Room_ID').all()
    return render(request, 'apartment/contract/list.html', {'contracts': contracts})

@login_required
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
def contract_print(request, pk):
    # หน้าพิมพ์สัญญา
    contract = get_object_or_404(Contract, pk=pk)
    return render(request, 'apartment/contract/print.html', {'contract': contract})

@login_required
def contract_delete(request, pk):
    contract = get_object_or_404(Contract, pk=pk)
    if request.method == 'POST':
        contract.delete()
        return redirect('contract_list')
    return render(request, 'apartment/contract/confirm_delete.html', {'object': contract, 'title': 'ลบสัญญาเช่า'})
# ==================== INVOICE ====================

@login_required
def invoice_list(request):
    # ดึง invoice ทั้งหมด พร้อม contract และ tenant
    invoices = Invoice.objects.select_related(
        'Contract_ID__Tenant_ID', 'Contract_ID__Room_ID'
    ).all().order_by('-Invoice_ID')
    return render(request, 'apartment/invoice/list.html', {'invoices': invoices})


@login_required
def invoice_create(request):
    invoice_form = InvoiceForm(request.POST or None)
    utility_form = UtilityForm(request.POST or None)

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
def invoice_pay(request, pk):
    # บันทึกการชำระเงิน
    invoice = get_object_or_404(Invoice, pk=pk)
    form    = PaymentForm(request.POST or None, instance=invoice)
    if form.is_valid():
        invoice         = form.save(commit=False)
        invoice.Status  = 'ชำระแล้ว'
        invoice.save()
        return redirect('invoice_detail', pk=pk)
    return render(request, 'apartment/invoice/pay.html', {
        'form':    form,
        'invoice': invoice,
        'title':   'บันทึกชำระเงิน',
    })

# ==================== MAINTENANCE ====================

@login_required
def maintenance_list(request):
    items = Maintenance.objects.select_related('Room_ID').all().order_by('-Report_Date')
    return render(request, 'apartment/maintenance/list.html', {'items': items})

@login_required
def maintenance_create(request):
    form = MaintenanceForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('maintenance_list')
    return render(request, 'apartment/maintenance/form.html', {'form': form, 'title': 'เพิ่มรายการแจ้งซ่อม'})

@login_required
def maintenance_edit(request, pk):
    item = get_object_or_404(Maintenance, pk=pk)
    form = MaintenanceForm(request.POST or None, instance=item)
    if form.is_valid():
        form.save()
        return redirect('maintenance_list')
    return render(request, 'apartment/maintenance/form.html', {'form': form, 'title': 'อัปเดตการซ่อม'})
# ==================== รายงาน ====================

@login_required
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
def booking_list(request):
    bookings = Booking.objects.select_related('Room_ID').filter(
        Status='รอยืนยัน'
    ).order_by('-Booking_Date')
    return render(request, 'apartment/booking/list.html', {'bookings': bookings})


@login_required
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
def booking_confirm(request, pk):
    # ดึงข้อมูลการจองมาเติมใน ContractForm อัตโนมัติ
    booking = get_object_or_404(Booking, pk=pk)

    # สร้าง Tenant จากข้อมูลการจองก่อน
    if request.method == 'POST':
        contract_form = ContractForm(request.POST)
        contract_form.fields['Room_ID'].queryset = Room.objects.filter(
            Room_ID=booking.Room_ID.Room_ID
        )
        if contract_form.is_valid():
            # 1. สร้าง Tenant
            tenant = Tenant.objects.create(
                First_Name = booking.First_Name,
                Last_Name  = booking.Last_Name,
                ID_Card    = booking.ID_Card,
                Phone      = booking.Phone,
                Email      = booking.Email      or '',
                Line_ID    = booking.Line_ID    or '',
                Address    = booking.Address    or '',
            )
            # 2. สร้าง Contract
            contract            = contract_form.save(commit=False)
            contract.Tenant_ID  = tenant
            contract.save()
            # 3. อัปเดตห้อง
            room             = booking.Room_ID
            room.Status      = 'มีผู้เช่า'
            room.Status_Flag = 'ปกติ'
            room.save()
            # 4. ปิดการจอง
            booking.Status = 'ยืนยันแล้ว'
            booking.save()
            return redirect('contract_print', pk=contract.Contract_ID)
    else:
        # pre-fill ข้อมูลจากการจอง
        import datetime
        contract_form = ContractForm(initial={
            'Room_ID':   booking.Room_ID,
            'Tenant_ID': None,
        })
        contract_form.fields['Room_ID'].queryset = Room.objects.filter(
            Room_ID=booking.Room_ID.Room_ID
        )

    return render(request, 'apartment/booking/confirm.html', {
        'booking':       booking,
        'contract_form': contract_form,
    })

# ==================== METER ====================

@login_required
def meter_index(request):
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

        prev_u    = prev_map.get(room.Room_ID)
        curr_u    = curr_map.get(room.Room_ID)
        contract  = contract_map.get(room.Room_ID)

        buildings[b][f].append({
            'room':     room,
            'contract': contract,
            'prev_u':   prev_u,
            'curr_u':   curr_u,
            # เลขก่อนหน้า: ถ้ามี utility เดือนก่อน ใช้ Water_Unit_After, ถ้าไม่มีใช้ Water_Meter_Start จาก contract
            'water_prev': prev_u.Water_Unit_After if prev_u else (contract.Water_Meter_Start if contract else 0),
            'elec_prev':  prev_u.Elec_Unit_Used + (prev_u.Water_Unit_Before if prev_u else 0) if prev_u else (contract.Elec_Meter_Start if contract else 0),
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

# ==================== ROOM ACTIONS ====================

@login_required
def room_action_moveout(request, pk):
    # ย้ายออก: ปิดสัญญา + เปลี่ยนสถานะห้อง
    room     = get_object_or_404(Room, pk=pk)
    contract = Contract.objects.filter(Room_ID=room, Status='ใช้งาน').first()

    if request.method == 'POST':
        if contract:
            contract.Status = 'หมดอายุ'
            contract.save()
        room.Status      = 'ว่าง'
        room.Status_Flag = 'รอทำความสะอาด'  # ย้ายออกแล้วรอทำความสะอาด
        room.save()
        return redirect('room_detail', pk=pk)

    return render(request, 'apartment/room/action_confirm.html', {
        'room':    room,
        'action':  'moveout',
        'title':   f'ยืนยันย้ายออก — ห้อง {room.Room_Number}',
        'message': f'ยืนยันการย้ายออกของห้อง {room.Room_Number} ? สัญญาจะถูกปิด และห้องจะเปลี่ยนเป็น "รอทำความสะอาด"',
        'btn_color': 'danger',
    })


@login_required
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