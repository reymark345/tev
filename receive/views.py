from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from main.models import (AuthUser, TevIncoming, SystemConfiguration,RoleDetails, StaffDetails, TevOutgoing, TevBridge, RemarksLib, Remarks_r, RolePermissions, Division, Section, TransactionLogs )
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
from openpyxl import load_workbook
from tablib import Dataset
import ast
from django.db.models import F, CharField, Value
from django.db.models.functions import Concat
from django.utils import timezone
from django.template.defaultfilters import date
from decimal import Decimal
from suds.client import Client
from django.db import transaction


def generate_code():
    trans_code = SystemConfiguration.objects.values_list(
        'transaction_code', flat=True
    ).first()

    last_code = trans_code.split('-')
    sample_date = datetime_date.today()
    year = sample_date.strftime("%y")
    month = sample_date.strftime("%m")
    day = sample_date.strftime("%d")
    if last_code[0] == year:
        series = int(last_code[2]) + 1
    else:
        series = 1
    code = year + '-' + month + '-' + f'{series:05d}'
    return code



@login_required(login_url='login')
def list(request):
    allowed_roles = ["Admin", "Incoming staff", "Validating staff"] 
    user_id = request.session.get('user_id', 0)
    role_permissions = RolePermissions.objects.filter(user_id=user_id).values('role_id')
    role_details = RoleDetails.objects.filter(id__in=role_permissions).values('role_name')
    role_names = [entry['role_name'] for entry in role_details]
    data = []
    user_name = RolePermissions.objects.filter(role_id=2) 
    get_id = user_name.values_list('user_id', flat=True)
    date_actual = SystemConfiguration.objects.filter().first().date_actual
    for user_id in get_id:
        userData = AuthUser.objects.filter(id=user_id)
        full_name = userData[0].first_name + ' ' + userData[0].last_name if userData else ''
        item_entry = {
            'id': userData[0].id,
            'full_name': full_name
        }
        data.append(item_entry)
    if any(role_name in allowed_roles for role_name in role_names):
        context = {
            'employee_list' : TevIncoming.objects.filter().order_by('first_name'),
            'remarks_list' : RemarksLib.objects.filter(status = 1).order_by('name'),
            'is_actual_date': date_actual,
            'permissions' : role_names,
            'created_by' :  data
        }
        return render(request, 'receive/receive.html' , context)
    else:
        return render(request, 'pages/unauthorized.html')
   
@csrf_exempt
def api(request):
    # url = "https://caraga-portal.dswd.gov.ph/api/employee/list/search/?q="
    url = "https://caraga-portal.dswd.gov.ph/api/employee/list/load"
    headers = {
        "Authorization": "Token 7a8203defd27f14ca23dacd19ed898dd3ff38ef6"
    }
    response = requests.get(url, headers=headers)
    data = response.json()
    return JsonResponse({'data': data})
    
@login_required(login_url='login')
def checking(request):
    allowed_roles = ["Admin", "Incoming staff", "Validating staff"] 
    user_id = request.session.get('user_id', 0)

    role_permissions = RolePermissions.objects.filter(user_id=user_id).values('role_id')
    role_details = RoleDetails.objects.filter(id__in=role_permissions).values('role_name')
    role_names = [entry['role_name'] for entry in role_details]
    date_actual = SystemConfiguration.objects.filter().first().date_actual

    created_user_name = RolePermissions.objects.filter(role_id=2)
    user_name = RolePermissions.objects.filter(role_id=3) 
    created_get_id = created_user_name.values_list('user_id', flat=True)
    get_id = user_name.values_list('user_id', flat=True)
    data = []
    created_data = []

    for c_user_id in created_get_id:
        c_userData = AuthUser.objects.filter(id=c_user_id)
        c_full_name = c_userData[0].first_name + ' ' + c_userData[0].last_name if c_userData else ''
        c_item_entry = {
            'id': c_userData[0].id,
            'full_name': c_full_name
        }
        created_data.append(c_item_entry)
    
    for user_id in get_id:
        userData = AuthUser.objects.filter(id=user_id)
        full_name = userData[0].first_name + ' ' + userData[0].last_name if userData else ''
        item_entry = {
            'id': userData[0].id,
            'full_name': full_name
        }
        data.append(item_entry)


    if any(role_name in allowed_roles for role_name in role_names):
        context = {
            'employee_list' : TevIncoming.objects.filter().order_by('first_name'),
            'remarks_list' : RemarksLib.objects.filter(status = 1).order_by('name'),
            'permissions' : role_names,
            'is_actual_date': date_actual,
            'created_by' :  created_data,
            'reviewed_by' :  data
        }
        return render(request, 'receive/review_docs.html', context)
    else:
        return render(request, 'pages/unauthorized.html')
    
    
@login_required(login_url='login')
@csrf_exempt
def search_list(request):
    allowed_roles = ["Admin", "Incoming staff", "Validating staff"] 
    return JsonResponse({'data': "success"})
    
