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
from openpyxl import load_workbook
from tablib import Dataset
import ast



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
    
def item_load(request):
    _search = request.GET.get('search[value]')
    _order_dir = request.GET.get('order[0][dir]')
    _order_dash = '-' if _order_dir == 'desc' else ''
    _order_col_num = request.GET.get('order[0][column]')
    FIdNumber= request.GET.get('FIdNumber')
    FTransactionCode = request.GET.get('FTransactionCode')
    FDateTravel= request.GET.get('FDateTravel') 
    FIncomingIn= request.GET.get('FIncomingIn')
    # FSLashedOut= request.GET.get('FSLashedOut')
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
    status_txt = ''
    if _search in "returned":
        status_txt = '3'
    else:
        status_txt = '1'
    id_numbers = EmployeeList if EmployeeList else []
    if FAdvancedFilter and not EmployeeList:
        query = """
            SELECT *
            FROM tev_incoming t1
            WHERE (code, id) IN (
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
            )ORDER BY id DESC;
        """

        params = [
            '%' + FTransactionCode + '%' if FTransactionCode else "%%",
            '%' + EmployeeList + '%' if EmployeeList else "%%",
            '%' + FAccountNumber + '%' if FAccountNumber else "%%",
            '%' + FDateTravel + '%' if FDateTravel else "%%",
            '%' + FOriginalAmount + '%' if FOriginalAmount else "%%",
            '%' + FFinalAmount + '%' if FFinalAmount else "%%",
            '%' + FIncomingIn + '%' if FIncomingIn else "%%",
            '%' + FStatus + '%' if FStatus else "%%"
        ]

    elif FAdvancedFilter:
        query = """
            SELECT *
            FROM tev_incoming t1
            WHERE (code, id) IN (
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
            )ORDER BY id DESC;
        """

        params = [
            '%' + FTransactionCode + '%' if FTransactionCode else "%%",
            tuple(id_numbers),
            '%' + FAccountNumber + '%' if FAccountNumber else "%%",
            '%' + FDateTravel + '%' if FDateTravel else "%%",
            '%' + FOriginalAmount + '%' if FOriginalAmount else "%%",
            '%' + FFinalAmount + '%' if FFinalAmount else "%%",
            '%' + FIncomingIn + '%' if FIncomingIn else "%%",
            '%' + FStatus + '%' if FStatus else "%%"
        ]

    else:
        query = """
            SELECT *
            FROM tev_incoming t1
            WHERE (code, id) IN (
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
            )ORDER BY id DESC;
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
    _order_dash = '-' if _order_dir == 'desc' else ''
    _order_col_num = request.GET.get('order[0][column]')
    FIdNumber= request.GET.get('FIdNumber')
    FTransactionCode = request.GET.get('FTransactionCode')
    FDateTravel= request.GET.get('FDateTravel') 
    FIncomingIn= request.GET.get('FIncomingIn')
    # FSLashedOut= request.GET.get('FSLashedOut')
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
    status_txt = ''
    if _search in "returned":
        status_txt = '3'

    elif _search in "for checking":
        status_txt = '2'
    else:
        status_txt = '7'
        
    id_numbers = EmployeeList if EmployeeList else []

    if FAdvancedFilter:
        def dictfetchall(cursor):
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

        query = """
            SELECT t.*
            FROM tev_incoming t
            WHERE (t.status_id = 2
                OR t.status_id = 7
                OR (t.status_id = 3 AND t.slashed_out IS NULL))
        """
        params = []

        if FTransactionCode:
            query += " AND t.code = %s"
            params.append(FTransactionCode)

        if FDateTravel:
            query += " AND t.date_travel = %s"
            params.append(FDateTravel)

        if FIncomingIn:
            query += " AND t.incoming_in = %s"
            params.append(FIncomingIn)

        if FStatus:
            query += " AND t.status_id = %s"
            params.append(FStatus)

            
        if FAccountNumber:
            query += " AND t.account_no = %s"
            params.append(FStatus)

        if FOriginalAmount:
            query += " AND t.original_amount = %s"
            params.append(FStatus)

        if FFinalAmount:
            query += " AND t.final_amount = %s"
            params.append(FStatus)

        if EmployeeList:
            placeholders = ', '.join(['%s' for _ in range(len(EmployeeList))])
            query += f" AND t.id_no IN ({placeholders})"
            params.extend(EmployeeList)

        query += " ORDER BY t.incoming_out DESC;"

        with connection.cursor() as cursor:
            cursor.execute(query, params)
            results = dictfetchall(cursor)

    else:
        print("third attempt")
        query = """
            SELECT t.*
            FROM tev_incoming t
            WHERE (t.status_id = 2
                    OR t.status_id = 7
                    OR (t.status_id = 3 AND t.slashed_out IS NULL)
            )
            AND (code LIKE %s
            OR id_no LIKE %s
            OR account_no LIKE %s
            OR date_travel LIKE %s
            OR original_amount LIKE %s
            OR final_amount LIKE %s
            OR remarks LIKE %s
            OR status_id LIKE %s
            )ORDER BY id DESC;
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

    excel_data = []
    for row in worksheet.iter_rows(min_row=2, values_only=True):
        id_no, amount, date_travel = row
        dates = [date.strip() for date in date_travel.split(',')]
        excel_data.append({
            'id_no': id_no,
            'amount': amount,
            'date_travel': dates,  # Store dates as a list of strings
        })

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

            print("codeenii")
            print(sc_code)


            matched_data = []
            id_list = []
            employees_data = json.loads(request.POST.get('employees'))
            excel_data = read_excel_file(excel_file)

            for row in excel_data:
                g_code = generate_code()
                id_no, amount, date_travel = row['id_no'], row['amount'], row['date_travel']
                id_number_value = None
                formatted_date_travel = ', '.join(date_travel).replace(', ', ',')
                for employee in employees_data:
                    
                    if employee.get('idNumber') == id_no:
                        id_number_value = employee.get('idNumber')
                        acc_no_value = employee.get('accNumber')
                        first_name_value = employee.get('firstName')
                        middle_initial_value = employee.get('middleInitial')
                        last_name_value = employee.get('lastName')

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
                        'lastName': last_name_value,
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
                            user_id = user_id
                            )
                            for data in matched_data_list
                        ]
                    TevIncoming.objects.bulk_create(tev_incoming_instances)
                    return JsonResponse({'data': 'success'})
            
                except json.JSONDecodeError as e:
                   print(f"Error decoding JSON: {e}")
                   matched_data_list = []

        except json.JSONDecodeError:
            print("JSON decoding error")
            return JsonResponse({'data': 'errorjson'})

    else:
        print("Invalid request")
        return JsonResponse({'data': 'error'})

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

        formatted_dates = [date.replace("'", "") for date in duplicate_travel]
        result = ",".join(formatted_dates)

        date_components = result.split(',')
        def format_date(date_str):
            date_object = datetime.strptime(date_str, '%d-%m-%Y')
            formatted_date = date_object.strftime('%b. %d, %Y')
            return formatted_date
        formatted_dates = [format_date(date) for date in date_components]
        formatted_dates_string = ', '.join(formatted_dates)
        formatted_dates_string = "Duplicate Travel for " + formatted_dates_string
        

        tev_add = TevIncoming(
            code=g_code,
            first_name=name,
            middle_name=middle,
            last_name=lname,
            id_no=idd_no,
            account_no=acct_no,
            date_travel=cleaned_dates,
            original_amount=amount,
            remarks=formatted_dates_string,
            user_id=user_id
        )
        tev_add.save()

        if tev_add.id:
            system_config = SystemConfiguration.objects.first()
            system_config.transaction_code = g_code
            system_config.save()

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
            if tev_update.status_id == 3:
                tev_update.slashed_out = date_time.datetime.now()
            else:
                tev_update.status_id = 4
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



