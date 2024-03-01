from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from main.models import (AuthUser, TevIncoming, SystemConfiguration,RoleDetails, StaffDetails, Cluster, Charges, TevOutgoing, TevBridge, Division, RemarksLib, RolePermissions)
import math
from django.core.serializers import serialize
from django.db import IntegrityError
import datetime as date
 
@login_required(login_url='login')
def division(request):
    allowed_roles = ["Admin", "Incoming staff", "Validating staff", "Payroll staff"] 
    user_id = request.session.get('user_id', 0)
    role_permissions = RolePermissions.objects.filter(user_id=user_id).values('role_id')
    role_details = RoleDetails.objects.filter(id__in=role_permissions).values('role_name')
    role_names = [entry['role_name'] for entry in role_details]

    if any(role_name in allowed_roles for role_name in role_names):
        context = {
            'division' : Division.objects.filter(status=0).order_by('name'),
            'cluster' : Cluster.objects.filter().order_by('name'),
            'permissions' : role_names,
        }
        return render(request, 'libraries/division.html', context)
    else:
        return render(request, 'pages/unauthorized.html')

@login_required(login_url='login')
def charges(request):
    allowed_roles = ["Admin", "Incoming staff", "Validating staff", "Payroll staff"] 
    user_id = request.session.get('user_id', 0)
    role_permissions = RolePermissions.objects.filter(user_id=user_id).values('role_id')
    role_details = RoleDetails.objects.filter(id__in=role_permissions).values('role_name')
    role_names = [entry['role_name'] for entry in role_details]
    if any(role_name in allowed_roles for role_name in role_names):
        context = {
            'charges' : Charges.objects.filter().order_by('name'),
            'cluster' : Cluster.objects.filter().order_by('name'),
            'permissions' : role_names,
        }
        return render(request, 'libraries/charges.html', context)
    else:
        return render(request, 'pages/unauthorized.html')
    
    
@login_required(login_url='login')
def remarks(request):
    allowed_roles = ["Admin", "Incoming staff", "Validating staff", "Payroll staff"] 
    user_id = request.session.get('user_id', 0)
    role_permissions = RolePermissions.objects.filter(user_id=user_id).values('role_id')
    role_details = RoleDetails.objects.filter(id__in=role_permissions).values('role_name')
    role_names = [entry['role_name'] for entry in role_details]
    
    if any(role_name in allowed_roles for role_name in role_names):
        context = {
            'charges' : RemarksLib.objects.filter().order_by('name'),
            'cluster' : Cluster.objects.filter().order_by('name'),
            'permissions' : role_names,
        }
        return render(request, 'libraries/remarks.html', context)
    else:
        return render(request, 'pages/unauthorized.html')
    
@csrf_exempt
def division_add(request):
    division = request.POST.get('Division')
    acrym = request.POST.get('Acronym')
    divchief = request.POST.get('Chief')
    ap_designation = request.POST.get('APDesignation')
    approval = request.POST.get('Approval')
    c_designation = request.POST.get('CDesignation')
    user_id = request.session.get('user_id', 0)
    
    try:
        if Division.objects.filter(name=division):
            return JsonResponse({'data': 'error', 'message': 'Division Already Taken'})
        else:
            division_add = Division(name=division,acronym = acrym, chief = divchief,c_designation=c_designation,approval= approval, ap_designation = ap_designation,created_by = user_id)
            division_add.save()
            return JsonResponse({'data': 'success'})
    except IntegrityError as e:
        return JsonResponse({'data': 'error'})
    
    
@csrf_exempt
def division_update(request):
    id = request.POST.get('ItemID')
    division = request.POST.get('Division')
    acrym = request.POST.get('Acronym')
    divchief = request.POST.get('Chief')
    c_designate = request.POST.get('CDesignation')
    approval = request.POST.get('Approval')
    ap_designation = request.POST.get('APDesignation')
    user_id = request.session.get('user_id', 0)

    if Division.objects.filter(name=division, status = 0).exclude(id=id):
        return JsonResponse({'data': 'error', 'message': 'Duplicate Division'})
    else:
        # division_add = Division(name=division,acronym = acrym, chief = divchief,c_designation=c_designate,approval= approval, ap_designation = ap_designation,created_by = user_id, status=0)
        Division.objects.filter(id=id).update(name=division,acronym = acrym, chief = divchief,c_designation=c_designate,approval= approval, ap_designation = ap_designation,created_by = user_id,updated_at =date.datetime.now())

        return JsonResponse({'data': 'success'})
    


    
    
