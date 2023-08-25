from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from main.models import (AuthUser, TevIncoming, SystemConfiguration,RoleDetails, StaffDetails, TevOutgoing, TevBridge)
import json 
from django.core import serializers
import datetime 
from datetime import date
from django.contrib.auth.hashers import make_password
from django.db import IntegrityError, connection
import math
from django.core.serializers import serialize
from django.forms.models import model_to_dict
import requests
from django.db.models import Q, F, Exists, OuterRef
from django.db import connections


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
            'employee_list' : TevIncoming.objects.filter().order_by('name'),
            'role_permission' : role.role_name,
        }
        return render(request, 'receive/list.html' , context)
    else:
        return render(request, 'pages/unauthorized.html')
    
    
    
@csrf_exempt
def api(request):
    url = "https://caraga-portal.dswd.gov.ph/api/employee/list/search/?q="
    headers = {
        "Authorization": "Token 7a8203defd27f14ca23dacd19ed898dd3ff38ef6"
    }
    response = requests.get(url, headers=headers)
    data = response.json()
    print(data)
    print("testdawa")
    return JsonResponse({'data': data})
    
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
    
    
    


def tracking_load(request):
    finance_database_alias = 'finance'
    dv_no_list = TevOutgoing.objects.order_by('id').values_list('dv_no', flat=True)

    query = """
        SELECT dv_no, amt_certified, amt_journal, amt_budget 
        FROM transactions 
        WHERE dv_no IN %s
    """
    params = [tuple(dv_no_list)]

    with connections[finance_database_alias].cursor() as cursor:
        cursor.execute(query, params)
        results = cursor.fetchall()


    dv_no_values = [result[0] for result in results]
    
    
    dv_no_to_result = {result[0]: result for result in results}
    
    
