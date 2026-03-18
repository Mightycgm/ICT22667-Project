from django.shortcuts import render, get_object_or_404, redirect
from django.db import models as django_models
from django.db.models import Sum, Count, Q
from django.contrib.auth.decorators import login_required
from decimal import Decimal
from .models import Tenant, Room, Contract, Invoice, MonthlyBill, Utility, Fine, Maintenance
from .forms  import TenantForm, RoomForm, ContractForm, InvoiceForm, UtilityForm, PaymentForm, FineForm, MaintenanceForm


# ==================== DASHBOARD ====================

@login_required
def dashboard(request):
    rooms       = Room.objects.all()
    total_rooms = rooms.count()
    vacant      = rooms.filter(Status='ว่าง').count()
    occupied    = rooms.filter(Status='มีผู้เช่า').count()
    maintenance = rooms.filter(Status='ซ่อมบำรุง').count()

    # Invoice รอชำระ
    pending_invoices = Invoice.objects.filter(Status='รอชำระ').count()

    # แจ้งซ่อมที่ยังไม่เสร็จ
    pending_repairs  = Maintenance.objects.exclude(Status='ซ่อมเสร็จ').count()

    context = {
        'rooms':            rooms,
        'total_rooms':      total_rooms,
        'vacant':           vacant,
        'occupied':         occupied,
        'maintenance':      maintenance,
        'pending_invoices': pending_invoices,
        'pending_repairs':  pending_repairs,
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

