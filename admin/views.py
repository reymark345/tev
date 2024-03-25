# Create your views here.
from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.shortcuts import render, redirect
from django.contrib import messages
from main.models import (AuthUser, StaffDetails,RoleDetails, RolePermissions, SystemConfiguration )
import json 
from django.core.serializers import serialize
import datetime
import datetime as date_time
from django.contrib.auth.hashers import make_password
import math
from django.db.models import Max
from django.utils import timezone
from django.db import connection



def is_member_of_inventory_staff(user):
    return user.groups.filter(name='inventory_staff').exists()
 
@login_required(login_url='login')
def users(request):
    allowed_roles = ["Admin"]    
    user_id = request.session.get('user_id', 0)
    role_permissions = RolePermissions.objects.filter(user_id=user_id).values('role_id')
    role_details = RoleDetails.objects.filter(id__in=role_permissions).values('role_name')
    role_names = [entry['role_name'] for entry in role_details]
    if any(role_name in allowed_roles for role_name in role_names):
        context = {
            'users' : AuthUser.objects.filter().exclude(id=1).order_by('first_name').select_related(),
            'permissions' : role_names,
            'role_details': RoleDetails.objects.filter().order_by('role_name'),
        }
        return render(request, 'admin/users.html', context)
    else:
        return render(request, 'pages/unauthorized.html')

@login_required(login_url='login')
def form_controls(request):
    allowed_roles = ["Admin"]    
    user_id = request.session.get('user_id', 0)
    role_permissions = RolePermissions.objects.filter(user_id=user_id).values('role_id')
    role_details = RoleDetails.objects.filter(id__in=role_permissions).values('role_name')
    role_names = [entry['role_name'] for entry in role_details]
    date_actual = SystemConfiguration.objects.filter().first().date_actual
    if any(role_name in allowed_roles for role_name in role_names):
        context = {
            'users' : AuthUser.objects.filter().exclude(id=1).order_by('first_name').select_related(),
            'is_actual_date': date_actual,
            'permissions' : role_names,
            'role_details': RoleDetails.objects.filter().order_by('role_name'),
        }
        return render(request, 'admin/form_controls.html', context)
    else:
        return render(request, 'pages/unauthorized.html')

@csrf_exempt
def adduser(request):
    if request.method == 'POST':
        
        firstname = request.POST.get('firstname')
        lastname = request.POST.get('lastname')
        username_ = request.POST.get('username')
        password_ = request.POST.get('password')
        email_ = request.POST.get('username')
        roles = request.POST.get('roles')
        address_ = request.POST.get('address')
        sex_ = request.POST.get('sex')
        position_ = request.POST.get('position')
        role_id = request.POST.get('roles')
        

        if AuthUser.objects.filter(username=username_):
            return JsonResponse({'data': 'error'})
        else:
            add_authuser = AuthUser(
                password = make_password(password_),is_superuser = roles ,username= username_, first_name = firstname, last_name = lastname, email = email_, date_joined = datetime.datetime.now())
            add_authuser.save()
            
            add_user_details = StaffDetails(
                sex = sex_, address = address_, position = position_,role_id =role_id , user_id = AuthUser.objects.last().id)
            add_user_details.save()

            return JsonResponse({'data': 'success'})
        
@csrf_exempt
def updateuser(request):
    if request.method == 'POST':
      
        user_id_ = request.POST.get('user_id')
        firstname = request.POST.get('firstname')
        middle_name_ = request.POST.get('middlename')
        lastname = request.POST.get('lastname')
        username_ = request.POST.get('username')
        password_ = request.POST.get('password')
        email_ = request.POST.get('email')
        roles = request.POST.get('roles')
        birthdate = request.POST.get('birthdate')
        address_ = request.POST.get('address')
        sex_ = request.POST.get('sex')
        position_ = request.POST.get('position')
        status = request.POST.get('is_active')


        if AuthUser.objects.filter(username=username_).exclude(id=user_id_):
            return JsonResponse({'data': 'error'})
        
        else:
            AuthUser.objects.filter(id=user_id_).update(password = make_password(password_),is_superuser = roles,username=username_,first_name=firstname,last_name=lastname, email = email_, is_active = status)
            StaffDetails.objects.filter(user_id=user_id_).update(sex=sex_, address = address_, position = position_, role_id = roles)
            return JsonResponse({'data': 'success'})
        
@csrf_exempt
def date_actual_update(request):
    if request.method == 'POST':
        status = request.POST.get('status')
        SystemConfiguration.objects.filter(id =1).update(date_actual=status)
        return JsonResponse({'data': 'success'})
        

#start User function ---------------->
        