def item_load(request):
    _search = request.GET.get('search[value]')
    _order_dir = request.GET.get('order[0][dir]')
    _order_dash = '-' if _order_dir == 'desc' else ''
    _order_col_num = request.GET.get('order[0][column]')
    FIdNumber= request.GET.get('FIdNumber')
    FTransactionCode = request.GET.get('FTransactionCode')
    FDateTravel= request.GET.get('FDateTravel') 
    FIncomingIn= request.GET.get('FIncomingIn')
    FOriginalAmount= request.GET.get('FOriginalAmount')
    FFinalAmount= request.GET.get('FFinalAmount')
    FAccountNumber= request.GET.get('FAccountNumber')
    FIncomingBy= request.GET.get('FIncomingBy')
    FFirstName= request.GET.get('FFirstName')
    FMiddleName= request.GET.get('FMiddleName')
    FLastName= request.GET.get('FLastName')
    FAdvancedFilter =  request.GET.get('FAdvancedFilter')
    FStatus = request.GET.get('FStatus')
    FCreatedBy = request.GET.get('FCreatedBy')
    EmployeeList = request.GET.getlist('EmployeeList[]')
    status_txt = ''
    if _search in "returned":
        status_txt = '3'
    else:
        status_txt = '1'
    id_numbers = EmployeeList if EmployeeList else []
    if FAdvancedFilter and not EmployeeList:
        query = """
            SELECT t1.*, GROUP_CONCAT(t3.name SEPARATOR ', ') AS lacking
            FROM tev_incoming t1
            LEFT JOIN remarks_r AS t2 ON t2.incoming_id = t1.id
            LEFT JOIN remarks_lib AS t3 ON t3.id = t2.remarks_lib_id
            WHERE (t1.code, t1.id) IN (
                SELECT DISTINCT code, MAX(id)
                FROM tev_incoming
                GROUP BY code 
            )
            AND ((`status_id` IN (3) AND slashed_out IS NOT NULL) OR (`status_id` IN (1) AND slashed_out IS NULL)) 
            AND (code LIKE %s
            AND id_no LIKE %s
            AND account_no LIKE %s
            AND date_travel LIKE %s
            AND original_amount LIKE %s
            AND final_amount LIKE %s
            AND incoming_in LIKE %s
            AND status_id LIKE %s
            AND user_id LIKE %s
            )GROUP BY t1.id ORDER BY id DESC;
        """

        params = [
            '%' + FTransactionCode + '%' if FTransactionCode else "%%",
            '%' + EmployeeList + '%' if EmployeeList else "%%",
            '%' + FAccountNumber + '%' if FAccountNumber else "%%",
            '%' + FDateTravel + '%' if FDateTravel else "%%",
            '%' + FOriginalAmount + '%' if FOriginalAmount else "%%",
            '%' + FFinalAmount + '%' if FFinalAmount else "%%",
            '%' + FIncomingIn + '%' if FIncomingIn else "%%",
            '%' + FStatus + '%' if FStatus else "%%",
            '%' + FCreatedBy + '%' if FCreatedBy else "%%"
        ]

    elif FAdvancedFilter:
        query = """
            SELECT t1.*, GROUP_CONCAT(t3.name SEPARATOR ', ') AS lacking
            FROM tev_incoming t1
            LEFT JOIN remarks_r AS t2 ON t2.incoming_id = t1.id
            LEFT JOIN remarks_lib AS t3 ON t3.id = t2.remarks_lib_id
            WHERE (t1.code, t1.id) IN (
                    SELECT DISTINCT code, MAX(id)
                    FROM tev_incoming
                    GROUP BY code 
            )
            AND ((`status_id` IN (3) AND slashed_out IS NOT NULL) OR (`status_id` IN (1) AND slashed_out IS NULL)) 
            AND (code LIKE %s
            AND id_no IN %s
            AND account_no LIKE %s
            AND date_travel LIKE %s
            AND original_amount LIKE %s
            AND final_amount LIKE %s
            AND incoming_in LIKE %s
            AND status_id LIKE %s
            AND user_id LIKE %s
            )GROUP BY t1.id ORDER BY id DESC;
        """

        params = [
            '%' + FTransactionCode + '%' if FTransactionCode else "%%",
            tuple(id_numbers),
            '%' + FAccountNumber + '%' if FAccountNumber else "%%",
            '%' + FDateTravel + '%' if FDateTravel else "%%",
            '%' + FOriginalAmount + '%' if FOriginalAmount else "%%",
            '%' + FFinalAmount + '%' if FFinalAmount else "%%",
            '%' + FIncomingIn + '%' if FIncomingIn else "%%",
            '%' + FStatus + '%' if FStatus else "%%",
            '%' + FCreatedBy + '%' if FCreatedBy else "%%"
        ]

    elif _search:
        query = """
            SELECT t1.*, GROUP_CONCAT(t3.name SEPARATOR ', ') AS lacking
            FROM tev_incoming t1
            LEFT JOIN remarks_r AS t2 ON t2.incoming_id = t1.id
            LEFT JOIN remarks_lib AS t3 ON t3.id = t2.remarks_lib_id
            WHERE (t1.code, t1.id) IN (
                    SELECT DISTINCT code, MAX(id)
                    FROM tev_incoming
                    GROUP BY code 
            )
            AND ((`status_id` IN (3) AND slashed_out IS NOT NULL) OR (`status_id` IN (1) AND slashed_out IS NULL)) 
            AND (first_name LIKE %s
            OR last_name LIKE %s
            OR id_no LIKE %s
            OR original_amount LIKE %s
            OR final_amount LIKE %s
            )GROUP BY t1.id ORDER BY id DESC;
        """
                
        params = [
            '%' + _search + '%' if _search else "%%",
            '%' + _search + '%' if _search else "%%",
            '%' + _search + '%' if _search else "%%",
            '%' + _search + '%' if _search else "%%",
            '%' + _search + '%' if _search else "%%",
        ]
    else:
        query = """
            SELECT t1.*, GROUP_CONCAT(t3.name SEPARATOR ', ') AS lacking
            FROM tev_incoming t1
            LEFT JOIN remarks_r AS t2 ON t2.incoming_id = t1.id
            LEFT JOIN remarks_lib AS t3 ON t3.id = t2.remarks_lib_id
            WHERE (t1.code, t1.id) IN (
                    SELECT DISTINCT code, MAX(id)
                    FROM tev_incoming
                    GROUP BY code 
            )
            AND ((`status_id` IN (3) AND slashed_out IS NOT NULL) OR (`status_id` IN (1) AND slashed_out IS NULL)) 
            AND (code LIKE %s
            OR first_name LIKE %s
            OR middle_name LIKE %s
            OR last_name LIKE %s
            OR id_no LIKE %s
            OR account_no LIKE %s
            OR date_travel LIKE %s
            OR original_amount LIKE %s
            OR final_amount LIKE %s
            OR status_id LIKE %s
            )GROUP BY t1.id ORDER BY id DESC;
        """
            
        params = ['%' + _search + '%', '%' + _search + '%', '%' + _search + '%', '%' + _search + '%', '%' + _search + '%', '%' + _search + '%', '%' + _search + '%', '%' + _search + '%', '%' + _search + '%','%' + status_txt + '%']
    
    with connection.cursor() as cursor:
        cursor.execute(query, params)
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
        full_name = userData[0].first_name if userData else ''
        
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
            'lacking': item['lacking'],
            'status': item['status_id'],
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
    _search = request.GET.get('search[value]')
    _order_dir = request.GET.get('order[0][dir]')
    FIdNumber= request.GET.get('FIdNumber')
    FTransactionCode = request.GET.get('FTransactionCode')
    FDateTravel= request.GET.get('FDateTravel') 
    FIncomingIn= request.GET.get('FIncomingIn')
    FOriginalAmount= request.GET.get('FOriginalAmount')
    FFinalAmount= request.GET.get('FFinalAmount')
    FAccountNumber= request.GET.get('FAccountNumber')
    FIncomingBy= request.GET.get('FIncomingBy')
    FFirstName= request.GET.get('FFirstName')
    FMiddleName= request.GET.get('FMiddleName')
    FLastName= request.GET.get('FLastName')
    FAdvancedFilter =  request.GET.get('FAdvancedFilter')
    FStatus = request.GET.get('FStatus')
    EmployeeList = request.GET.getlist('EmployeeList[]')
    FReviewedBy = request.GET.get('FReviewedBy')
    FCreatedBy = request.GET.get('FCreatedBy')

    status_txt = ''
    if _search in "returned":
        status_txt = '3'

    elif _search in "for checking":
        status_txt = '2'
    else:
        status_txt = '7'
        
    id_numbers = EmployeeList if EmployeeList else []

    if FAdvancedFilter:
        query = """
            SELECT t1.*, GROUP_CONCAT(t3.name SEPARATOR ', ') AS lacking
            FROM tev_incoming t1
            LEFT JOIN remarks_r AS t2 ON t2.incoming_id = t1.id
            LEFT JOIN remarks_lib AS t3 ON t3.id = t2.remarks_lib_id
            WHERE (t1.status_id = 2
                OR t1.status_id = 7
                OR (t1.status_id = 3 AND t1.slashed_out IS NULL))
        """
        params = []

        if FStatus:
            query += " AND t1.status_id = %s"
            params.append(FStatus)

        if FTransactionCode:
            query += " AND t1.code = %s"
            params.append(FTransactionCode)

        if FIdNumber:
            query += " AND t1.id_no = %s"
            params.append(FIdNumber)

        if FDateTravel:
            query += " AND t1.date_travel LIKE %s"
            params.append(f'%{FDateTravel}%')

        if FIncomingIn:
            query += " AND t1.incoming_in = %s"
            params.append(FIncomingIn)

        if FAccountNumber:
            query += " AND t1.account_no = %s"
            params.append(FAccountNumber)

        if FOriginalAmount:
            query += " AND t1.original_amount = %s"
            params.append(FOriginalAmount)

        if FFinalAmount:
            query += " AND t1.final_amount = %s"
            params.append(FFinalAmount)
        
        if FCreatedBy:
            query += " AND t1.user_id = %s"
            params.append(FCreatedBy)

        if FReviewedBy:
            query += " AND t1.reviewed_by = %s"
            params.append(FReviewedBy)

        if EmployeeList:
            placeholders = ', '.join(['%s' for _ in range(len(EmployeeList))])
            query += f" AND t1.id_no IN ({placeholders})"
            params.extend(EmployeeList)
        query += " GROUP BY t1.id ORDER BY t1.incoming_out DESC;"



    elif _search:
        query = """
            SELECT t1.*, GROUP_CONCAT(t3.name SEPARATOR ', ') AS lacking
            FROM tev_incoming t1
            LEFT JOIN remarks_r AS t2 ON t2.incoming_id = t1.id
            LEFT JOIN remarks_lib AS t3 ON t3.id = t2.remarks_lib_id
            WHERE (t1.status_id = 2
                            OR t1.status_id = 7
                            OR (t1.status_id = 3 AND t1.slashed_out IS NULL)
            )
            AND (code LIKE %s
            OR first_name LIKE %s
            OR last_name LIKE %s
            OR id_no LIKE %s
            OR original_amount LIKE %s
            OR final_amount LIKE %s
            )GROUP BY t1.id ORDER BY id DESC;
        """

        params = [
            '%' + _search + '%' if _search else "%%",
            '%' + _search + '%' if _search else "%%",
            '%' + _search + '%' if _search else "%%",
            '%' + _search + '%' if _search else "%%",
            '%' + _search + '%' if _search else "%%",
            '%' + _search + '%' if _search else "%%",
        ]
    else:

        query = """
            SELECT t1.*, GROUP_CONCAT(t3.name SEPARATOR ', ') AS lacking
            FROM tev_incoming t1
            LEFT JOIN remarks_r AS t2 ON t2.incoming_id = t1.id
            LEFT JOIN remarks_lib AS t3 ON t3.id = t2.remarks_lib_id
            WHERE (t1.status_id = 2
                            OR t1.status_id = 7
                            OR (t1.status_id = 3 AND t1.slashed_out IS NULL)
            )
            AND (code LIKE %s
            OR id_no LIKE %s
            OR account_no LIKE %s
            OR date_travel LIKE %s
            OR original_amount LIKE %s
            OR final_amount LIKE %s
            OR remarks LIKE %s
            OR status_id LIKE %s
            )GROUP BY t1.id ORDER BY id DESC;
        """
        params = ['%' + _search + '%', '%' + _search + '%', '%' + _search + '%', '%' + _search + '%', '%' + _search + '%', '%' + _search + '%', '%' + _search + '%','%' + status_txt + '%']
    
    with connection.cursor() as cursor:
        cursor.execute(query, params)
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
        full_name = userData[0].first_name if userData else ''
        
        first_name = item['first_name'] if item['first_name'] else ''
        middle_name = item['middle_name'] if item['middle_name'] else ''
        last_name = item['last_name'] if item['last_name'] else ''
        
        emp_fullname = f"{first_name} {middle_name} {last_name}".strip()
        formatted_date_out = date(item['incoming_out'], "F j, Y g:i A")

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
            'incoming_out': formatted_date_out,
            'remarks': item['remarks'],
            'lacking': item['lacking'],
            'status': item['status_id'],
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



