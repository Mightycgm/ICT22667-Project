from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Tenant
    path('tenants/',                views.tenant_list,   name='tenant_list'),
    path('tenants/add/',            views.tenant_create, name='tenant_create'),
    path('tenants/<int:pk>/edit/',  views.tenant_edit,   name='tenant_edit'),
    path('tenants/<int:pk>/delete/',views.tenant_delete, name='tenant_delete'),

    # Room
    path('rooms/',                  views.room_list,   name='room_list'),
    path('rooms/add/',              views.room_create, name='room_create'),
    path('rooms/<int:pk>/edit/',    views.room_edit,   name='room_edit'),
    path('rooms/<int:pk>/delete/',  views.room_delete, name='room_delete'),
    path('rooms/<int:pk>/detail/', views.room_detail, name='room_detail'),

    # Contract
    path('contracts/',                  views.contract_list,   name='contract_list'),
    path('contracts/add/',              views.contract_create, name='contract_create'),
    path('contracts/<int:pk>/edit/',    views.contract_edit,   name='contract_edit'),
    path('contracts/<int:pk>/delete/',  views.contract_delete, name='contract_delete'),
    path('contracts/<int:pk>/print/',   views.contract_print,  name='contract_print'),

    # Invoice
    path('invoices/',                   views.invoice_list,   name='invoice_list'),
    path('invoices/add/',               views.invoice_create, name='invoice_create'),
    path('invoices/<int:pk>/',          views.invoice_detail, name='invoice_detail'),
    path('invoices/<int:pk>/pay/',      views.invoice_pay,    name='invoice_pay'),
    path('invoices/<int:pk>/send-email/', views.invoice_send_email, name='invoice_send_email'),

    # Maintenance
    path('maintenance/',                views.maintenance_list,   name='maintenance_list'),
    path('maintenance/add/',            views.maintenance_create, name='maintenance_create'),
    path('maintenance/<int:pk>/edit/',  views.maintenance_edit,   name='maintenance_edit'),

    # Print + Report
    path('invoices/<int:pk>/print/',  views.invoice_print,    name='invoice_print'),
    path('report/summary/',           views.monthly_summary,  name='monthly_summary'),

    # Booking
    path('bookings/',                       views.booking_list,    name='booking_list'),
    path('bookings/add/',                   views.booking_create,  name='booking_create'),
    path('bookings/add/<int:room_pk>/',     views.booking_create,  name='booking_create_room'),
    path('bookings/<int:pk>/cancel/',       views.booking_cancel,  name='booking_cancel'),
    path('bookings/<int:pk>/confirm/',      views.booking_confirm, name='booking_confirm'),

    # Meter
    path('meter/',       views.meter_index, name='meter_index'),
    path('meter/save/',  views.meter_save,  name='meter_save'),
    path('meter/input/', views.meter_input, name='meter_input'),

    # Room Actions
    path('rooms/<int:pk>/moveout/',     views.room_action_moveout,     name='room_moveout'),
    path('rooms/<int:pk>/notify-out/',  views.room_action_notify_out,  name='room_notify_out'),
    path('rooms/<int:pk>/clean/',       views.room_action_clean,       name='room_clean'),
    path('rooms/<int:pk>/done-clean/',  views.room_action_done_clean,  name='room_done_clean'),
]