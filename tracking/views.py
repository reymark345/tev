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

    FIdNumber= request.GET.get('FIdNumber')
    FTransactionCode = request.GET.get('FTransactionCode')
    FDateTravel= request.GET.get('FDateTravel') 
    NDVNumber= request.GET.get('NDVNumber') 
    EmployeeList = request.GET.getlist('EmployeeList[]')
    FAdvancedFilter =  request.GET.get('FAdvancedFilter')




    if FAdvancedFilter:

        def dictfetchall(cursor):
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

        query = """
            SELECT tev_incoming.id, tev_incoming.code, tev_incoming.first_name, tev_incoming.middle_name,
                tev_incoming.last_name, tev_incoming.date_travel, tev_incoming.status_id,
                tev_incoming.original_amount, tev_incoming.final_amount, tev_incoming.incoming_in,
                tev_incoming.incoming_out, tev_bridge.purpose AS purposes,
                tev_outgoing.dv_no AS dv_no
            FROM tev_incoming
            INNER JOIN (
                SELECT MAX(id) AS max_id
                FROM tev_incoming
                GROUP BY code
            ) AS latest_ids
            ON tev_incoming.id = latest_ids.max_id
            LEFT JOIN tev_bridge
            ON tev_incoming.id = tev_bridge.tev_incoming_id
            LEFT JOIN tev_outgoing
            ON tev_bridge.tev_outgoing_id = tev_outgoing.id
            WHERE tev_incoming.is_upload = 0 OR tev_incoming.is_upload = 1
        """
        params = []

        if FTransactionCode:
            query += " AND tev_incoming.code = %s"
            params.append(FTransactionCode)

        if FDateTravel:
            query += " AND tev_incoming.date_travel LIKE %s"
            params.append(f'%{FDateTravel}%')

        if EmployeeList:
            placeholders = ', '.join(['%s' for _ in range(len(EmployeeList))])
            query += f" AND tev_incoming.id_no IN ({placeholders})"
            params.extend(EmployeeList)

        query += "ORDER BY tev_incoming.id DESC;"

        with connection.cursor() as cursor:
            cursor.execute(query, params)
            finance_data = dictfetchall(cursor)

      

    else:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT tev_incoming.id, tev_incoming.code, tev_incoming.first_name, tev_incoming.middle_name,
                    tev_incoming.last_name, tev_incoming.date_travel, tev_incoming.status_id,
                    tev_incoming.original_amount, tev_incoming.final_amount, tev_incoming.incoming_in,
                    tev_incoming.incoming_out, tev_bridge.purpose AS purposes,
                    tev_outgoing.dv_no AS dv_no
                FROM tev_incoming
                INNER JOIN (
                    SELECT MAX(id) AS max_id
                    FROM tev_incoming
                    GROUP BY code
                ) AS latest_ids
                ON tev_incoming.id = latest_ids.max_id
                LEFT JOIN tev_bridge
                ON tev_incoming.id = tev_bridge.tev_incoming_id
                LEFT JOIN tev_outgoing
                ON tev_bridge.tev_outgoing_id = tev_outgoing.id
                ORDER BY tev_incoming.id DESC;
            """)
            columns = [col[0] for col in cursor.description]
            finance_data = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
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
        approved_date = ''
        if row['dv_no']:
            
            finance_query = """
                SELECT ts.dv_no, ts.amt_certified, ts.amt_journal, ts.amt_budget, tc.check_amount, ts.approval_date
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
                approved_date = finance_results[0][5]
                
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
            'approved_date': approved_date,
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

    query = """
        SELECT ti.id, ti.code, ti.id_no, ti.account_no, ti.original_amount, ti.final_amount, ti.status_id, tb.purpose, ti.remarks, ti.incoming_in,
        t_o.dv_no, ch.name AS charges, cl.name AS cluster FROM tev_incoming AS ti 
        LEFT JOIN tev_bridge AS tb ON tb.tev_incoming_id = ti.id
        LEFT JOIN tev_outgoing AS t_o ON t_o.id = tb.tev_outgoing_id
        LEFT JOIN charges AS ch ON ch.id = tb.charges_id
        LEFT JOIN cluster AS cl ON cl.id = t_o.cluster
        -- LEFT JOIN trans_check AS tc ON tc.dv_no = t_o.dv_no 
        -- LEFT JOIN trans_payeename AS tp ON tp.dv_no = t_o.dv_no
        -- LEFT JOIN trans_number AS tn ON tn.trans_payee_id = tp.trans_payee_id
        -- LEFT JOIN obligate AS ob ON ob.obligate_id = tn.obligate_id
        WHERE ti.id = %s
    """

    with connection.cursor() as cursor:
        cursor.execute(query, [idd])
        results = cursor.fetchall()

    print("daks")
    print(results)


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









