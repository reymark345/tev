from django.urls import path

from . import views

urlpatterns = [
    path('list', views.list, name='transaction-list'),
    path('addtev', views.addtev, name='add-tev'),
    path('addtevdetails', views.addtevdetails, name='add-tev-details'),
    path('tevemployee', views.tevemployee, name='tev-employee'),
    
    path('payroll_load', views.payroll_load, name='payroll-load'),
    path('payroll_list_load', views.payroll_list_load, name='payroll-list-load'),
    path('box_load', views.box_load, name='box-load'),
    path('outgoing_load', views.outgoing_load, name='outgoing-load'),
    path('budget_load', views.budget_load, name='budget-load'),
    path('journal_load', views.journal_load, name='journal-load'),
    path('approval_load', views.approval_load, name='approval-load'),
    path('box_emp_load', views.box_emp_load, name='box-emp-load'),
    path('item_edit', views.item_edit, name='item-edit'),

    path('out_box_a', views.out_box_a, name='out-box-a'),
    path('receive_otg', views.receive_otg, name='receive-otg'),
    path('forward_otg', views.forward_otg, name='forward-otg'),
    path('receive_budget', views.receive_budget, name='receive-budget'),
    path('forward_budget', views.forward_budget, name='forward-budget'),
    path('receive_journal', views.receive_journal, name='receive-journal'),
    path('forward_journal', views.forward_journal, name='forward-journal'),
    path('receive_approval', views.receive_approval, name='receive-approval'),
    path('forward_approval', views.forward_approval, name='forward-approval'),

    path('tev_details', views.tev_details, name='tev-details'),
    path('payroll', views.list_payroll, name='transaction-payroll'),
    path('assign_payroll', views.assign_payroll, name='assign-payroll'),
    path('save_payroll', views.save_payroll, name='save-payroll'),
    path('box_a', views.box_a, name='box-a'),
    path('preview', views.preview_box_a, name='preview-box-a'),
    path('preview_pending', views.rd_preview_print, name='rd-preview-print'),

    
    path('outgoing_list', views.outgoing_list, name='outgoing-list'),
    path('budget_list', views.budget_list, name='budget-list'),
    path('journal_list', views.journal_list, name='journal-list'),
    path('approval_list', views.approval_list, name='approval-list'),
    
    path('employee_dv', views.employee_dv, name='employee-dv'),
    path('employee_journal', views.employee_journal, name='employee-journal'),
    path('update_box_list', views.update_box_list, name='update-box-list'),
    path('delete_box_list', views.delete_box_list, name='delete-box-list'),
    path('update_amt', views.update_amt, name='update-amt'),
    
    path('update_status', views.update_status, name='update-status'),
    path('dv_number_lib', views.dv_number_lib, name='dv-number-lib'),
    path('add_existing_record', views.add_existing_record, name='add-existing-record'),
    path('multiple_charges_details', views.multiple_charges_details, name='multiple-charges-details'),
    path('add_multiple_charges', views.add_multiple_charges, name='add-multiple-charges'),
    path('update_multiple_charges', views.update_multiple_charges, name='update-multiple-charges'),
    path('check_charges', views.check_charges, name='check-charges'),
    path('remove_charges', views.remove_charges, name='remove-charges'),
    path('payroll_add_charges', views.payroll_add_charges, name='payroll-add-charges'),
    path('add_dv', views.add_dv, name='add-dv'),  
    path('retrieve_employee', views.retrieve_employee, name='retrieve-employee'),  
    path('add_emp_dv', views.add_emp_dv, name='add-emp-dv'),  
    path('add_emp_journal', views.add_emp_journal, name='add-emp-journal'), 
    path('update_purpose', views.update_purpose , name='update-purpose'),  
    path('transmittal_details', views.transmittal_details , name='transmittal-details'),  
    path('get_project_src', views.get_project_src , name='get-project-src'),  
    path('get_payees', views.get_payees , name='get-payees'),  
]
