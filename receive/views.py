from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from main.models import (AuthUser, TevList)
import json 
from django.core import serializers
import datetime
from django.contrib.auth.hashers import make_password
from django.db import IntegrityError
import math
from django.core.serializers import serialize


@csrf_exempt
def list(request):
    print("testtt11")
    context = {
		'employee_list' : TevList.objects.filter().order_by('employee_name'),
	}
    return render(request, 'receive/list.html', context)


def item_load(request):
    
    item_data = TevList.objects.select_related().order_by('-date_in').reverse()
    total = item_data.count()
    
    print("giloadddddnahhh")
    print(item_data)

    _start = request.GET.get('start')
    _length = request.GET.get('length')
    if _start and _length:
        start = int(_start)
        length = int(_length)
        page = math.ceil(start / length) + 1
        per_page = length
        item_data = item_data[start:start + length]

    data = []
    
    print("testtt")
    print(item_data)

    for item in item_data:
        userData = AuthUser.objects.filter(id=item.user_id)
        
        full_name = userData[0].first_name + ' ' + userData[0].last_name

        item = {
            'id': item.id,
            'employee_name': item.employee_name,
            'original_amount': item.original_amount,
            'final_amount': item.final_amount,
            'status': item.status,
            'incoming_remarks': item.incoming_remarks,
            'correctness_remarks': item.correctness_remarks,
            'date_in': item.date_in,
            'date_out': item.date_out,
            'deleted_at': item.deleted_at,
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
    items = TevList.objects.get(pk=id)
    data = serialize("json", [items])
    return HttpResponse(data, content_type="application/json")


@csrf_exempt
def item_update(request):
    list_id = request.GET.get('id')
    emp_name = request.POST.get('EmployeeName')
    amount = request.POST.get('OriginalAmount')
    remarks = request.POST.get('IncomingRemarks')
    tev_update = TevList.objects.filter(id=list_id).update(employee_name=emp_name,original_amount=amount,incoming_remarks=remarks)
    
    return JsonResponse({'data': 'success'})

    # id = request.POST.get('ItemID')
    # barcode = request.POST.get('ItemBarcode')
    # description = request.POST.get('Description')
    # classification = request.POST.get('Classification')
    # generic_id = request.POST.get('Generic')
    # sub_generic_id = request.POST.get('SubGeneric')
    # brand_id = request.POST.get('Brand')
    # type_id = request.POST.get('ItemType')

    # check_barcode = False
    # if Items.objects.filter(barcode=barcode).exclude(id=id):
    #     return JsonResponse({'data': 'error', 'message': 'Duplicate Barcode'})
    # else:
    #     check_barcode = True
    # if check_barcode:
    #     Items.objects.filter(id=id).update(barcode=barcode, description=description, classification=classification,
    # generic_id=generic_id, sub_generic_id=sub_generic_id, brand_id=brand_id, type_id=type_id)
    

    
@csrf_exempt
def item_add(request):
    employeename = request.POST.get('EmployeeName')
    amount = request.POST.get('OriginalAmount')
    remarks = request.POST.get('IncomingRemarks')
    user_id = request.session.get('user_id', 0)
    
    tev_add = TevList(employee_name=employeename,original_amount=amount,incoming_remarks=remarks,user_id=user_id)
    tev_add.save()
    
    return JsonResponse({'data': 'success'})



@csrf_exempt
def tracking(request):
    context = {
		'employee_list' : TevList.objects.filter().order_by('employee_name'),
	}
    return render(request, 'receive/tracking.html', context)



@csrf_exempt
def tevemployee(request):
    tev_id = request.POST.get('tev_id')
    qs_object = TevList.objects.filter(id=tev_id).first()
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
    
    tev_add = TevList(employee_name=employeename,original_amount=amount,incoming_remarks=remarks,user_id=user_id)
    tev_add.save()

    return JsonResponse({'data': 'success'})



@csrf_exempt
def addtevdetails(request):
    
    amount = request.POST.get('final_amount')
    remarks = request.POST.get('correctness_remarks')
    status = request.POST.get('status')
    transaction_id = request.POST.get('transaction_id')
    
    print("amountsss")
    print(amount)
    print(remarks)
    print(status)
    print(transaction_id)
    
    tev_update = TevList.objects.filter(id=transaction_id).update(final_amount=amount,correctness_remarks =remarks,status=status)

    return JsonResponse({'data': 'success'})
