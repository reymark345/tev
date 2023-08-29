from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from main.models import (AuthUser, TevIncoming, SystemConfiguration,RoleDetails, StaffDetails, Cluster, Charges, TevOutgoing, TevBridge, Division)
import json 
from django.core import serializers
import datetime 
from datetime import date
from django.contrib.auth.hashers import make_password
from django.db import IntegrityError
import math
from django.core.serializers import serialize
from django.forms.models import model_to_dict
from urllib.parse import parse_qs



def get_user_details(request):
    return StaffDetails.objects.filter(user_id=request.user.id).first()

def generate_code():
    trans_code = SystemConfiguration.objects.values_list(
        'transaction_code', flat=True).first()
    
    last_code = trans_code.split('-')
    sampleDate = date.today()
    year = sampleDate.strftime("%y")
    month = sampleDate.strftime("%m")
    series = 1

    if last_code[1] == month:
        series = int(last_code[2]) + 1

    code = year + '-' + month + '-' + f'{series:05d}'

    return code

@login_required(login_url='login')
def list(request):
    user_details = get_user_details(request)
    allowed_roles = ["Admin", "Incoming staff", "Validating staff"] 
    role = RoleDetails.objects.filter(id=user_details.role_id).first()
    if role.role_name in allowed_roles:
        context = {
            'role_permission' : role.role_name,
            'cluster' : Cluster.objects.filter().order_by('name'),
            'division' : Division.objects.filter().order_by('name'),
        }
        return render(request, 'receive/list.html', context)
    else:
        return render(request, 'pages/unauthorized.html')
    
    
@login_required(login_url='login')
def list_payroll(request):
    user_details = get_user_details(request)
    allowed_roles = ["Admin", "Incoming staff", "Validating staff"] 
    role = RoleDetails.objects.filter(id=user_details.role_id).first()
    if role.role_name in allowed_roles:
        context = {
            'charges' : Charges.objects.filter().order_by('name'),
            'cluster' : Cluster.objects.filter().order_by('name'),
            'division' : Division.objects.filter().order_by('name'),
            'role_permission' : role.role_name,
        }
        return render(request, 'transaction/list.html', context)
    else:
        return render(request, 'pages/unauthorized.html')
    

@login_required(login_url='login')
@csrf_exempt
def assign_payroll(request):
    user_details = get_user_details(request)
    allowed_roles = ["Admin", "Incoming staff", "Validating staff"] 
    role = RoleDetails.objects.filter(id=user_details.role_id).first()
    if role.role_name in allowed_roles:
        user_details = get_user_details(request)
        allowed_roles = ["Admin", "Payroll staff"] 
        context = {
            'role_permission' : role.role_name,
        }
        return render(request, 'transaction/list.html', context)
    else:
        return render(request, 'pages/unauthorized.html')    
    
    
@login_required(login_url='login')
@csrf_exempt
def save_payroll(request):
    user_details = get_user_details(request)
    allowed_roles = ["Admin", "Incoming staff", "Validating staff"] 
    role = RoleDetails.objects.filter(id=user_details.role_id).first()
    if role.role_name in allowed_roles:
        user_details = get_user_details(request)
        allowed_roles = ["Admin", "Payroll staff"] 
        user_id = request.session.get('user_id', 0)
        formdata = request.POST.get('form_data')
        formdata_dict = parse_qs(formdata)
        cluster_name = formdata_dict.get('Cluster', [None])[0]
        dv_number = formdata_dict.get('DvNumber', [None])[0]
        div_id = formdata_dict.get('Division', [None])[0]
        selected_tev = json.loads(request.POST.get('selected_item'))
        outgoing = TevOutgoing(dv_no=dv_number,cluster=cluster_name,box_b_in=datetime.datetime.now(),user_id=user_id, division_id = div_id)
        outgoing.save()
        latest_outgoing = TevOutgoing.objects.latest('id')
        for item in selected_tev:
            tev_update = TevIncoming.objects.filter(id=item['id']).update(status=5)
            obj, was_created_bool = TevBridge.objects.get_or_create(
                tev_incoming_id=item['id'],
                tev_outgoing_id=latest_outgoing.id,
                purpose=item['purpose'],
                charges_id=item['charges']
            )
                
        return JsonResponse({'data': 'success'})
    else:
        return render(request, 'pages/unauthorized.html')    
    
    
