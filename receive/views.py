from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from main.models import (AuthUser, TevIncoming, SystemConfiguration)
import json 
from django.core import serializers
import datetime 
from datetime import date
from django.contrib.auth.hashers import make_password
from django.db import IntegrityError
import math
from django.core.serializers import serialize
from django.forms.models import model_to_dict




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
    
    print("last_code")
    print(last_code)
    print("code")
    print(code)

    return code


@csrf_exempt
def list(request):
    context = {
		'employee_list' : TevIncoming.objects.filter().order_by('name'),
	}
    return render(request, 'receive/list.html', context)


def item_load(request):
    
    item_data = TevIncoming.objects.select_related().order_by('-incoming_in').reverse()
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

def item_edit(request):
    id = request.GET.get('id')
    items = TevIncoming.objects.get(pk=id)
    data = serialize("json", [items])
    return HttpResponse(data, content_type="application/json")


@csrf_exempt
def item_update(request):
    list_id = request.GET.get('id')
    emp_name = request.POST.get('EmployeeName')
    amount = request.POST.get('OriginalAmount')
    remarks = request.POST.get('IncomingRemarks')
    tev_update = TevIncoming.objects.filter(id=list_id).update(employee_name=emp_name,original_amount=amount,incoming_remarks=remarks)
    return JsonResponse({'data': 'success'})

    
@csrf_exempt
def item_add(request):
    employeename = request.POST.get('EmployeeName')
    amount = request.POST.get('OriginalAmount')
    remarks = request.POST.get('Remarks')
    user_id = request.session.get('user_id', 0)
    g_code = generate_code()
    tev_add = TevIncoming(code=g_code,name=employeename,original_amount=amount,remarks=remarks,user_id=user_id)
    tev_add.save()
    
    if tev_add.id:
        system_config = SystemConfiguration.objects.first()
        system_config.transaction_code = g_code
        system_config.save()
        
    return JsonResponse({'data': 'success', 'g_code': g_code})


@csrf_exempt
def tracking(request):
    context = {
		'employee_list' : TevIncoming.objects.filter().order_by('employee_name'),
	}
    return render(request, 'receive/tracking.html', context)


@csrf_exempt
def out_pending_tev(request):
    out_list = request.POST.getlist('out_list[]')
    
    for item_id  in out_list:
        tev_update = TevIncoming.objects.filter(id=item_id).update(status=1,incoming_out=datetime.datetime.now())
    
    return JsonResponse({'data': 'success'})

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
    
    print("amountsss")
    print(amount)
    print(remarks)
    print(status)
    print(transaction_id)
    
    if amount =='':
        amount = 0
  
    tev_update = TevIncoming.objects.filter(id=transaction_id).update(final_amount=amount,remarks=remarks,status=status)

    return JsonResponse({'data': 'success'})