def read_excel_file(excel_file):
    workbook = load_workbook(excel_file, data_only=True)
    worksheet = workbook.active
    has_empty_fields = False

    excel_data = []
    for row in worksheet.iter_rows(min_row=2, values_only=True):
        id_no, amount, date_travel = row
        
        if amount is None:
            amount = 0
        
        dates = []
        if date_travel:
            date_list = date_travel.split(',')
            for date_str in date_list:
                date_obj = datetime.strptime(date_str.strip(), '%d-%m-%Y')
                dates.append(date_obj.strftime('%d-%m-%Y')) 

        excel_data.append({
            'id_no': id_no,
            'amount': amount,
            'date_travel': dates,
        })

    for record in excel_data:
        if record['id_no'] is None or record['amount'] == 0 or not record['date_travel']:
            has_empty_fields = True
            break

    if has_empty_fields:
        return has_empty_fields
    else:
        return excel_data

@csrf_exempt
def upload_tev(request):
    user_id = request.session.get('user_id', 0)

    if request.method == 'POST' and request.FILES.get('ExcelData'):
        excel_file = request.FILES['ExcelData']
        if not excel_file.name.endswith('xlsx'):
            return JsonResponse({'data': 'errorxlsx'})

        try:
            sc_code = SystemConfiguration.objects.first()
            sc_code = sc_code.transaction_code
            matched_data = []
            id_list = []
            duplicate_travel = []
            duplicate_te = []

            formatted_duplicates = []
            duplicate_dates = {}
            seen_dates = {}

            employees_data = json.loads(request.POST.get('employees'))
            excel_data = read_excel_file(excel_file)

            if excel_data ==True:
                response_data = {
                    'data': 'empty'
                }
                return JsonResponse(response_data) 

            for row in excel_data:
                g_code = generate_code()
                id_no, amount, date_travel = row['id_no'], row['amount'], row['date_travel']
                

                for date in date_travel:
                    if id_no not in seen_dates:
                        seen_dates[id_no] = set()
                    if date in seen_dates[id_no]:
                        if id_no not in duplicate_dates:
                            duplicate_dates[id_no] = []
                        duplicate_dates[id_no].append(date)
                    seen_dates[id_no].add(date)
                
                id_number_value = None
                formatted_date_travel = ', '.join(date_travel).replace(', ', ',')
                for employee in employees_data:
                    
                    if employee.get('idNumber') == id_no:
                        id_number_value = employee.get('idNumber')
                        acc_no_value = employee.get('accNumber')
                        first_name_value = employee.get('firstName')
                        middle_initial_value = employee.get('middleInitial')
                        last_name_value = employee.get('lastName')

                dates_to_check = formatted_date_travel.split(',')
                duplicate_records = {}

                for date in dates_to_check:
                    results = TevIncoming.objects.filter(date_travel__contains=date).filter(id_no=id_number_value).all()
                    if results:
                        for record in results:
                            if date not in duplicate_records:
                                duplicate_records[date] = []
                            duplicate_records[date].append({'id_no': record.id_no, 'date_travel': record.date_travel})


                for date, records in duplicate_records.items():
                    for record in records:
                        duplicate_te.append({
                            'id_no': record["id_no"],
                            'travel': date
                        })
                        
                if results:
                    # duplicate_travel.append(formatted_date_travel)
                    duplicate_travel.append({
                        'id_no': id_no,
                        'duplicate_travel': formatted_date_travel
                    })

                if id_number_value:
                    matched_data.append({
                        'id_no': id_no,
                        'g_code': g_code,
                        'amount': amount,
                        'date_travel': formatted_date_travel,
                        'idNumber': id_number_value,
                        'accNumber': acc_no_value,
                        'firstName': first_name_value,
                        'middleInitial': middle_initial_value,
                        'lastName': last_name_value
                    })
                    system_config = SystemConfiguration.objects.first()
                    system_config.transaction_code = g_code
                    system_config.save()

                else:
                    id_list.append(id_no)
            if id_list:
                system_config = SystemConfiguration.objects.first()
                system_config.transaction_code = sc_code
                system_config.save()
                response_data = {
                    'data': 'success',
                    'id_no': id_list
                }
                return JsonResponse(response_data) 
            
            elif duplicate_dates:
                for id_no, dates in duplicate_dates.items():
                    formatted_entry = {
                        'id_no': id_no,
                        'duplicate_travel': ','.join(dates)
                    }
                    formatted_duplicates.append(formatted_entry)
                response_data = {
                    'data': 'success',
                    'duplicate_excel_dates': formatted_duplicates
                }
                return JsonResponse(response_data) 

            elif duplicate_travel:
                response_data = {
                    'data': 'success',
                    'duplicate_travel': duplicate_travel
                }
                return JsonResponse(response_data) 
            else:
                try:
                    matched_data_list = matched_data
                    tev_incoming_instances = [
                        TevIncoming(
                            code=data['g_code'],
                            original_amount=data['amount'],
                            id_no=data['id_no'],
                            account_no=data['accNumber'],
                            date_travel=data['date_travel'],
                            first_name=data['firstName'],
                            middle_name=data['middleInitial'],
                            last_name=data['lastName'],
                            user_id = user_id,
                            is_upload = True
                            )
                            for data in matched_data_list
                        ]
                    
                    TevIncoming.objects.bulk_create(tev_incoming_instances)
                    return JsonResponse({'data': 'success'})
        
            
                except json.JSONDecodeError as e:
                   print(f"Error decoding JSON: {e}")
                   matched_data_list = []

        except json.JSONDecodeError:
            return JsonResponse({'data': 'errorjson'})

    else:
        return JsonResponse({'data': 'error'})