@login_required(login_url='login')
def box_a(request):
    user_details = get_user_details(request)

    allowed_roles = ["Admin", "Incoming staff", "Validating staff"] 
    role = RoleDetails.objects.filter(id=user_details.role_id).first()
    if role.role_name in allowed_roles:
        context = {
            'employee_list' : TevIncoming.objects.filter().order_by('name'),
            'role_permission' : role.role_name,
        }
        return render(request, 'transaction/box_a.html', context)
    else:
        return render(request, 'pages/unauthorized.html')
    
    


@login_required(login_url='login')
def preview_box_a(request):
    outgoing_id = request.GET.get('id')
    
    if outgoing_id:
        tev_incoming_ids = TevBridge.objects.filter(tev_outgoing_id=outgoing_id).values_list('tev_incoming_id', flat=True)
        selected_tev_incoming_data = TevIncoming.objects.filter(id__in=tev_incoming_ids)
        
        return render(request, 'transaction/print_box_a.html', {'selected_tev_incoming_data': selected_tev_incoming_data})
    else:
        return render(request, 'error_template.html', {'error_message': "Missing or invalid 'id' parameter"})
    


# @login_required(login_url='login')
# @csrf_exempt
# def preview_box_a(request):
#     outgoing_id = request.POST.get('box_id')
#     tev_incoming_ids = TevBridge.objects.filter(tev_outgoing_id=outgoing_id).values_list('tev_incoming_id', flat=True)
#     selected_tev_incoming_data = TevIncoming.objects.filter(id__in=tev_incoming_ids)
    
#     serialized_data = serializers.serialize('json', selected_tev_incoming_data)
#     parsed_data = json.loads(serialized_data)
    
#     return JsonResponse({'incoming_data': parsed_data})
    




    
@login_required(login_url='login')
def checking(request):
    user_details = get_user_details(request)
    allowed_roles = ["Admin", "Incoming staff", "Validating staff"] 
    
    role = RoleDetails.objects.filter(id=user_details.role_id).first()
    if role.role_name in allowed_roles:
        context = {
            'employee_list' : TevIncoming.objects.filter().order_by('name'),
            'role_permission' : role.role_name,
        }
        return render(request, 'receive/checking.html', context)
    else:
        return render(request, 'pages/unauthorized.html')


def payroll_load(request):       
    item_data = (TevIncoming.objects.filter(status=4).select_related().distinct().order_by('-id').reverse())
    total = item_data.count()

    _start = request.GET.get('start')
    _length = request.GET.get('length')
    if _start and _length:
        start = int(_start)
        length = int(_length)
        page = math.ceil(start / length) + 1
        per_page = length
        item_data = item_data[start:start + length]

    data = []

    for item in item_data: 
        userData = AuthUser.objects.filter(id=item.user_id)
        
        full_name = userData[0].first_name + ' ' + userData[0].last_name

        item = {
            'id': item.id,
            'code': item.code,
            'name': item.name,
            'id_no': item.id_no,
            'original_amount': item.original_amount,
            'final_amount': item.final_amount,
            'incoming_in': item.incoming_in,
            'incoming_out': item.incoming_out,
            'slashed_out': item.incoming_out,
            'remarks': item.remarks,
            'status': item.status,
            'user_id': full_name
        }

        data.append(item)

    response = {
        'data': data,
        'page': page,
        'per_page': per_page,
        'recordsTotal': total,
        'recordsFiltered': total,
    }
    return JsonResponse(response)



def box_load(request):       
    item_data = (TevOutgoing.objects.filter().select_related().distinct().order_by('-id').reverse())
    total = item_data.count()

    _start = request.GET.get('start')
    _length = request.GET.get('length')
    if _start and _length:
        start = int(_start)
        length = int(_length)
        page = math.ceil(start / length) + 1
        per_page = length
        item_data = item_data[start:start + length]

    data = []

    for item in item_data: 
        userData = AuthUser.objects.filter(id=item.user_id)
        
        full_name = userData[0].first_name + ' ' + userData[0].last_name

        item = {
            'id': item.id,
            'dv_no': item.dv_no,
            'cluster': item.cluster,
            'division_name': item.division.name,
            'division_chief': item.division.chief,
            'status':item.status,
            'box_b_in': item.box_b_in,
            'box_b_out': item.box_b_out,
            'user_id': full_name
        }

        data.append(item)

    response = {
        'data': data,
        'page': page,
        'per_page': per_page,
        'recordsTotal': total,
        'recordsFiltered': total,
    }
    return JsonResponse(response)


