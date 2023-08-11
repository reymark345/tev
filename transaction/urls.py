from django.urls import path

from . import views

urlpatterns = [
    path('list', views.list, name='transaction-list'),
    path('addtev', views.addtev, name='add-tev'),
    path('addtevdetails', views.addtevdetails, name='add-tev-details'),
    path('tevemployee', views.tevemployee, name='tev-employee'),
    path('tracking', views.tracking, name='receive-tracking'),
    
    path('payroll_load', views.payroll_load, name='payroll-load'),
    path('item_edit', views.item_edit, name='item-edit'),
    path('item_update', views.item_update, name='item-update'),
    path('item_add', views.item_add, name='item-add'),
    path('item_returned', views.item_returned, name='item-returned'),
    
    path('out_pending_tev', views.out_pending_tev, name='out-pending-tev'),
    path('tev_details', views.tev_details, name='tev-details'),

    path('payroll', views.list_payroll, name='transaction-payroll'),
    path('assign_payroll', views.assign_payroll, name='assign-payroll'),
    path('save_payroll', views.save_payroll, name='save-payroll'),
    path('box_a', views.box_a, name='box-a'),


    
    
    
]
