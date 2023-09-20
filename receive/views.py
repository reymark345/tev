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
from datetime import date as datetime_date
from django.contrib.auth.hashers import make_password
from django.db import IntegrityError, connection
import math
from django.core.serializers import serialize
from django.forms.models import model_to_dict
import requests
from django.db.models import Q, F, Exists, OuterRef
from django.db import connections
from datetime import datetime,timedelta
from receive.filters import UserFilter
import datetime as date_time



def get_user_details(request):
    return StaffDetails.objects.filter(user_id=request.user.id).first()

def generate_code():
    trans_code = SystemConfiguration.objects.values_list(
        'transaction_code', flat=True).first()
    
    last_code = trans_code.split('-')
    sampleDate = datetime_date.today()
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
            'employee_list' : TevIncoming.objects.filter().order_by('first_name'),
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
    return JsonResponse({'data': data})
    
@login_required(login_url='login')
def checking(request):
    user_details = get_user_details(request)
    allowed_roles = ["Admin", "Incoming staff", "Validating staff"] 
    role = RoleDetails.objects.filter(id=user_details.role_id).first()
    if role.role_name in allowed_roles:
        context = {
            'employee_list' : TevIncoming.objects.filter().order_by('first_name'),
            'role_permission' : role.role_name,
        }
        return render(request, 'receive/checking.html', context)
    else:
        return render(request, 'pages/unauthorized.html')
    
    
@login_required(login_url='login')
@csrf_exempt
def search_list(request):
    
    print("dataheree")
    user_details = get_user_details(request)
    allowed_roles = ["Admin", "Incoming staff", "Validating staff"] 
    role = RoleDetails.objects.filter(id=user_details.role_id).first()
    
    return JsonResponse({'data': "success"})
    
    
    
    
