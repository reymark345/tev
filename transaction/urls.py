from django.urls import path

from . import views

urlpatterns = [
    path('list', views.list, name='transaction-list'),
    path('addtev', views.addtev, name='add-tev'),
    path('addtevdetails', views.addtevdetails, name='add-tev-details'),
    path('tevemployee', views.tevemployee, name='tev-employee'),
    
    path('payroll_load', views.payroll_load, name='payroll-load'),
    path('box_load', views.box_load, name='box-load'),
    path('item_edit', views.item_edit, name='item-edit'),
    path('item_update', views.item_update, name='item-update'),

    path('out_box_a', views.out_box_a, name='out-box-a'),
    path('tev_details', views.tev_details, name='tev-details'),

    path('payroll', views.list_payroll, name='transaction-payroll'),
    path('assign_payroll', views.assign_payroll, name='assign-payroll'),
    path('save_payroll', views.save_payroll, name='save-payroll'),
    path('box_a', views.box_a, name='box-a'),
    path('preview', views.preview_box_a, name='preview-box-a'),


    
    
    
]