# Format the dv_no_values list
    formatted_values = []
    for dv_no in dv_no_values:
        result = dv_no_to_result.get(dv_no)
        if result:
            amt_certified = result[1]
            amt_journal = result[2]
            amt_budget = result[3]
            formatted_values.append([dv_no, amt_certified, amt_journal, amt_budget])
        else:
            formatted_values.append([dv_no])

    print("Formatted dv_no_values:")
    print(formatted_values)

    tev_outgoing_ids = TevOutgoing.objects.filter(dv_no__in=dv_no_values).order_by('id').values_list('id', flat=True)


    result_data = []
    for i, tev_outgoing_id in enumerate(tev_outgoing_ids):
        result_data.append((formatted_values[i], tev_outgoing_id))

    print("Combined data:")
    for formatted_value, tev_outgoing_id in result_data:
        print(f"Formatted: {formatted_value}, tev_outgoing_id: {tev_outgoing_id}") 
        
    
                
    
    
    tev_outgoing_ids = TevOutgoing.objects.filter(dv_no__in=dv_no_values).order_by('id').values_list('id', flat=True)
    print(tev_outgoing_ids)
    
    
    
    query = """
        SELECT t.*
        FROM tev_incoming t
        WHERE t.status IN (1, 2, 4, 5 , 7)
           OR (t.status = 3 AND (
               SELECT COUNT(*)
               FROM tev_incoming
               WHERE code = t.code
               ) = 1
           );
    """

    with connection.cursor() as cursor:
        cursor.execute(query)
        results = cursor.fetchall()

    total = len(results)

    _start = request.GET.get('start')
    _length = request.GET.get('length')

    if _start and _length:
        start = int(_start)
        length = int(_length)
        page = math.ceil(start / length) + 1
        per_page = length
        results = results[start:start + length]

    data = []
    
    for row in results:
        item = {
            'id': row[0],
            'code': row[1],
            'name': row[2],
            'id_no': row[3],
            'original_amount': row[5],
            'final_amount': row[6],
            'incoming_in': row[7],
            'incoming_out': row[8],
            'slashed_out': row[9],
            'remarks': row[10],
            'purpose': row[12],
            'status': row[13],
            'user_id': row[13],
            'date_travel': row[14]
      
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

    
# def tracking_load(request):
#     finance_database_alias = 'finance'
    
    
#     query = "SELECT dv_no,amt_certified,amt_journal, amt_budget FROM transactions"

#     with connections[finance_database_alias].cursor() as cursor:
#         cursor.execute(query)
#         results = cursor.fetchall()
        
#     print("newdatabase")
#     print(results)
    
    
    
#     # query = "SELECT dv_no,amt_certified,amt_journal, amt_budget FROM transactions WHERE dv_no = %s"
#     # params = ['23-01-0001']

#     # with connections[finance_database_alias].cursor() as cursor:
#     #     cursor.execute(query, params)
#     #     results = cursor.fetchall()
        
#     print("testdatabase")
#     print(results)

       
#     item_data = (TevIncoming.objects.filter().select_related().distinct().order_by('-id').reverse())
#     total = item_data.count()

#     _start = request.GET.get('start')
#     _length = request.GET.get('length')
#     if _start and _length:
#         start = int(_start)
#         length = int(_length)
#         page = math.ceil(start / length) + 1
#         per_page = length
#         item_data = item_data[start:start + length]

#     data = []

#     for item in item_data:
#         userData = AuthUser.objects.filter(id=item.user_id)
#         full_name = userData[0].first_name + ' ' + userData[0].last_name

#         item = {
#             'id': item.id,
#             'code': item.code,
#             'name': item.name,
#             'id_no': item.id_no,
#             'original_amount': item.original_amount,
#             'final_amount': item.final_amount,
#             'incoming_in': item.incoming_in,
#             'incoming_out': item.incoming_out,
#             'slashed_out': item.incoming_out,
#             'remarks': item.remarks,
#             'purpose': item.purpose,
#             'status': item.status,
#             'user_id': full_name
#         }

#         data.append(item)

#     response = {
#         'data': data,
#         'page': page,
#         'per_page': per_page,
#         'recordsTotal': total,
#         'recordsFiltered': total,
#     }
#     return JsonResponse(response)


def item_load(request):
    idn = request.GET.get('identifier')
    if idn == "1":
        retrieve = [1, 3]
    elif idn == "2":
        retrieve = [2, 3, 4]
    else:
        retrieve = [1, 2, 3, 4]
    
    query = """
    SELECT t.*
    FROM tev_incoming t
    WHERE (
        t.status = 1
        OR (
            t.status = 3 AND t.slashed_out IS NOT NULL AND NOT EXISTS (
                SELECT 1
                FROM tev_incoming t2
                WHERE t2.code = t.code
                AND t2.status IN (1, 2)
            )
        )
    );
    """

    with connection.cursor() as cursor:
        cursor.execute(query)
        columns = [col[0] for col in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]

    total = len(results)

    _start = request.GET.get('start')
    _length = request.GET.get('length')
    if _start and _length:
        start = int(_start)
        length = int(_length)
        page = math.ceil(start / length) + 1
        per_page = length
        results = results[start:start + length]

    data = []

    for item in results:
        userData = AuthUser.objects.filter(id=item['user_id'])
        full_name = userData[0].first_name + ' ' + userData[0].last_name

        item_entry = {
            'id': item['id'],
            'code': item['code'],
            'name': item['name'],
            'id_no': item['id_no'],
            'original_amount': item['original_amount'],
            'final_amount': item['final_amount'],
            'incoming_in': item['incoming_in'],
            'incoming_out': item['incoming_out'],
            'slashed_out': item['slashed_out'],
            'remarks': item['remarks'],
            'status': item['status'],
            'user_id': full_name
        }

        data.append(item_entry)

    response = {
        'data': data,
        'page': page,
        'per_page': per_page,
        'recordsTotal': total,
        'recordsFiltered': total,
    }
    return JsonResponse(response)


from django.db import connection
from django.http import JsonResponse
import math

def checking_load(request):
    query = """
        SELECT t.*
        FROM tev_incoming t
        WHERE t.status = 2
            OR t.status = 7
            OR (t.status = 3 AND t.slashed_out IS NULL AND (
                SELECT COUNT(*)
                FROM tev_incoming
                WHERE code = t.code
            ) = 1
        );
    """

    with connection.cursor() as cursor:
        cursor.execute(query)
        results = cursor.fetchall()

    total = len(results)

    _start = request.GET.get('start')
    _length = request.GET.get('length')

    if _start and _length:
        start = int(_start)
        length = int(_length)
        page = math.ceil(start / length) + 1
        per_page = length
        results = results[start:start + length]

    data = []

    for row in results:

        userData = AuthUser.objects.filter(id=row[14])
        full_name = userData[0].first_name + ' ' + userData[0].last_name

        item = {
            'id': row[0],
            'code': row[1],
            'name': row[2],
            'id_no': row[3],
            'original_amount': row[6],
            'final_amount': row[7],
            'incoming_in': row[8],
            'incoming_out': row[9],
            'slashed_out': row[10],
            'remarks': row[11],
            'status': row[13],
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



# def checking_load(request):
    
#     idn = request.GET.get('identifier')
#     retrieve =[2,3,4]

       
#     item_data = (TevIncoming.objects.filter(status__in=retrieve).select_related().distinct().order_by('-id').reverse())
#     total = item_data.count()

#     _start = request.GET.get('start')
#     _length = request.GET.get('length')
#     if _start and _length:
#         start = int(_start)
#         length = int(_length)
#         page = math.ceil(start / length) + 1
#         per_page = length
#         item_data = item_data[start:start + length]

#     data = []

#     for item in item_data:
#         userData = AuthUser.objects.filter(id=item.user_id)
#         full_name = userData[0].first_name + ' ' + userData[0].last_name

#         item = {
#             'id': item.id,
#             'code': item.code,
#             'name': item.name,
#             'id_no': item.id_no,
#             'original_amount': item.original_amount,
#             'final_amount': item.final_amount,
#             'incoming_in': item.incoming_in,
#             'incoming_out': item.incoming_out,
#             'slashed_out': item.incoming_out,
#             'remarks': item.remarks,
#             'status': item.status,
#             'user_id': full_name
#         }

#         data.append(item)

#     response = {
#         'data': data,
#         'page': page,
#         'per_page': per_page,
#         'recordsTotal': total,
#         'recordsFiltered': total,
#     }
#     return JsonResponse(response)

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
def item_add(request):
    employeename = request.POST.get('EmployeeName')
    amount = request.POST.get('OriginalAmount')
    travel_date = request.POST.get('DateTravel')
    remarks = request.POST.get('Remarks')
    user_id = request.session.get('user_id', 0)
    g_code = generate_code()
    tev_add = TevIncoming(code=g_code,name=employeename,original_amount=amount,remarks=remarks,date_travel = travel_date,user_id=user_id)
    tev_add.save()
    
    if tev_add.id:
        system_config = SystemConfiguration.objects.first()
        system_config.transaction_code = g_code
        system_config.save()
        
    return JsonResponse({'data': 'success', 'g_code': g_code})


@csrf_exempt
def tracking(request):
    context = {
		'employee_list' : TevIncoming.objects.filter().order_by('name'),
	}
    return render(request, 'receive/tracking.html', context)



@csrf_exempt
def out_pending_tev(request):
    out_list = request.POST.getlist('out_list[]')
    
    for item_id  in out_list:
        tev_update = TevIncoming.objects.filter(id=item_id).update(status=2,incoming_out=datetime.datetime.now())
    
    return JsonResponse({'data': 'success'})

@csrf_exempt
def out_checking_tev(request):
    out_list = request.POST.getlist('out_list[]')   
    for item_id in out_list:
        tev_update = TevIncoming.objects.filter(id=item_id).first()  

        if tev_update:
            if tev_update.status == 3:
                tev_update.slashed_out = datetime.datetime.now()
            else:
                tev_update.status = 4
            tev_update.save()
        else:
            pass 

    return JsonResponse({'data': 'success'})
# tev_update = TevIncoming.objects.filter(id=item_id).update(status=4,slashed_out=datetime.datetime.now())

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