def item_edit(request):
    id = request.GET.get('id')
    items = TevIncoming.objects.get(pk=id)
    data = serialize("json", [items])
    return HttpResponse(data, content_type="application/json")

def preview_received(request):

    id = request.GET.get('id')
    with connection.cursor() as cursor:
        query = """
        SELECT
            t1.id,
            t1.code,
            t1.first_name,
            t1.middle_name,
            t1.last_name,
            t1.id_no,
            t1.account_no,
            t1.date_travel,
            t1.original_amount,
            t1.final_amount,
            t1.incoming_in,
            t1.incoming_out,
            t1.slashed_out,
            t1.remarks,
            t1.user_id,
            t1.status_id,
            GROUP_CONCAT(t3.id SEPARATOR ', ') AS lacking,
            GROUP_CONCAT(t2.date SEPARATOR ', ') AS date_remarks
        FROM
            tev_incoming t1
            LEFT JOIN remarks_r AS t2 ON t2.incoming_id = t1.id
            LEFT JOIN remarks_lib AS t3 ON t3.id = t2.remarks_lib_id
        WHERE
            t1.id = %s
        """
        cursor.execute(query, [id])
        result = cursor.fetchone()

    if result:
        orig_amt =  Decimal(result[8])
        orig_amt = orig_amt.quantize(Decimal("0.01"))
        data = {
            'id': result[0],
            'code': result[1],
            'first_name': result[2],
            'middle_name': result[3],
            'last_name': result[4],
            'id_no': result[5],
            'account_no': result[6],
            'date_travel': result[7],
            'original_amount': orig_amt,
            'final_amount': result[9],
            'incoming_in': result[10],
            'incoming_out': result[11],
            'slashed_out': result[12],
            'remarks': result[13],
            'user_id': result[14],
            'status_id': result[15],
            'lacking': result[16],
            'date_remarks': result[17],
        }
        return JsonResponse(data)
    else:
        return JsonResponse({'error': 'No data found for the given ID'}, status=404)

