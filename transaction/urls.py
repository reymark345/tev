from django.urls import path

from . import views

urlpatterns = [
    path('list', views.list, name='transaction-list'),
    path('addtev', views.addtev, name='add-tev'),
    path('addtevdetails', views.addtevdetails, name='add-tev-details'),
    path('tevemployee', views.tevemployee, name='tev-employee'),
    
    path('payroll_load', views.payroll_load, name='payroll-load'),
    path('box_load', views.box_load, name='box-load'),
    path('box_emp_load', views.box_emp_load, name='box-emp-load'),
    path('item_edit', views.item_edit, name='item-edit'),
    # path('item_update', views.item_update, name='item-update'),

    path('out_box_a', views.out_box_a, name='out-box-a'),
    path('tev_details', views.tev_details, name='tev-details'),

    path('payroll', views.list_payroll, name='transaction-payroll'),
    path('assign_payroll', views.assign_payroll, name='assign-payroll'),
    path('save_payroll', views.save_payroll, name='save-payroll'),
    path('box_a', views.box_a, name='box-a'),
    path('preview', views.preview_box_a, name='preview-box-a'),
    
    path('employee_dv', views.employee_dv, name='employee-dv'),
    path('update_box_list', views.update_box_list, name='update-box-list'),
    path('delete_box_list', views.delete_box_list, name='delete-box-list'),
    
    path('update_status', views.update_status, name='update-status'),
    path('dv_number_lib', views.dv_number_lib, name='dv-number-lib'),
    path('add_existing_record', views.add_existing_record, name='add-existing-record'),
    path('multiple_charges_details', views.multiple_charges_details, name='multiple-charges-details'),
    path('add_multiple_charges', views.add_multiple_charges, name='add-multiple-charges'),
    path('update_multiple_charges', views.update_multiple_charges, name='update-multiple-charges'),
    path('check_charges', views.check_charges, name='check-charges'),
    path('remove_charges', views.remove_charges, name='remove-charges'),

    
    
]