def division_edit(request):
    id = request.GET.get('id')
    items = Division.objects.get(pk=id)
    data = serialize("json", [items])
    return HttpResponse(data, content_type="application/json")
    
    
def division_load(request):
    division_data = Division.objects.select_related().filter().order_by('-created_at').reverse()
    total = division_data.count()

    _start = request.GET.get('start')
    _length = request.GET.get('length')
    if _start and _length:
        start = int(_start)
        length = int(_length)
        page = math.ceil(start / length) + 1
        per_page = length

        division_data = division_data[start:start + length]

    data = []

    for item in division_data:
        userData = AuthUser.objects.filter(id=item.created_by)
        full_name = userData[0].first_name + ' ' + userData[0].last_name
        item = {
            'id': item.id,
            'name': item.name,
            'acronym': item.acronym,
            'chief': item.chief,
            'c_designation': item.c_designation,
            'approval': item.approval,
            'ap_designation': item.ap_designation,
            'created_by': full_name,
            'created_at': item.created_at
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



@csrf_exempt
def charges_add(request):
    charges = request.POST.get('Charges')
    user_id = request.session.get('user_id', 0)
    charges_add = Charges(name=charges, created_by = user_id)
    try:
        charges_add.save()
        return JsonResponse({'data': 'success'})
    except IntegrityError as e:
        return JsonResponse({'data': 'error'})
    
@csrf_exempt
def charges_update(request):
    id = request.POST.get('ItemID')
    charges = request.POST.get('Charges')


    if Charges.objects.filter(name=charges).exclude(id=id):
        return JsonResponse({'data': 'error', 'message': 'Duplicate Charges'})
    else:
        Charges.objects.filter(id=id).update(name=charges)
        return JsonResponse({'data': 'success'})
    
    
def charges_edit(request):
    id = request.GET.get('id')
    items = Charges.objects.get(pk=id)
    data = serialize("json", [items])
    return HttpResponse(data, content_type="application/json")
    
    
def charges_load(request):
    charges_data = Charges.objects.select_related().order_by('-created_at').reverse()
    total = charges_data.count()

    _start = request.GET.get('start')
    _length = request.GET.get('length')
    if _start and _length:
        start = int(_start)
        length = int(_length)
        page = math.ceil(start / length) + 1
        per_page = length

        charges_data = charges_data[start:start + length]

    data = []

    for item in charges_data:
        userData = AuthUser.objects.filter(id=item.created_by)
        full_name = userData[0].first_name + ' ' + userData[0].last_name

        if item.name != "Multiple":
            item = {
                'id': item.id,
                'name': item.name,
                'created_by': full_name,
                'created_at': item.created_at
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


@csrf_exempt
def remarks_add(request):
    remarks = request.POST.get('Remarks')
    user_id = request.session.get('user_id', 0)
    try:
        if RemarksLib.objects.filter(name=remarks):
            return JsonResponse({'data': 'error', 'message': 'Remarks Already Taken'})
        else:
            remarks_ = RemarksLib(name=remarks, created_by = user_id)
            remarks_.save()
            return JsonResponse({'data': 'success'})
    except IntegrityError as e:
        return JsonResponse({'data': 'error'})
    
@csrf_exempt
def remarks_update(request):
    id = request.POST.get('ItemID')
    charges = request.POST.get('Remarks')


    if RemarksLib.objects.filter(name=charges).exclude(id=id):
        return JsonResponse({'data': 'error', 'message': 'Duplicate Remarks'})
    else:
        RemarksLib.objects.filter(id=id).update(name=charges)
        return JsonResponse({'data': 'success'})
    
    
def remarks_edit(request):
    id = request.GET.get('id')
    items = RemarksLib.objects.get(pk=id)
    data = serialize("json", [items])
    return HttpResponse(data, content_type="application/json")


def remarks_load(request):
    charges_data = RemarksLib.objects.select_related().order_by('-created_at').reverse()
    total = charges_data.count()

    _start = request.GET.get('start')
    _length = request.GET.get('length')
    if _start and _length:
        start = int(_start)
        length = int(_length)
        page = math.ceil(start / length) + 1
        per_page = length

        charges_data = charges_data[start:start + length]

    data = []

    for item in charges_data:
        userData = AuthUser.objects.filter(id=item.created_by)
        full_name = userData[0].first_name + ' ' + userData[0].last_name
        item = {
            'id': item.id,
            'name': item.name,
            'created_by': full_name,
            'created_at': item.created_at
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