@csrf_exempt
def item_update(request):
    id = request.POST.get('ItemID')
    name = request.POST.get('EmpName')
    middle = request.POST.get('EmpMiddle')
    lname = request.POST.get('EmpLastname')
    amount = request.POST.get('OriginalAmount')
    selected_remarks = request.POST.getlist('selectedRemarks[]')
    selected_dates = request.POST.getlist('selectedDate[]')
    travel_date = request.POST.get('DateTravel')
    range_travel = request.POST.get('RangeTravel')
    date_received = request.POST.get('DateReceived')
    id_no = request.POST.get('IdNumber')
    acc_no = request.POST.get('AccountNumber')
    div = request.POST.get('Division')
    sec = request.POST.get('Section')
    contact = request.POST.get('Contact')



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
        results = Q(first_name=name) & \
          Q(middle_name=middle) & \
          Q(last_name=lname) & \
          Q(date_travel__icontains=cleaned_date) & \
          ~Q(status_id=3) & \
          ~Q(id=id)
        
        results = TevIncoming.objects.filter(results).values('date_travel')
        
        if results:
            duplicate_travel.append(cleaned_date)

    if duplicate_travel:
        formatted_dates = [date.replace("'", "") for date in duplicate_travel]
        result = ",".join(formatted_dates)

        date_components = result.split(',')
        def format_date(date_str):
            date_object = datetime.strptime(date_str, '%d-%m-%Y')
            formatted_date = date_object.strftime('%b. %d, %Y')
            return formatted_date
        formatted_dates = [format_date(date) for date in date_components]
        formatted_dates_string = ', '.join(formatted_dates)
        formatted_dates_string = formatted_dates_string
        
        TevIncoming.objects.filter(id=id).update(first_name=name,middle_name = middle,last_name = lname, id_no = id_no, account_no = acc_no, date_travel = travel_date, original_amount=amount, incoming_in = date_received, remarks = formatted_dates_string, division = div, section = sec, contact_no = contact)
        Remarks_r.objects.filter(incoming_id=id).delete()
        for selected_remarks, selected_dates in zip(selected_remarks, selected_dates):
            remarks_lib = Remarks_r(
                date=selected_dates,
                incoming_id=id,
                remarks_lib_id=selected_remarks
            )
            remarks_lib.save()
        
        return JsonResponse({'data': 'error', 'message': duplicate_travel})
    else:
        TevIncoming.objects.filter(id=id).update(first_name=name,middle_name = middle,last_name = lname, id_no = id_no, account_no = acc_no, date_travel = travel_date, original_amount=amount, incoming_in = date_received, remarks = None, division = div, section = sec, contact_no = contact)
        Remarks_r.objects.filter(incoming_id=id).delete()
        for selected_remarks, selected_dates in zip(selected_remarks, selected_dates):
            remarks_lib = Remarks_r(
                date=selected_dates,
                incoming_id=id,
                remarks_lib_id=selected_remarks
            )
            remarks_lib.save()
        return JsonResponse({'data': 'success'})
    

