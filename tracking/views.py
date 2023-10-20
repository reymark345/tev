from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from main.models import (AuthUser, TevIncoming, SystemConfiguration,RoleDetails, StaffDetails, TevOutgoing, TevBridge,Charges)
import json 
from django.core import serializers
from datetime import date as datetime_date
from django.contrib.auth.hashers import make_password
from django.db import IntegrityError, connection
import math
from django.core.serializers import serialize
from django.forms.models import model_to_dict
import requests
from django.db import connections
from datetime import datetime,timedelta
from receive.filters import UserFilter
import datetime as date_time
from django.db.models import Subquery, Max, F, Q, Exists, OuterRef



def get_user_details(request):
    return StaffDetails.objects.filter(user_id=request.user.id).first()

@login_required(login_url='login')
@csrf_exempt
def tracking_list(request):
    user_details = get_user_details(request)
    allowed_roles = ["Admin", "Incoming staff", "Validating staff"] 
    role = RoleDetails.objects.filter(id=user_details.role_id).first()
    if role.role_name in allowed_roles:
        context = {
            'employee_list' : TevIncoming.objects.filter().order_by('first_name'),
            'role_permission' : role.role_name,
        }
        return render(request, 'tracking/tracking_list.html', context)
    else:
        return render(request, 'pages/unauthorized.html')
    
def tracking_load(request):
    total = 0
    data = []
    finance_database_alias = 'finance'
    _search = request.GET.get('search[value]')
    _order_dir = request.GET.get('order[0][dir]')
    _order_dash = '-' if _order_dir == 'desc' else ''
    _order_col_num = request.GET.get('order[0][column]')

    latest_ids = TevIncoming.objects.values('code').annotate(max_id=Max('id')).values('max_id')
    finance_data = TevIncoming.objects.filter(id__in=Subquery(latest_ids)).values(
        'id','code', 'first_name', 'middle_name', 'last_name', 'date_travel', 'status_id',
        'original_amount', 'final_amount', 'incoming_in', 'incoming_out',
        purposes=F('tevbridge__purpose'),
        dv_no=F('tevbridge__tev_outgoing__dv_no')
    ).order_by('-id')
    
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
            'status': row['status_id'],
            'original_amount': row['original_amount'],
            'final_amount': row['final_amount'],
            'incoming_in': row['incoming_in'],
            'incoming_out': row['incoming_out'],
            'purpose': row['purposes'],
            'dv_no': row['dv_no'],
            'id': row['id'],
            'amt_certified': amt_certified,
            'amt_journal': amt_journal,
            'amt_budget': amt_budget,
            'amt_check': amt_check,
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


@login_required(login_url='login')
@csrf_exempt
def employee_details(request):
    user_details = get_user_details(request)
    allowed_roles = ["Admin", "Incoming staff", "Validating staff"] 
    dvno = ''
    fullname = ''
    total_amount = 0
    charges_list = []
    data = []  
    
    idd = request.POST.get('dv_id')
    incoming = TevIncoming.objects.filter(id=idd).first()
    inc_list = TevIncoming.objects.filter(code=incoming.code).order_by('-id')

    id_number = incoming.id_no
    if incoming:
        first_name = incoming.first_name or ""
        middle_name = incoming.middle_name or ""
        last_name = incoming.last_name or ""
        fullname = first_name + " "+ middle_name + " "+ last_name


    for row in inc_list:
        item = {
            'id': row.id,
            'code': row.code,
            'id_no': row.id_no,
            'account_no': row.account_no,
            'date_travel': row.date_travel,
            'original_amount': row.original_amount,
            'final_amount': row.final_amount,
            'incoming_in': row.incoming_in,
            'remarks': row.remarks,
            'status': row.status_id,
            'purpose': "",
        }
        data.append(item)
        
               
    total = len(data)    

          
    response = {
        'data': data,
        'full_name': fullname,
        'id_number': id_number,
        'charges': charges_list,
        'is_print': 1,
        'recordsTotal': total,
        'recordsFiltered': total,
        'total_amount':total_amount
    }
    return JsonResponse(response)

    

@login_required(login_url='login')
@csrf_exempt
def travel_history(request):
    user_details = get_user_details(request)
    allowed_roles = ["Admin", "Incoming staff", "Validating staff", "End user"] 
    role = RoleDetails.objects.filter(id=user_details.role_id).first()
    if role.role_name in allowed_roles:
        context = {
            'employee_list' : TevIncoming.objects.filter().order_by('first_name'),
            'role_permission' : role.role_name,
        }
        return render(request, 'tracking/travel_history.html', context)
    else:
        return render(request, 'pages/unauthorized.html')
    
@login_required(login_url='login')
@csrf_exempt
def travel_calendar(request):
    user_details = get_user_details(request)
    allowed_roles = ["Admin", "Incoming staff", "Validating staff", "End user"] 
    role = RoleDetails.objects.filter(id=user_details.role_id).first()
    if role.role_name in allowed_roles:
        context = {
            'employee_list' : TevIncoming.objects.filter().order_by('first_name'),
            'role_permission' : role.role_name,
        }
        return render(request, 'tracking/travel_calendar.html', context)
    else:
        return render(request, 'pages/unauthorized.html')
    

def travel_history_load(request):
    total = 0
    finance_database_alias = 'finance'
    usr_id = request.session.get('user_id', 0)
    print("why")
    print(usr_id)
    userData = StaffDetails.objects.filter(user_id=usr_id)
    id_number = userData[0].id_number
    query = """
        SELECT code,first_name,middle_name,last_name,date_travel,ti.status_id,original_amount,final_amount,incoming_in,incoming_out, tb.purpose, dv_no, ti.user_id FROM tev_incoming AS ti 
        LEFT JOIN tev_bridge AS tb ON tb.tev_incoming_id = ti.id
        LEFT JOIN tev_outgoing AS t_o ON t_o.id = tb.tev_outgoing_id
        WHERE ti.id_no = %s AND
        (ti.status_id IN (1, 2, 4, 5 ,6, 7) 
        OR (ti.status_id = 3 AND 
                (
                        SELECT COUNT(*)
                        FROM tev_incoming
                        WHERE code = ti.code
                ) = 1
        ));
        """
    with connection.cursor() as cursor:
        cursor.execute(query, [id_number])
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