@csrf_exempt
def user_add(request):
    user_name = request.POST.get('Username')
    firstname = request.POST.get('Firstname')
    middlename = request.POST.get('Middlename')
    id_no = request.POST.get('IdNo')
    lastname = request.POST.get('Lastname')
    password = request.POST.get('Password')
    email = request.POST.get('Email')
    
    # role_id = request.POST.get('Roles')
    role_ids = request.POST.getlist('Roles')
    superuser = 0
    

    sex = request.POST.get('Sex')
    address = request.POST.get('Address')
    position = request.POST.get('Position')
    password = make_password(password)
    user_id = request.session.get('user_id', 0)

    if '1' in role_ids: 
        superuser = 1
        
    if AuthUser.objects.filter(username=user_name):
        return JsonResponse({'data': 'error', 'message': 'Username Taken'})
    
    else:
        user_add = AuthUser(password = password,is_superuser=superuser,username=user_name,first_name=firstname,last_name=lastname,email=email,date_joined=date_time.datetime.now())
        user_add.save()
        max_id = AuthUser.objects.aggregate(max_id=Max('id'))['max_id']
        user_details_add = StaffDetails(id_number = id_no,sex=sex,position=position,address=address,user_id = max_id)
        user_details_add.save()

        auth_max = AuthUser.objects.aggregate(max_id=Max('id'))['max_id']
        for role_id in role_ids:
            role_p_lib = RolePermissions(
                role_id=int(role_id), 
                user_id=auth_max
            )
            role_p_lib.save()

        return JsonResponse({'data': 'success'})

    
#End User function ---------------->


@csrf_exempt
def user_update(request):
    try:
        id = request.POST.get('ModalID')
        user_name = request.POST.get('ModalUsername')
        firstname = request.POST.get('ModalFname')
        lastname = request.POST.get('ModalLname')
        email = request.POST.get('ModalEmail')
        sex = request.POST.get('ModalSex')
        address = request.POST.get('ModalAddress')
        position = request.POST.get('ModalPosition')
        user_id = request.session.get('user_id', 0)
        status = request.POST.get('ModalStatus')
        if AuthUser.objects.filter(username=user_name).exclude(id=id):
            return JsonResponse({'data': 'error', 'message': 'Username Taken'})
        
        else:
            AuthUser.objects.filter(id=id).update(username=user_name,first_name=firstname,last_name=lastname,email=email,is_active = status)
            StaffDetails.objects.filter(user_id=id).update(sex=sex,address=address,position=position)
            return JsonResponse({'data': 'success'})
    except Exception as e:
        return JsonResponse({'data': 'error'})

@csrf_exempt
def user_edit(request):
    id = request.GET.get('id')
    items = AuthUser.objects.get(pk=id)
    userdetail = StaffDetails.objects.get(user_id=id)
    data = serialize("json", [items])
    data = json.loads(data)
    userdetail_data = serialize("json", [userdetail])
    userdetail_data = json.loads(userdetail_data)
    data[0]['fields'].update(userdetail_data[0]['fields'])
    data = json.dumps(data)
    return HttpResponse(data, content_type="application/json")


@csrf_exempt
def role_edit(request):
    try:
        id = request.GET.get('id')
        items = RolePermissions.objects.filter(user_id=id)

        response_list = []
        for item in items:
            response_list.append({
                'role_id': item.role_id,
                'user_id': item.user_id,
            })

        return JsonResponse(response_list, safe=False)
    
    except Exception as e:
        return JsonResponse({'data': 'error'})

@csrf_exempt
def role_update(request):
    id = request.POST.get('role_id')
    # role = request.POST.get('ModalRole')
    role = request.POST.getlist('modal_role[]')
    RolePermissions.objects.filter(user_id=id).delete()
    for role_id in role:
        role_p_lib = RolePermissions(
            role_id=int(role_id), 
            user_id=id
        )
        role_p_lib.save()

    return JsonResponse({'data': 'success'})
    
@csrf_exempt
def update_password(request):
    try:
        user_id= request.POST.get('PasswordID')
        password_ = request.POST.get('ModalPassword')
        AuthUser.objects.filter(id=user_id).update(password = make_password(password_))
        return JsonResponse({'data': 'success'})
    except Exception as e:
        return JsonResponse({'data': 'error'})
    


def user_load(request):    
    data = []

    user_data = """
        SELECT t1.id, t1.username, t1.first_name, t1.last_name, t2.position, t1.email, t2.sex, t2.address, GROUP_CONCAT(t4.role_name SEPARATOR ', ') AS role, t2.id AS staff_id, t1.is_active
        FROM auth_user AS t1 
        LEFT JOIN staff_details AS t2 ON t2.user_id = t1.id
        LEFT JOIN role_permissions AS t3 ON t3.user_id = t1.id
        LEFT JOIN role_details AS t4 ON t4.id = t3.role_id
        GROUP BY t1.id ORDER BY t1.date_joined DESC;
    """
    with connection.cursor() as cursor:
        cursor.execute(user_data)
        columns = [col[0] for col in cursor.description]
        user_data = [dict(zip(columns, row)) for row in cursor.fetchall()]
    total = len(user_data)
    _start = request.GET.get('start')
    _length = request.GET.get('length')
    
    if _start and _length:
        start = int(_start)
        length = int(_length)
        page = math.ceil(start / length) + 1
        per_page = length
        user_data = user_data[start:start + length]
        
    for item in user_data:
        user_data_item = {
            'user_details_id': item['staff_id'],
            'sex': item['sex'],
            'address': item['address'],
            'position': item['position'],
            'role_name': item['role'],
            'id': item['id'],
            'username': item['username'],
            'first_name': item['first_name'],
            'last_name': item['last_name'],
            'email': item['email'],
            'is_active': item['is_active'],
        }
        data.append(user_data_item)

    response = {
        'data_user': data,
        'data': data,
        'page': page,
        'per_page': per_page,
        'recordsTotal': total,
        'recordsFiltered': total,
    }
    return JsonResponse(response)