@csrf_exempt
def item_rod_update(request):

    id = request.POST.get('ItemID')
    name = request.POST.get('EmpName')
    middle = request.POST.get('EmpMiddle')
    lname = request.POST.get('EmpLastname')
    travel_date = request.POST.get('DateTravel')
    date_received = request.POST.get('DateReceived')
    id_no = request.POST.get('IdNumber')
    acc_no = request.POST.get('AccountNumber')
    div = request.POST.get('Division')
    sec = request.POST.get('Section')
    orig_amnt = request.POST.get('FAmount')
    duplicate_travel = []
    individual_dates = travel_date.split(',')

    for date in individual_dates:
        cleaned_date = date.strip()
        results = Q(first_name=name) & \
          Q(middle_name=middle) & \
          Q(last_name=lname) & \
          Q(date_travel__icontains=cleaned_date) & \
          ~Q(status_id=3) & \
          ~Q(id=id)
        
        results = TevIncoming.objects.filter(results).values('date_travel')
        
        if results:
            duplicate_travel.append(cleaned_date)

    if duplicate_travel:
        formatted_dates = [date.replace("'", "") for date in duplicate_travel]
        result = ",".join(formatted_dates)

        date_components = result.split(',')
        def format_date(date_str):
            date_object = datetime.strptime(date_str, '%d-%m-%Y')
            formatted_date = date_object.strftime('%b. %d, %Y')
            return formatted_date
        formatted_dates = [format_date(date) for date in date_components]
        formatted_dates_string = ', '.join(formatted_dates)
        formatted_dates_string = formatted_dates_string
        TevIncoming.objects.filter(id=id).update(first_name=name,middle_name = middle,last_name = lname, id_no = id_no, account_no = acc_no,date_travel = travel_date, incoming_in = date_received, remarks = formatted_dates_string, division = div, section = sec, original_amount = orig_amnt)
        return JsonResponse({'data': 'error', 'message': duplicate_travel})
    else:
        TevIncoming.objects.filter(id=id).update(first_name=name,middle_name = middle,last_name = lname, id_no = id_no, account_no = acc_no,date_travel = travel_date, incoming_in = date_received, remarks = None, division = div, section = sec, original_amount = orig_amnt)
        return JsonResponse({'data': 'success'})

@csrf_exempt
def item_returned(request):
    id = request.POST.get('ItemID')
    travel_date = request.POST.get('HDateTravel')
    selected_remarks = request.POST.getlist('selectedRemarks[]')
    selected_dates = request.POST.getlist('selectedDate[]')

    travel_date_stripped = travel_date.strip()
    travel_date_spaces = travel_date_stripped.replace(' ', '')
    id = request.POST.get('ItemID')

    data = TevIncoming.objects.filter(id=id).first()
    tev_add = TevIncoming(code=data.code,first_name=data.first_name,middle_name=data.middle_name,last_name = data.last_name,id_no = data.id_no, account_no = data.account_no, date_travel = travel_date_spaces,original_amount=data.original_amount,final_amount = data.final_amount,incoming_in =date_time.datetime.now(),user_id=data.user_id)
    tev_add.save()

    last_added_tevincoming = TevIncoming.objects.latest('id')
    for selected_remarks, selected_dates in zip(selected_remarks, selected_dates):
        remarks_lib = Remarks_r(
            date=selected_dates,
            incoming_id=last_added_tevincoming.id,
            remarks_lib_id=selected_remarks
        )
        remarks_lib.save()

    return JsonResponse({'data': 'success'})