def item_edit(request):
    id = request.GET.get('id')
    items = TevIncoming.objects.get(pk=id)
    data = serialize("json", [items])
    return HttpResponse(data, content_type="application/json")


@csrf_exempt
def item_update(request):
    id = request.POST.get('ItemID')
    emp_name = request.POST.get('EmployeeName')
    amount = request.POST.get('OriginalAmount')
    remarks = request.POST.get('Remarks')
    tev_update = TevIncoming.objects.filter(id=id).update(name=emp_name,original_amount=amount,remarks=remarks)
    return JsonResponse({'data': 'success'})

@csrf_exempt
def item_returned(request):
    id = request.POST.get('ItemID')
    emp_name = request.POST.get('EmployeeName')
    amount = request.POST.get('OriginalAmount')
    remarks = request.POST.get('Remarks')
    
    id = request.POST.get('ItemID')
    data = TevIncoming.objects.filter(id=id).first()

    
    tev_add = TevIncoming(code=data.code,name=data.name,original_amount=amount,remarks=remarks,user_id=data.user_id)
    tev_add.save()
    
    
    #tev_update = TevIncoming.objects.filter(id=id).update(name=emp_name,original_amount=amount,remarks=remarks)
    return JsonResponse({'data': 'success'})



@csrf_exempt
def out_box_a(request):
    out_list = request.POST.getlist('out_list[]')
    
    # Convert the out_list items to integers
    out_list_int = [int(item) for item in out_list]

    
    # Update the tev_incoming table
    ids = TevBridge.objects.filter(tev_outgoing_id__in=out_list_int).values_list('tev_incoming_id', flat=True)
    
    TevIncoming.objects.filter(id__in=ids).update(status=6)
    
    for item_id  in out_list:
        box_b = TevOutgoing.objects.filter(id=item_id).update(status=6,box_b_out=datetime.datetime.now())

    
    return JsonResponse({'data': 'success'})



# @csrf_exempt
# def out_box_a(request):
#     out_list = request.POST.getlist('out_list[]')
    
#     for item_id  in out_list:
#         box_b = TevOutgoing.objects.filter(id=item_id).update(box_b_out=datetime.datetime.now())
    
#     return JsonResponse({'data': 'success'})


@csrf_exempt
def tev_details(request):
    tev_id = request.POST.get('tev_id')
    tev = TevIncoming.objects.filter(id=tev_id).first()
    data = {
        'data': model_to_dict(tev)
    }
    return JsonResponse(data)


@csrf_exempt
def tevemployee(request):
    tev_id = request.POST.get('tev_id')
    qs_object = TevIncoming.objects.filter(id=tev_id).first()
    if qs_object:
        data = serializers.serialize('json', [qs_object])
        return JsonResponse({'data': data})
    else:
        return JsonResponse({'data': None})

@csrf_exempt
def addtev(request):
    
    employeename = request.POST.get('employeename')
    amount = request.POST.get('amount')
    remarks = request.POST.get('remarks')
    user_id = request.session.get('user_id', 0)
    
    tev_add = TevIncoming(employee_name=employeename,original_amount=amount,incoming_remarks=remarks,user_id=user_id)
    tev_add.save()

    return JsonResponse({'data': 'success'})



@csrf_exempt
def addtevdetails(request):
    
    amount = request.POST.get('final_amount')
    remarks = request.POST.get('remarks')
    status = request.POST.get('status')
    transaction_id = request.POST.get('transaction_id')
    
    if amount =='':
        amount = 0
  
    tev_update = TevIncoming.objects.filter(id=transaction_id).update(final_amount=amount,remarks=remarks,status=status)

    return JsonResponse({'data': 'success'})