def tracking_load(request):
    total = 0
    finance_database_alias = 'finance'

    query = """
        SELECT code,first_name,middle_name,last_name,date_travel,ti.status,original_amount,final_amount,incoming_in,incoming_out, tb.purpose, dv_no FROM tev_incoming AS ti 
        LEFT JOIN tev_bridge AS tb ON tb.tev_incoming_id = ti.id
        LEFT JOIN tev_outgoing AS t_o ON t_o.id = tb.tev_outgoing_id
        WHERE ti.status IN (1, 2, 4, 5 ,6, 7)
        OR (ti.status = 3 AND 
            (
                SELECT COUNT(*)
                FROM tev_incoming
                WHERE code = ti.code
            ) = 1
        );
        """
    with connection.cursor() as cursor:
        cursor.execute(query)
        results = cursor.fetchall()
        
    column_names = ['code', 'first_name','middle_name','last_name', 'date_travel','status','original_amount', 'final_amount', 'incoming_in', 'incoming_out', 'purpose','dv_no']
    finance_data = []

    for finance_row in results:
        finance_dict = dict(zip(column_names, finance_row))
        finance_data.append(finance_dict)
    
    data = []
    
    total = len(finance_data)
    _start = request.GET.get('start')
    _length = request.GET.get('length')
    if _start and _length:
        start = int(_start)
        length = int(_length)
        page = math.ceil(start / length) + 1
        per_page = length
        finance_data = finance_data[start:start + length]

    for row in finance_data:
        amt_certified = ''
        amt_journal = ''
        amt_budget = ''
        amt_check = ''
        if row['dv_no']:
            
            finance_query = """
                SELECT ts.dv_no, ts.amt_certified, ts.amt_journal, ts.amt_budget, tc.check_amount
                FROM transactions AS ts
                LEFT JOIN trans_check AS tc ON tc.dv_no = ts.dv_no WHERE ts.dv_no = %s
            """
            with connections[finance_database_alias].cursor() as cursor2:
                cursor2.execute(finance_query, (row['dv_no'],))
                finance_results = cursor2.fetchall()

            if finance_results:
                
                amt_certified = finance_results[0][1]
                amt_journal = finance_results[0][2]
                amt_budget = finance_results[0][3]
                amt_check = finance_results[0][4]
                
        first_name = row['first_name'] if row['first_name'] else ''
        middle_name = row['middle_name'] if row['middle_name'] else ''
        last_name = row['last_name'] if row['last_name'] else ''
        
        emp_fullname = f"{first_name} {middle_name} {last_name}".strip()
        
        item = {
            'code': row['code'],
            'full_name': emp_fullname,
            'date_travel': row['date_travel'],
            'status': row['status'],
            'original_amount': row['original_amount'],
            'final_amount': row['final_amount'],
            'incoming_in': row['incoming_in'],
            'incoming_out': row['incoming_out'],
            'purpose': row['purpose'],
            'dv_no': row['dv_no'],
            'amt_certified': amt_certified,
            'amt_journal': amt_journal,
            'amt_budget': amt_budget,
            'amt_check': amt_check
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

def item_load(request):
    _search = request.GET.get('search[value]')
    _start = request.GET.get('start')
    _length = request.GET.get('length')
    _order_dir = request.GET.get('order[0][dir]')
    _order_dash = '-' if _order_dir == 'desc' else ''
    _order_col_num = request.GET.get('order[0][column]')
    
    
    print("_search1111")
    print(_search)
    
    
    # query = """
    # SELECT t.*
    # FROM tev_incoming t
    # WHERE (
    #     t.status = 1
    #     OR (
    #         t.status = 3 AND t.slashed_out IS NOT NULL AND NOT EXISTS (
    #             SELECT 1
    #             FROM tev_incoming t2
    #             WHERE t2.code = t.code
    #             AND t2.status IN (1, 2)
    #         )
    #     )
    # );
    # """
    query = """
    SELECT t1.*
    FROM tev_incoming t1
    WHERE t1.status = 1
    OR (
        t1.status = 3
        AND t1.slashed_out IS NOT NULL
        AND NOT EXISTS (
            SELECT 1
            FROM tev_incoming t2
            WHERE t2.code = t1.code
            AND t2.status IN (1, 2)
        )
        AND NOT EXISTS (
            SELECT 1
            FROM tev_incoming t3
            WHERE t3.code = t1.code
            AND t3.status = 3
            AND t3.slashed_out > t1.slashed_out
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
        full_name = userData[0].first_name + ' ' + userData[0].last_name if userData else ''
        
        first_name = item['first_name'] if item['first_name'] else ''
        middle_name = item['middle_name'] if item['middle_name'] else ''
        last_name = item['last_name'] if item['last_name'] else ''
        
        emp_fullname = f"{first_name} {middle_name} {last_name}".strip()

        item_entry = {
            'id': item['id'],
            'code': item['code'],
            'name': emp_fullname,
            'id_no': item['id_no'],
            'account_no': item['account_no'],
            'date_travel': item['date_travel'],
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



def checking_load(request):
    # query = """
    #     SELECT t.*
    #     FROM tev_incoming t
    #     WHERE t.status = 2
    #         OR t.status = 7
    #         OR (t.status = 3 AND t.slashed_out IS NULL AND (
    #             SELECT COUNT(*)
    #             FROM tev_incoming
    #             WHERE code = t.code
    #         ) = 1
    #     );
    # """
    
    query = """
        SELECT t.*
        FROM tev_incoming t
        WHERE t.status = 2
            OR t.status = 7
            OR (t.status = 3 AND t.slashed_out IS NULL
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

        userData = AuthUser.objects.filter(id=row[16])
        full_name = userData[0].first_name + ' ' + userData[0].last_name
        first_name = row[2] if row[2] else ''
        middle_name = row[3] if row[3] else ''
        last_name = row[4] if row[4] else ''
        emp_fullname = f"{first_name} {middle_name} {last_name}".strip()
        

        item = {
            'id': row[0],
            'code': row[1],
            'name': emp_fullname,
            'id_no': row[5],
            'account_no': row[6],
            'date_travel': row[7],
            'original_amount': row[8],
            'final_amount': row[9],
            'incoming_in': row[10],
            'incoming_out': row[11],
            'slashed_out': row[12],
            'remarks': row[13],
            'status': row[15],
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
    name = request.POST.get('EmpName')
    middle = request.POST.get('EmpMiddle')
    lname = request.POST.get('EmpLastname')
    amount = request.POST.get('OriginalAmount')

    print(amount)
    print("whyywalayamount")
    remarks = request.POST.get('Remarks')
    tev_update = TevIncoming.objects.filter(id=id).update(first_name=name,middle_name = middle,last_name = lname,original_amount=amount,remarks=remarks)
    return JsonResponse({'data': 'success'})

@csrf_exempt
def item_returned(request):
    id = request.POST.get('ItemID')
    emp_name = request.POST.get('EmployeeName')
    amount = request.POST.get('OriginalAmount')
    remarks = request.POST.get('Remarks')
    
    travel_date = request.POST.get('HDateTravel')
    
    
    print(travel_date)
    print("travel_date")
    
    
    
    travel_date_stripped = travel_date.strip()
    travel_date_spaces = travel_date_stripped.replace(' ', '')
    
    id = request.POST.get('ItemID')
    data = TevIncoming.objects.filter(id=id).first()
    
    tev_add = TevIncoming(code=data.code,first_name=data.first_name,middle_name=data.middle_name,last_name = data.last_name,id_no = data.id_no, account_no = data.account_no, date_travel = travel_date_spaces,original_amount=data.original_amount,final_amount = data.final_amount,remarks=remarks,user_id=data.user_id)
    tev_add.save()
    return JsonResponse({'data': 'success'})



@csrf_exempt
def item_add(request):
    employeename = request.POST.get('EmployeeName')
    amount = request.POST.get('OriginalAmount')
    travel_date = request.POST.get('DateTravel')
    range_travel = request.POST.get('RangeTravel')
    idd_no = request.POST.get('IdNumber')
    acct_no = request.POST.get('AccountNumber')
    name = request.POST.get('EmpName')
    middle = request.POST.get('EmpMiddle')
    lname = request.POST.get('EmpLastname')
    remarks = request.POST.get('Remarks')
    user_id = request.session.get('user_id', 0)
    g_code = generate_code()

    if travel_date:
        travel_date = request.POST.get('DateTravel')
    else :
        start_date_str, end_date_str = range_travel.split(' to ')
        
        start_date = datetime.strptime(start_date_str.strip(), '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str.strip(), '%Y-%m-%d')
        
        formatted_dates = []

        current_date = start_date
        while current_date <= end_date:
            formatted_dates.append(current_date.strftime('%d-%m-%Y'))
            current_date += timedelta(days=1)

        formatted_dates_str = ', '.join(formatted_dates)
        travel_date = formatted_dates_str

    duplicate_travel = []
    individual_dates = travel_date.split(',')
    cleaned_dates = ','.join(date.strip() for date in individual_dates)

    for date in individual_dates:
        cleaned_date = date.strip()

        results = TevIncoming.objects.filter(
            Q(first_name=name) & Q(middle_name=middle) & Q(last_name=lname) &
            Q(date_travel__contains=cleaned_date)
        ).values('date_travel')

        if results:
            duplicate_travel.append(cleaned_date)

    if duplicate_travel:
        return JsonResponse({'data': 'error', 'message': duplicate_travel})

    else:
        tev_add = TevIncoming(
            code=g_code,
            first_name=name,
            middle_name=middle,
            last_name=lname,
            id_no=idd_no,
            account_no=acct_no,
            date_travel=cleaned_dates,
            original_amount=amount,
            remarks=remarks,
            user_id=user_id
        )
        tev_add.save()

        if tev_add.id:
            system_config = SystemConfiguration.objects.first()
            system_config.transaction_code = g_code
            system_config.save()

        return JsonResponse({'data': 'success', 'g_code': g_code})


@csrf_exempt
def tracking(request):
    context = {
		'employee_list' : TevIncoming.objects.filter().order_by('first_name'),
	}
    return render(request, 'receive/tracking.html', context)

@csrf_exempt
def out_pending_tev(request):
    out_list = request.POST.getlist('out_list[]')
    
    for item_id  in out_list:
        tev_update = TevIncoming.objects.filter(id=item_id).update(status=2,incoming_out=date_time.datetime.now())
    
    return JsonResponse({'data': 'success'})


@csrf_exempt
def add_existing_record(request):
    out_list = request.POST.getlist('out_list[]')
    
    for item_id  in out_list:
        tev_update = TevIncoming.objects.filter(id=item_id).update(status=2,incoming_out=date_time.datetime.now())
    
    return JsonResponse({'data': 'success'})




@csrf_exempt
def out_checking_tev(request):
    out_list = request.POST.getlist('out_list[]')   
    for item_id in out_list:
        tev_update = TevIncoming.objects.filter(id=item_id).first()  

        if tev_update:
            if tev_update.status == 3:
                tev_update.slashed_out = date_time.datetime.now()
            else:
                tev_update.status = 4
            tev_update.save()
        else:
            pass 

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
    
    if amount =='':
        amount = 0
  
    tev_update = TevIncoming.objects.filter(id=transaction_id).update(final_amount=amount,remarks=remarks,status=status)

    return JsonResponse({'data': 'success'})