@csrf_exempt
def item_add(request):
    amount = request.POST.get('OriginalAmount')
    travel_date = request.POST.get('DateTravel')
    range_travel = request.POST.get('RangeTravel')
    date_received = request.POST.get('DateReceived')
    idd_no = request.POST.get('IdNumber')
    acct_no = request.POST.get('AccountNumber')
    contact = request.POST.get('Contact')
    name = request.POST.get('EmpName')
    middle = request.POST.get('EmpMiddle')
    lname = request.POST.get('EmpLastname')
    user_id = request.session.get('user_id', 0)
    division = request.POST.get('Division')
    section = request.POST.get('Section')
    selected_remarks = request.POST.getlist('selectedRemarks[]')
    selected_dates = request.POST.getlist('selectedDate[]')
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

        formatted_dates = [date.replace("'", "") for date in duplicate_travel]
        result = ",".join(formatted_dates)

        date_components = result.split(',')
        def format_date(date_str):
            date_object = datetime.strptime(date_str, '%d-%m-%Y')
            formatted_date = date_object.strftime('%b. %d, %Y')
            return formatted_date
        formatted_dates = [format_date(date) for date in date_components]
        formatted_dates_string = ', '.join(formatted_dates)
        formatted_dates_string = formatted_dates_string
        
        if date_received:
            tev_add = TevIncoming(
                code=g_code,
                first_name=name,
                middle_name=middle,
                last_name=lname,
                id_no=idd_no,
                account_no=acct_no,
                date_travel=cleaned_dates,
                original_amount=amount,
                incoming_in = date_received,
                remarks=formatted_dates_string,
                user_id=user_id,
                division = division,
                section = section,
                contact_no = contact
            )
        else:
            tev_add = TevIncoming(
                code=g_code,
                first_name=name,
                middle_name=middle,
                last_name=lname,
                id_no=idd_no,
                account_no=acct_no,
                date_travel=cleaned_dates,
                incoming_in = date_time.datetime.now(),
                original_amount=amount,
                remarks=formatted_dates_string,
                user_id=user_id,
                division = division,
                section = section,
                contact_no = contact
            )
        tev_add.save()

        if tev_add.id:
            system_config = SystemConfiguration.objects.first()
            system_config.transaction_code = g_code
            system_config.save()
            last_added_tevincoming = TevIncoming.objects.latest('id')

            for selected_remarks, selected_dates in zip(selected_remarks, selected_dates):
                remarks_lib = Remarks_r(
                    date=selected_dates,
                    incoming_id=last_added_tevincoming.id,
                    remarks_lib_id=selected_remarks
                )
                remarks_lib.save()

        return JsonResponse({'data': 'error', 'message': duplicate_travel})

    else:
        if date_received:
            tev_add = TevIncoming(
                code=g_code,
                first_name=name,
                middle_name=middle,
                last_name=lname,
                id_no=idd_no,
                account_no=acct_no,
                date_travel=cleaned_dates,
                original_amount=amount,
                incoming_in = date_received,
                user_id=user_id,
                division = division,
                section = section,
                contact_no = contact
            )
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
                incoming_in = date_time.datetime.now(),
                user_id=user_id,
                division = division,
                section = section,
                contact_no = contact
            )
        tev_add.save()

        last_added_tevincoming = TevIncoming.objects.latest('id')

        for selected_remarks, selected_dates in zip(selected_remarks, selected_dates):
            remarks_lib = Remarks_r(
                date=selected_dates,
                incoming_id=last_added_tevincoming.id,
                remarks_lib_id=selected_remarks
            )
            remarks_lib.save()

        if tev_add.id:
            system_config = SystemConfiguration.objects.first()
            system_config.transaction_code = g_code
            system_config.save()

        return JsonResponse({'data': 'success', 'g_code': g_code})

@csrf_exempt
def out_pending_tev(request):
    user_id = request.session.get('user_id', 0) 
    out_list = request.POST.getlist('out_list[]')
    for item_id  in out_list:
        tev_update = TevIncoming.objects.filter(id=item_id).update(status=2,incoming_out=date_time.datetime.now(), forwarded_by = user_id)
    return JsonResponse({'data': 'success'})


@csrf_exempt
def add_existing_record(request):
    out_list = request.POST.getlist('out_list[]')
    
    for item_id  in out_list:
        tev_update = TevIncoming.objects.filter(id=item_id).update(status=2,incoming_out=date_time.datetime.now())
    
    return JsonResponse({'data': 'success'})


def send_notification(message, contact_number):
    url = 'https://wiserv.dswd.gov.ph/soap/?wsdl'
    try:
        client = Client(url)
        result = client.service.sendMessage(UserName='crgwiservuser', PassWord='#w153rvcr9!', WSID='0',
                                            MobileNo=contact_number, Message=message)
    except Exception:
        pass

def convert_date_string(date_str):
    date_list = date_str.split(',')
    formatted_dates = []
    for date in date_list:
        d, m, y = date.split('-')
        month_name = datetime.strptime(m, '%m').strftime('%B')
        formatted_date = f"{month_name} {d} {y}"
        formatted_dates.append(formatted_date)
    return ', '.join(formatted_dates)



@csrf_exempt
def out_checking_tev(request):

    out_list = request.POST.getlist('out_list[]')  
    user_id = request.session.get('user_id', 0) 
    
    for item_id in out_list:
        tev_update = TevIncoming.objects.filter(id=item_id).first()  

        if tev_update:
            if tev_update.status_id == 3:
                tev_update.slashed_out = date_time.datetime.now()
                tev_update.review_date_forwarded = date_time.datetime.now()
                tev_update.review_forwarded_by = user_id
            else:
                tev_update.status_id = 4
            tev_update.review_date_forwarded = date_time.datetime.now()
            tev_update.review_forwarded_by = user_id
            tev_update.save()
            # fullname = tev_update.first_name
            # contact_no = "09518149919"
            # date_travel = tev_update.date_travel
            # formatted_dates = convert_date_string(date_travel)
            # message = 'Good day,{}! Your Travel in {} is being Forwarded to Budget Section and Ready to Obligate - DSWD CARAGA TRIS SYSTEM'.format(fullname,formatted_dates)
            # send_notification(message, contact_no)
            # contact_numbers = [{first_name: ['09518149919']}]
            # for contact in contact_numbers:
            #     for k, vs in contact.items():
            #         for v in vs:
            #             send_notification('Good day,{}! Your Travel From January 25 2024 is being Forwarded to Budget Section and Ready to Obligate - DSWD CARAGA TRIS SYSTEM'.format(k, formatted_dates), v)
        else:
            pass 

    return JsonResponse({'data': 'success'})

@csrf_exempt
def tev_details(request):
    
    tev_id = request.POST.get('tev_id')
    
    result = TevIncoming.objects.filter(id=tev_id).first()
    data = {
        'data': model_to_dict(result)
    }
    return JsonResponse(data)


