from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from main.models import (AuthUser, TevIncoming, SystemConfiguration,RoleDetails, StaffDetails, Cluster, Charges, TevOutgoing, TevBridge, Division)
import math
from django.core.serializers import serialize
from django.db import IntegrityError



def get_user_details(request):
    return StaffDetails.objects.filter(user_id=request.user.id).first()

@login_required(login_url='login')
def division(request):
    user_details = get_user_details(request)
    allowed_roles = ["Admin", "Incoming staff", "Validating staff"] 
    role = RoleDetails.objects.filter(id=user_details.role_id).first()
    if role.role_name in allowed_roles:
        context = {
            'division' : Division.objects.filter().order_by('name'),
            'cluster' : Cluster.objects.filter().order_by('name'),
            'role_permission' : role.role_name,
        }
        return render(request, 'libraries/division.html', context)
    else:
        return render(request, 'pages/unauthorized.html')

@login_required(login_url='login')
def charges(request):
    user_details = get_user_details(request)
    allowed_roles = ["Admin", "Incoming staff", "Validating staff"] 
    role = RoleDetails.objects.filter(id=user_details.role_id).first()
    if role.role_name in allowed_roles:
        context = {
            'charges' : Charges.objects.filter().order_by('name'),
            'cluster' : Cluster.objects.filter().order_by('name'),
            'role_permission' : role.role_name,
        }
        return render(request, 'libraries/charges.html', context)
    else:
        return render(request, 'pages/unauthorized.html')
    
    
@csrf_exempt
def division_add(request):
    division = request.POST.get('Division')
    acrym = request.POST.get('Acronym')
    divchief = request.POST.get('Chief')
    user_id = request.session.get('user_id', 0)
    division_add = Division(name=division,acronym = acrym, chief = divchief, created_by = user_id)
    try:
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

    if Division.objects.filter(name=division).exclude(id=id):
        return JsonResponse({'data': 'error', 'message': 'Duplicate Division'})
    else:
        Division.objects.filter(id=id).update(name=division, acronym = acrym, chief = divchief)
        return JsonResponse({'data': 'success'})
    
    
def division_edit(request):
    id = request.GET.get('id')
    items = Division.objects.get(pk=id)
    data = serialize("json", [items])
    return HttpResponse(data, content_type="application/json")
    
    
def division_load(request):
    division_data = Division.objects.select_related().order_by('-created_at').reverse()
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