def review_details(request):
    tev_id = request.POST.get('tev_id')
    with connection.cursor() as cursor:
        query = """
        SELECT
            t1.code,
            t1.first_name,
            t1.middle_name,
            t1.last_name,
            t1.id_no,
            t1.account_no,
            t1.date_travel,
            t1.original_amount,
            t1.final_amount,
            t1.incoming_in,
            t1.incoming_out,
            t1.slashed_out,
            t1.remarks,
            t1.user_id,
            t1.status_id,
            GROUP_CONCAT(t3.id SEPARATOR ', ') AS lacking,
            GROUP_CONCAT(t2.date SEPARATOR ', ') AS date_remarks
        FROM
            tev_incoming t1
            LEFT JOIN remarks_r AS t2 ON t2.incoming_id = t1.id
            LEFT JOIN remarks_lib AS t3 ON t3.id = t2.remarks_lib_id
        WHERE
            t1.id = %s
        """
        cursor.execute(query, [tev_id])
        result = cursor.fetchone()

    # Convert the result to a dictionary for JsonResponse
    if result:
        data = {
            'code': result[0],
            'first_name': result[1],
            'middle_name': result[2],
            'last_name': result[3],
            'id_no': result[4],
            'account_no': result[5],
            'date_travel': result[6],
            'original_amount': result[7],
            'final_amount': result[8],
            'incoming_in': result[9],
            'incoming_out': result[10],
            'slashed_out': result[11],
            'remarks': result[12],
            'user_id': result[13],
            'status_id': result[14],
            'lacking': result[15],
            'date_remarks': result[16],
        }
        return JsonResponse(data)
    else:
        return JsonResponse({'error': 'No data found for the given ID'}, status=404)



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
def updatetevdetails(request):
    user_id = request.session.get('user_id', 0)
    if request.method == 'POST':
        amount = request.POST.get('final_amount')
        status = request.POST.get('status')
        transaction_id = request.POST.get('transaction_id')
        selected_remarks = request.POST.getlist('selected_remarks[]')
        selected_dates = request.POST.getlist('selected_dates[]')
        TevIncoming.objects.filter(id=transaction_id).update(final_amount=amount,status=status, reviewed_by =user_id, date_reviewed =date_time.datetime.now())
        Remarks_r.objects.filter(incoming_id=transaction_id).delete()
        for selected_remarks, selected_dates in zip(selected_remarks, selected_dates):
            Remarks_r.objects.create(
                incoming_id=transaction_id,
                remarks_lib_id=selected_remarks,
                date=selected_dates
        )
        return JsonResponse({'data': 'success'})
    
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
    
@csrf_exempt
def updatetevamount(request):
    user_id = request.session.get('user_id', 0)
    if request.method == 'POST':
        amount = request.POST.get('final_amount')
        transaction_id = request.POST.get('transaction_id')
        selected_remarks = request.POST.getlist('selected_remarks[]')
        selected_dates = request.POST.getlist('selected_dates[]')
        TevIncoming.objects.filter(id=transaction_id).update(final_amount=amount)
        Remarks_r.objects.filter(incoming_id=transaction_id).delete()
        for selected_remarks, selected_dates in zip(selected_remarks, selected_dates):
            Remarks_r.objects.create(
                incoming_id=transaction_id,
                remarks_lib_id=selected_remarks,
                date=selected_dates
        )
        return JsonResponse({'data': 'success'})
    
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
    

@csrf_exempt
def delete_entry(request):
    item_id = request.POST.get('item_id')
    user_id = request.session.get('user_id', 0)

    userData = AuthUser.objects.filter(id=user_id).first()
    if not userData:
        return JsonResponse({'error': 'User not found'}, status=404)

    full_name = f"{userData.first_name} {userData.last_name}"

    try:
        with transaction.atomic():
            data = TevIncoming.objects.get(id=item_id)
            dl_codes = TevIncoming.objects.filter(code=data.code)

            for dl_code in dl_codes:
                remark_data = Remarks_r.objects.filter(incoming_id=dl_code.id)
                
                if remark_data: 
                    for remark in remark_data:
                        remarks_lib = RemarksLib.objects.filter(id=remark.remarks_lib_id).first()
                        description = (
                            "This Transaction from RECEIVED module is deleted with code number " + data.code +
                            " and ID Number : " + data.id_no + " Fullname : " + data.first_name + " " +
                            data.middle_name + " " + data.last_name + " with Original amount : " + str(data.original_amount) +
                            " and Date Travel : " + data.date_travel + " deleted by " + full_name +
                            " with remarks " + (remarks_lib.name if remarks_lib else "N/A")
                        )

                        tev_add = TransactionLogs(description=description, user_id=user_id, created_at=timezone.now())
                        tev_add.save()
                        remark.delete()
                else:
                    description = (
                            "This Transaction from RECEIVED module is deleted with code number " + data.code +
                            " and ID Number : " + data.id_no + " Fullname : " + data.first_name + " " +
                            data.middle_name + " " + data.last_name + " with Original amount : " + str(data.original_amount) +
                            " and Date Travel : " + data.date_travel + " deleted by " + full_name
                        )
                    tev_add = TransactionLogs(description=description, user_id=user_id, created_at=timezone.now())
                    tev_add.save()
                dl_code.delete()

            return JsonResponse({'data': 'success'})
    except Exception as e:
        print("Exception occurred:", str(e))
        transaction.rollback()
        return JsonResponse({'error': str(e)}, status=500)
    
@csrf_exempt
def addtevdetails(request):
    return JsonResponse({'data': 'success'})



