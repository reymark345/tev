from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from main.models import (AuthUser, TevIncoming, SystemConfiguration,RoleDetails, StaffDetails, Cluster, Charges, TevOutgoing, TevBridge, Division, PayrolledCharges, RolePermissions)
import json 
from django.core import serializers
from datetime import date, datetime, timedelta
from django.contrib.auth.hashers import make_password
from django.db import IntegrityError
import math
from django.core.serializers import serialize
from django.forms.models import model_to_dict
from urllib.parse import parse_qs
from django.db import connections
from django.db import IntegrityError, connection
from django.db.models import Q, Max
import datetime as date_time
from decimal import Decimal
from decimal import Decimal, ROUND_HALF_UP
from django.utils import timezone


def get_user_details(request):
    return StaffDetails.objects.filter(user_id=request.user.id).first()

def generate_code():
    trans_code = SystemConfiguration.objects.values_list(
        'transaction_code', flat=True
    ).first()

    last_code = trans_code.split('-')
    sample_date = date.today()
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
    user_details = get_user_details(request)
    allowed_roles = ["Admin", "Incoming staff", "Validating staff"] 
    role = RoleDetails.objects.filter(id=user_details.role_id).first()
    if role.role_name in allowed_roles:
        context = {
            'role_permission' : role.role_name,
            'cluster' : Cluster.objects.filter().order_by('name'),
            'division' : Division.objects.filter(status=0).order_by('name'),
        }
        return render(request, 'receive/list.html', context)
    else:
        return render(request, 'pages/unauthorized.html')
    
    
@login_required(login_url='login')
def list_payroll(request):
    allowed_roles = ["Admin", "Incoming staff", "Validating staff","Payroll staff", "Certified staff"] 
    user_id = request.session.get('user_id', 0)
    role_permissions = RolePermissions.objects.filter(user_id=user_id).values('role_id')
    role_details = RoleDetails.objects.filter(id__in=role_permissions).values('role_name')
    role_names = [entry['role_name'] for entry in role_details]
    if any(role_name in allowed_roles for role_name in role_names):
        context = {
            'charges' : Charges.objects.filter().order_by('name'),
            'cluster' : Cluster.objects.filter().order_by('name'),
            'division' : Division.objects.filter(status=0).order_by('name'),
            'permissions' : role_names,
        }
        return render(request, 'transaction/p_preparation.html', context)
    else:
        return render(request, 'pages/unauthorized.html')
    
# @login_required(login_url='login')
# def list_payroll(request):
#     user_details = get_user_details(request)
#     allowed_roles = ["Admin", "Incoming staff", "Validating staff"] 
#     role = RoleDetails.objects.filter(id=user_details.role_id).first()
#     if role.role_name in allowed_roles:
#         context = {
#             'charges' : Charges.objects.filter().order_by('name'),
#             'cluster' : Cluster.objects.filter().order_by('name'),
#             'division' : Division.objects.filter(status=0).order_by('name'),
#             'role_permission' : role.role_name,
#         }
#         return render(request, 'transaction/p_preparation.html', context)
#     else:
#         return render(request, 'pages/unauthorized.html')
    

@login_required(login_url='login')
@csrf_exempt
def assign_payroll(request):
    allowed_roles = ["Admin", "Incoming staff", "Validating staff", "Payroll staff", "Certified staff"] 
    user_id = request.session.get('user_id', 0)
    role_permissions = RolePermissions.objects.filter(user_id=user_id).values('role_id')
    role_details = RoleDetails.objects.filter(id__in=role_permissions).values('role_name')
    role_names = [entry['role_name'] for entry in role_details]
    if any(role_name in allowed_roles for role_name in role_names):
        context = {
            'permissions' : role_names,
        }
        return render(request, 'transaction/p_preparation.html', context)
    else:
        return render(request, 'pages/unauthorized.html')    
    
# @login_required(login_url='login')
# @csrf_exempt
# def assign_payroll(request):
#     user_details = get_user_details(request)
#     allowed_roles = ["Admin", "Incoming staff", "Validating staff"] 
#     role = RoleDetails.objects.filter(id=user_details.role_id).first()
#     if role.role_name in allowed_roles:
#         user_details = get_user_details(request)
#         allowed_roles = ["Admin", "Payroll staff"] 
#         context = {
#             'role_permission' : role.role_name,
#         }
#         return render(request, 'transaction/p_preparation.html', context)
#     else:
#         return render(request, 'pages/unauthorized.html')        
    
@login_required(login_url='login')
@csrf_exempt
def save_payroll(request):
    user_details = get_user_details(request)
    allowed_roles = ["Admin", "Incoming staff", "Validating staff"] 
    role = RoleDetails.objects.filter(id=user_details.role_id).first()
    if role.role_name in allowed_roles:
        user_details = get_user_details(request)
        allowed_roles = ["Admin", "Payroll staff"] 
        user_id = request.session.get('user_id', 0)
        formdata = request.POST.get('form_data')
        formdata_dict = parse_qs(formdata)
        cluster_name = formdata_dict.get('Cluster', [None])[0]
        dv_number = formdata_dict.get('DvNumber', [None])[0]
        div_id = formdata_dict.get('Division', [None])[0]
        selected_tev = json.loads(request.POST.get('selected_item'))
        outgoing = TevOutgoing(dv_no=dv_number,cluster=cluster_name,box_b_in=date_time.datetime.now(),user_id=user_id, division_id = div_id)
        outgoing.save()
        latest_outgoing = TevOutgoing.objects.latest('id')
        for item in selected_tev:
            tev_update = TevIncoming.objects.filter(id=item['id']).update(status_id=5)
            obj, was_created_bool = TevBridge.objects.get_or_create(
                tev_incoming_id=item['id'],
                tev_outgoing_id=latest_outgoing.id,
                purpose=item['purpose'],
                charges_id=item['charges']
            )
                
        return JsonResponse({'data': 'success'})
    else:
        return render(request, 'pages/unauthorized.html')    
    
    
@login_required(login_url='login')
def box_a(request):
    user_details = get_user_details(request)

    allowed_roles = ["Admin", "Incoming staff", "Validating staff", "Payroll staff", "Certified staff"] 
    role = RoleDetails.objects.filter(id=user_details.role_id).first()

    user_id = request.session.get('user_id', 0)
    role_permissions = RolePermissions.objects.filter(user_id=user_id).values('role_id')
    role_details = RoleDetails.objects.filter(id__in=role_permissions).values('role_name')
    role_names = [entry['role_name'] for entry in role_details]


    if any(role_name in allowed_roles for role_name in role_names):
        context = {
            'employee_list' : TevIncoming.objects.filter().order_by('first_name'),
            'permissions' : role_names,
            'dv_number' : TevOutgoing.objects.filter().order_by('id'),
            'cluster' : Cluster.objects.filter().order_by('id'),
            'division' : Division.objects.filter(status=0).order_by('id'),
            'charges' : Charges.objects.filter().order_by('name')

        }
        return render(request, 'transaction/p_printing.html', context)
    else:
        return render(request, 'pages/unauthorized.html')
    
# @login_required(login_url='login')
# def box_a(request):
#     user_details = get_user_details(request)

#     allowed_roles = ["Admin", "Incoming staff", "Validating staff"] 
#     role = RoleDetails.objects.filter(id=user_details.role_id).first()
#     if role.role_name in allowed_roles:
#         context = {
#             'employee_list' : TevIncoming.objects.filter().order_by('first_name'),
#             'role_permission' : role.role_name,
#             'dv_number' : TevOutgoing.objects.filter().order_by('id'),
#             'cluster' : Cluster.objects.filter().order_by('id'),
#             'division' : Division.objects.filter(status=0).order_by('id'),
#             'charges' : Charges.objects.filter().order_by('name')

#         }
#         return render(request, 'transaction/p_printing.html', context)
#     else:
#         return render(request, 'pages/unauthorized.html')
    

@login_required(login_url='login')
def preview_box_a(request):
    finance_database_alias = 'finance'    
    outgoing_id = request.GET.get('id')
    user_id = request.session.get('user_id', 0)


    
    year, ot_id = outgoing_id.split('/')
    year = int(year)
    outgoing_id = int(ot_id)

    if year == 2023:
        finance_database_alias = 'finance' 
    else:
        finance_database_alias = 'finance_2024' 

    results = []
    total_final_amount = 0.0
    emp_list_code = []
    emp_list_lname = []
    charges_list = []
    data_result = []
    
    userData = AuthUser.objects.filter(id=user_id)
    full_name = userData[0].first_name + ' ' + userData[0].last_name

    designation = StaffDetails.objects.filter(user_id= user_id)
    position = designation[0].position
    
    
    if outgoing_id:
        tev_incoming_ids = TevBridge.objects.filter(tev_outgoing_id=outgoing_id).values_list('tev_incoming_id', flat=True)

        query = """
            SELECT
                tev_incoming.id,
                tev_incoming.first_name,
                tev_incoming.last_name,
                tev_incoming.middle_name,
                tev_incoming.id_no,
                tev_incoming.account_no,
                tev_incoming.final_amount,
                tev_bridge.purpose,
                tev_outgoing.dv_no,
                charges.name AS name,
                charges2.name AS charges_name,
                payrolled_charges.amount AS charges_amount
            FROM
                tev_incoming
            JOIN
                tev_bridge ON tev_incoming.id = tev_bridge.tev_incoming_id
            LEFT JOIN
                tev_outgoing ON tev_bridge.tev_outgoing_id = tev_outgoing.id
            LEFT JOIN
                charges ON charges.id = tev_bridge.charges_id
            LEFT JOIN
                payrolled_charges ON payrolled_charges.incoming_id = tev_incoming.id
            LEFT JOIN
                charges AS charges2 ON payrolled_charges.charges_id = charges2.id
            WHERE
                tev_incoming.id IN %s
            ORDER BY
                tev_incoming.last_name;
        """
        total_final_amount = 0
        with connection.cursor() as cursor:
            cursor.execute(query, [tuple(tev_incoming_ids)])
            rows = cursor.fetchall()
            for row in rows:
                total_final_amount += Decimal(row[11]) if row[11] is not None else Decimal('0.0')
                data_dict = {
                    "id": row[0],
                    "first_name": row[1],
                    "last_name": row[2],
                    "middle_name": row[3],
                    "id_no": row[4],
                    "account_no": row[5],
                    "final_amount": row[6],
                    "purpose": row[7],
                    "dv_no": row[8],
                    "name": row[9],
                    "charges_name": row[10],
                    "charges_amount": row[11]
                }
                data_result.append(data_dict)
        
        outgoing = TevOutgoing.objects.filter(id=outgoing_id).values('dv_no','box_b_in','division__chief','division__c_designation','division__approval','division__ap_designation').first()
        dvno = outgoing['dv_no']

        te_lname = TevIncoming.objects.filter(id__in=tev_incoming_ids).values(
                'code',
                'first_name',
                'last_name',
                'middle_name',
                'id_no',
                'account_no',
                'final_amount',
                'tevbridge__purpose',
                'tevbridge__tev_outgoing__dv_no', 
                'tevbridge__charges__name'  
            ).order_by('last_name')
        result_count = len(te_lname)

        final_charges_amount = Decimal('0')
        charges_dict = {}

        for item in data_result:
            charges_name = item['charges_name']
            charges_amount = Decimal(item['charges_amount']) if item['charges_amount'] is not None else 0.0

            if charges_name in charges_dict:
                charges_dict[charges_name] += charges_amount
            else:
                charges_dict[charges_name] = charges_amount

        charges_list = [{'charges': name, 'final_amount': amount} for name, amount in charges_dict.items()]

        for item in te_lname:
            fullname = item['last_name'] + ', '+ item['first_name']
            list_lname = {
                    "code": item['code'],
                    "name": fullname,
                    "id_no": item['id_no'],
                    "account_no": item['account_no'],
                    "final_amount": item['final_amount'],
                    "purpose": item['tevbridge__purpose'],
                    "dv_no": item['tevbridge__tev_outgoing__dv_no'],
                    "charges": item['tevbridge__charges__name'],
                }
            emp_list_lname.append(list_lname)
            

        
        
        box_b_in  = outgoing['box_b_in']
        
        query = """
            SELECT dv_no,dv_date,payee, modepayment
            FROM transactions
            WHERE dv_no = %s
        """

        with connections[finance_database_alias].cursor() as cursor:
            cursor.execute(query, (dvno,))
            rows = cursor.fetchall()
            for row in rows:
                result_dict = {
                    "dv_no": row[0],
                    "dv_date": row[1],
                    "payee": row[2],
                    "modepayment": row[3]
                }
                results.append(result_dict)
                
        designation_result = {
            "chief":outgoing['division__chief'],
            "c_designation":outgoing['division__c_designation'],
            "approval":outgoing['division__approval'],
            "ap_designation":outgoing['division__ap_designation']
        }

        context = {
            'data' : data_result,
            'dv_number':dvno,
            'charges_list':charges_list,
            'payroll_date':box_b_in,
            'total_amount':total_final_amount,
            'total_count':'',
            'finance':results,
            'details':designation_result,
            'emp_list_lname':'',
            'user' : full_name  ,
            'position' : position
        }
        
        return render(request, 'transaction/preview_print.html', context)
    else:
        return render(request, 'error_template.html', {'error_message': "Missing or invalid 'id' parameter"})
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
def employee_dv(request):
    user_details = get_user_details(request)
    allowed_roles = ["Admin", "Incoming staff", "Validating staff"] 
    dvno = ''
    total_amount = 0       
    charges_list = []
    idd = request.GET.get('dv_id')
    dv_no = TevOutgoing.objects.filter(id=idd).values('dv_no','id').first()

    charges = Charges.objects.filter().order_by('name')
    for charge in charges:
        charge_data = {
            'id': charge.id,
            'name': charge.name
        }
        charges_list.append(charge_data)
    
    if dv_no is not None:
        dvno = dv_no['dv_no']
    query = """ 
        SELECT 
            ti.id, 
            code, 
            first_name, 
            middle_name, 
            last_name,
            id_no,
            account_no, 
            final_amount, 
            MAX(tb.purpose) AS purpose,  -- Using an aggregate function
            dv_no, 
            cl.name as cluster, 
            GROUP_CONCAT(t3.name SEPARATOR ', ') AS multiple_charges 
        FROM tev_incoming AS ti 
        LEFT JOIN tev_bridge AS tb ON tb.tev_incoming_id = ti.id
        LEFT JOIN tev_outgoing AS t_o ON t_o.id = tb.tev_outgoing_id
        LEFT JOIN cluster AS cl ON cl.id = t_o.cluster
        LEFT JOIN payrolled_charges AS t2 ON t2.incoming_id = ti.id
        LEFT JOIN charges AS t3 ON t3.id = t2.charges_id
        WHERE ti.status_id IN (1, 2, 4, 5, 6, 7) AND dv_no = %s 
        GROUP BY ti.id, code, first_name, middle_name, last_name, id_no, account_no, final_amount, dv_no, cl.name
        ORDER BY ti.updated_at DESC;  
    """

    with connection.cursor() as cursor:
        cursor.execute(query, (dvno,))
        results = cursor.fetchall()
        
    column_names = ['id','code', 'first_name','middle_name', 'last_name','id_no','account_no', 'final_amount','purpose','dv_no','cluster','multiple_charges']
    data_result = []

    for finance_row in results:
        finance_dict = dict(zip(column_names, finance_row))
        data_result.append(finance_dict)

    data = []  
    

    for row in data_result:
        first_name = row['first_name'] if row['first_name'] else ''
        middle_name = row['middle_name'] if row['middle_name'] else ''
        last_name = row['last_name'] if row['last_name'] else ''
        emp_fullname = f"{first_name} {middle_name} {last_name}".strip()
        
        final_amount_str = row['final_amount']
        final_amount = Decimal(final_amount_str).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        

        total_amount += final_amount
        item = {
            'id': row['id'],
            'code': row['code'],
            'name': emp_fullname,
            'id_no': row['id_no'],
            'account_no': row['account_no'],
            'final_amount': final_amount,
            'purpose': row['purpose'],
            'dv_no': row['dv_no'],
            'cluster':row['cluster'],
            'multiple_charges':row['multiple_charges'],
            'total':final_amount,
        }
        data.append(item)
    payrolled_list = serialize('json', TevIncoming.objects.filter(status_id=4).order_by('first_name'))

                    
    total = len(data)  
 
    response = {
        'data': data,
        'charges': charges_list,
        'dv_number':dv_no['dv_no'],
        'outgoing_id':dv_no['id'],
        'payrolled_list': payrolled_list,
        'recordsTotal': total,
        'recordsFiltered': total
    }
    return JsonResponse(response)

@csrf_exempt
def multiple_charges_details(request):
    pp_id = request.POST.get('payroll_id')
    data = []
    charges = PayrolledCharges.objects.filter(incoming_id=pp_id)
    incoming_amount= TevIncoming.objects.filter(id=pp_id).first()
    amount = round(incoming_amount.final_amount, 2)

    full_name = incoming_amount.first_name + " " + incoming_amount.middle_name + " " + incoming_amount.last_name

    for charge in charges:
        amount_ = Decimal(charge.amount).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        amount_ = int(amount_)
        charge_data = {
            'id': charge.id,
            'amount': amount_,
            'charges_id': charge.charges_id,
            'incoming_id': charge.incoming_id
        }
        data.append(charge_data)
    response = {
        'data': data,
        'amount' : amount,
        'full_name' : full_name
    }
    return JsonResponse(response)

def payroll_load(request):  

    FIdNumber= request.GET.get('FIdNumber')
    FTransactionCode = request.GET.get('FTransactionCode')
    FDateTravel= request.GET.get('FDateTravel') 
    FIncomingIn= request.GET.get('FIncomingIn')
    FFinalAmount= request.GET.get('FFinalAmount')
    FAdvancedFilter =  request.GET.get('FAdvancedFilter')
    EmployeeList = request.GET.getlist('EmployeeList[]')

    _search = request.GET.get('search[value]')
    _order_dir = request.GET.get('order[0][dir]')
    _order_dash = '-' if _order_dir == 'desc' else ''

    search_fields = ['code', 'first_name', 'last_name'] 
    filter_conditions = Q()

    for field in search_fields:
        filter_conditions |= Q(**{f'{field}__icontains': _search})

    if FAdvancedFilter:
        def dictfetchall(cursor):
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

        # query = """
        #     SELECT * FROM `tev_incoming` WHERE status_id = 4
        # """
        query = """
            SELECT t1.*,GROUP_CONCAT(t3.name SEPARATOR ', ') AS multiple_charges 
            FROM `tev_incoming` t1 
            LEFT JOIN payrolled_charges AS t2 ON t2.incoming_id = t1.id
            LEFT JOIN charges AS t3 ON t3.id = t2.charges_id
            WHERE t1.status_id = 4
        """

        params = []

        if FTransactionCode:
            query += " AND code = %s"
            params.append(FTransactionCode)

        if FIdNumber:
            query += " AND id_no = %s"
            params.append(FIdNumber)

        if FDateTravel:
            query += " AND date_travel LIKE %s"
            params.append(f'%{FDateTravel}%')

        if FFinalAmount:
            query += " AND final_amount = %s"
            params.append(FFinalAmount)

        if FIncomingIn:
            query += " AND incoming_in LIKE %s"
            params.append(f'%{FIncomingIn}%')

        if EmployeeList:
            placeholders = ', '.join(['%s' for _ in range(len(EmployeeList))])
            query += f" AND id_no IN ({placeholders})"
            params.extend(EmployeeList)
        
        query += "GROUP BY t1.id ORDER BY t1.incoming_out DESC;"

        with connection.cursor() as cursor:
            cursor.execute(query, params)
            results = dictfetchall(cursor)

            print (results)

    
    elif _search:
        with connection.cursor() as cursor:
            query = """
                SELECT t1.*, GROUP_CONCAT(t3.name SEPARATOR ', ') AS multiple_charges, t1.user_id
                FROM `tev_incoming` t1 
                LEFT JOIN payrolled_charges AS t2 ON t2.incoming_id = t1.id
                LEFT JOIN charges AS t3 ON t3.id = t2.charges_id
                WHERE t1.status_id = 4
                AND (
                    t1.code LIKE %s
                    OR t1.first_name LIKE %s
                )
                GROUP BY t1.id ORDER BY t1.incoming_out DESC;
            """
            cursor.execute(query, [f'%{_search}%', f'%{_search}%'])
            columns = [col[0] for col in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
    else:
        query = """
            SELECT t1.*,GROUP_CONCAT(t3.name SEPARATOR ', ') AS multiple_charges 
            FROM `tev_incoming` t1 
            LEFT JOIN payrolled_charges AS t2 ON t2.incoming_id = t1.id
            LEFT JOIN charges AS t3 ON t3.id = t2.charges_id
            WHERE t1.status_id = 4 GROUP BY t1.id ORDER BY t1.incoming_out DESC;
        """
        with connection.cursor() as cursor:
            cursor.execute(query)
            columns = [col[0] for col in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    
    # total = item_data.count()
    total = len(results)

    _start = request.GET.get('start')
    _length = request.GET.get('length')
    if _start and _length:
        start = int(_start)
        length = int(_length)
        page = math.ceil(start / length) + 1
        per_page = length
        item_data = results[start:start + length]

    data = []

    for item in results: 
        userData = AuthUser.objects.filter(id=item['user_id'])
        
        full_name = userData[0].first_name + ' ' + userData[0].last_name
        
        fname = item['first_name'] if item['first_name'] else ''
        mname = item['middle_name'] if item['middle_name'] else ''
        lname = item['last_name'] if item['last_name'] else ''
        emp_fullname = f"{fname} {mname} {lname}".strip()

        item = {
            'id': item['id'],
            'code': item['code'],
            'name': emp_fullname,
            'middle_name': item['middle_name'],
            'last_name': item['last_name'],
            'date_travel': item['date_travel'],
            'id_no': item['id_no'],
            'original_amount': item['original_amount'],
            'final_amount': item['final_amount'],
            'incoming_in': item['incoming_in'],
            'incoming_out': item['incoming_out'],
            'slashed_out': item['incoming_out'],
            'remarks': item['remarks'],
            'status': item['status_id'],
            'm_charges': item['multiple_charges'],
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


@csrf_exempt
def box_load(request):
    adv_filter = request.GET.get('FAdvancedFilter')

    _search = request.GET.get('search[value]')
    _order_dir = request.GET.get('order[0][dir]')
    _order_dash = '-' if _order_dir == 'desc' else ''
    _order_col_num = request.GET.get('order[0][column]')
    year = request.GET.get('DpYear')
    print("owowooooo111o2")
    print(year)
    year = int(year)
    last_two_digits = year % 100
    print(last_two_digits)

    dv_no_string = f"{last_two_digits:02d}-"


    # print("Last two digits: %d" % last_two_digits)
     
    search_fields = ['dv_no', 'division__name', 'status__name'] 
    filter_conditions = Q()

    for field in search_fields:
        filter_conditions |= Q(**{f'{field}__icontains': _search})

    if adv_filter:

        FCluster = request.GET.get('FCluster')
        FDivision = request.GET.get('FDivision')
        FBoxIn = request.GET.get('FBoxIn')
        FBoxOut = request.GET.get('FBoxOut')
        BoxStatus = request.GET.get('BoxStatus')
        dv_list = request.GET.getlist('ListDv[]')

        # item_data = TevOutgoing.objects.all(dv_no = dv_no_string)
        item_data = TevOutgoing.objects.filter(dv_no__startswith=dv_no_string)

        if FCluster:
            item_data = item_data.filter(cluster=FCluster)

        if FDivision:
            item_data = item_data.filter(division_id = FDivision)

        if FBoxIn:
            item_data = item_data.filter(box_b_in__icontains=FBoxIn)

        if FBoxOut:
            item_data = item_data.filter(box_b_out__icontains=FBoxOut)

        if BoxStatus:
            item_data = item_data.filter(status_id=BoxStatus)

        if dv_list:
            item_data = item_data.filter(id__in=dv_list)

    elif _search:
        item_data = TevOutgoing.objects.filter().filter(filter_conditions,dv_no__startswith=dv_no_string).select_related().distinct().order_by(_order_dash + 'id')
    else:
        item_data = TevOutgoing.objects.filter(dv_no__startswith=dv_no_string).select_related().distinct().order_by('-id')

    total = item_data.count()

    _start = request.GET.get('start')
    _length = request.GET.get('length')
    if _start and _length:
        start = int(_start)
        length = int(_length)
        page = math.ceil(start / length) + 1
        per_page = length
        item_data = item_data[start:start + length]

    data = []

    for item in item_data:
        userData = AuthUser.objects.filter(id=item.user_id)
        if userData.exists():
            full_name = userData[0].first_name + ' ' + userData[0].last_name
        else:
            full_name = ""
        
        userData_out = AuthUser.objects.filter(id=item.out_by)
        if userData_out.exists():
            full_name_out = userData_out[0].first_name + ' ' + userData_out[0].last_name
        else:
            full_name_out = ""

        item = {
            'id': item.id,
            'dv_no': item.dv_no,
            'cluster': item.cluster,
            'division_name': item.division.name,
            'division_chief': item.division.chief,
            'status':item.status_id,
            'box_b_in': item.box_b_in,
            'box_b_out': item.box_b_out,
            'user_id': full_name,
            'out_by': full_name_out
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


def box_emp_load(request):  
    item_data = (TevOutgoing.objects.filter().select_related().distinct().order_by('-id').reverse())
    total = item_data.count()

    _start = request.GET.get('start')
    _length = request.GET.get('length')
    if _start and _length:
        start = int(_start)
        length = int(_length)
        page = math.ceil(start / length) + 1
        per_page = length
        item_data = item_data[start:start + length]

    data = []

    for item in item_data: 
        userData = AuthUser.objects.filter(id=item.user_id)
        
        # Check if userData has results
        if userData.exists():
            full_name = userData[0].first_name + ' ' + userData[0].last_name
        else:
            full_name = ""
        
        userData_out = AuthUser.objects.filter(id=item.out_by)
        
        # Check if userData_out has results
        if userData_out.exists():
            full_name_out = userData_out[0].first_name + ' ' + userData_out[0].last_name
        else:
            full_name_out = ""

        item = {
            'id': item.id,
            'dv_no': item.dv_no,
            'cluster': item.cluster,
            'division_name': item.division.name,
            'division_chief': item.division.chief,
            'status':item.status_id,
            'box_b_in': item.box_b_in,
            'box_b_out': item.box_b_out,
            'user_id': full_name,
            'out_by': full_name_out
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
def update_status(request):
    id = request.POST.get('dv_id')
    # tev_update = TevOutgoing.objects.filter(dv_no=id).update(is_print=True)
    return JsonResponse({'data': 'success'})



@csrf_exempt
def dv_number_lib(request):
    dv_list = TevOutgoing.objects.values_list('dv_no', flat=True)
    # dv_list = list(dv_list)
    # print(dv_list)
    return JsonResponse({'data': dv_list})



@csrf_exempt
def update_box_list(request):
    total_amount = 0
    incoming_id = request.POST.get('emp_id')
    amount = request.POST.get('amount')
    purpose = request.POST.get('purpose')
    charges = request.POST.get('charges')
    dv_no = request.POST.get('dv_number')
    
    try:
        tev_incoming = TevIncoming.objects.get(id=incoming_id)
        tev_bridge = tev_incoming.tevbridge_set.first()
        if tev_bridge:
            tev_incoming.final_amount = amount
            tev_bridge.purpose = purpose
            tev_bridge.charges_id = charges
            tev_bridge.save()
            tev_incoming.save()
    except TevIncoming.DoesNotExist:
        pass
    
    query = """
        SELECT final_amount FROM tev_incoming AS ti 
        LEFT JOIN tev_bridge AS tb ON tb.tev_incoming_id = ti.id
        LEFT JOIN tev_outgoing AS t_o ON t_o.id = tb.tev_outgoing_id
        WHERE ti.status_id IN (1, 2, 4, 5, 6, 7) AND dv_no = %s    
    """

    with connection.cursor() as cursor:
        cursor.execute(query, (dv_no,))
        results = cursor.fetchall()
        
    column_names = ['final_amount']
    data_result = []

    for finance_row in results:
        finance_dict = dict(zip(column_names, finance_row))
        data_result.append(finance_dict)
        
    for row in data_result:
        final_amount = float(row['final_amount'])
        total_amount += final_amount
    
    
    response = {
        'data': 'success',
        'total_amount':total_amount
    }
    return JsonResponse(response)


@csrf_exempt
def add_multiple_charges(request):
    if request.method == 'POST':
        amount = request.POST.getlist('amount[]')
        charges_id = request.POST.getlist('charges_id[]')
        incoming_id = request.POST.get('incoming_id')
        
        PayrolledCharges.objects.filter(incoming_id=incoming_id).delete()
        for amt, ch_id in zip(amount, charges_id):
            PayrolledCharges.objects.create(
                incoming_id=incoming_id,
                amount=amt,
                charges_id=ch_id
        )
        return JsonResponse({'data': 'success'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
    
@csrf_exempt
def update_multiple_charges(request):
    if request.method == 'POST':
        amount = request.POST.getlist('amount[]')
        charges_id = request.POST.getlist('charges_id[]')
        incoming_id = request.POST.get('incoming_id')
        amt_issued = request.POST.get('amt_issued')
        TevIncoming.objects.filter(id=incoming_id).update(final_amount=amt_issued)
        PayrolledCharges.objects.filter(incoming_id=incoming_id).delete()
        for amt, ch_id in zip(amount, charges_id):
            PayrolledCharges.objects.create(
                incoming_id=incoming_id,
                amount=amt,
                charges_id=ch_id
        )
        return JsonResponse({'data': 'success'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
    
@csrf_exempt
def check_charges(request):
    if request.method == 'POST':
        incoming_id = request.POST.get('incoming_id')
        
    
        amt = TevIncoming.objects.filter(id=incoming_id).values_list('final_amount', flat=True).first()
        try:
            data_exists = PayrolledCharges.objects.filter(incoming_id=incoming_id).exists()
            return JsonResponse({'data': data_exists,'amt': amt})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
    
@csrf_exempt
def payroll_add_charges(request):
    if request.method == 'POST':
        incoming_id = request.POST.get('incoming_id')
        amt = request.POST.get('amt')
        charge_id = request.POST.get('charge_id')
        try:
            PayrolledCharges(amount=amt,charges_id=charge_id,incoming_id=incoming_id).save()
            return JsonResponse({'data': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
    
@csrf_exempt
def remove_charges(request):
    if request.method == 'POST':
        incoming_id = request.POST.get('incoming_id')
        charge_id = request.POST.get('charge_id')
        amt = request.POST.get('amt')
        try:
            PayrolledCharges.objects.filter(incoming_id=incoming_id).delete()
            PayrolledCharges(amount=amt,charges_id=charge_id,incoming_id =incoming_id).save()
            return JsonResponse({'data': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
    

@csrf_exempt
def update_purpose(request):
    if request.method == 'POST':
        te_id = request.POST.get('te_id')
        purpose = request.POST.get('value')
        try:
            TevBridge.objects.filter(tev_incoming_id=te_id).update(purpose=purpose)
            return JsonResponse({'data': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
    

@csrf_exempt
def add_dv(request):
    if request.method == 'POST':
        user_id = request.session.get('user_id', 0)
        dv_number = request.POST.get('DvNumber')
        cluster_id = request.POST.get('Cluster')
        div_id = request.POST.get('Division')
        outgoing = TevOutgoing(dv_no=dv_number,cluster=cluster_id,box_b_in=date_time.datetime.now(),user_id=user_id, division_id = div_id)
        outgoing.save()
        
        return JsonResponse({'data': 'success'})

    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
  

@csrf_exempt
def add_emp_dv(request):
    if request.method == 'POST':
        user_id = request.session.get('user_id', 0)
        tev_id = request.POST.get('tev_id')
        dv_no = request.POST.get('dv_no')
        box_b = TevIncoming.objects.filter(id=tev_id).update(status_id=6, updated_at = date_time.datetime.now())
        month_mapping = {
            '01': 'Jan', '02': 'Feb', '03': 'Mar', '04': 'Apr',
            '05': 'May', '06': 'Jun', '07': 'Jul', '08': 'Aug',
            '09': 'Sep', '10': 'Oct', '11': 'Nov', '12': 'Dec'
        }
        tev_incoming_object = TevIncoming.objects.get(id=tev_id)
        travel_dates_str = tev_incoming_object.date_travel
        travel_dates_list = travel_dates_str.split(',')
        unique_months_by_year = {}

        for date in travel_dates_list:
            parts = date.split('-')
            if len(parts) == 3:
                year = parts[2]
                month_abbr = month_mapping.get(parts[1])
                if month_abbr:
                    if year not in unique_months_by_year:
                        unique_months_by_year[year] = set()
                    unique_months_by_year[year].add(month_abbr)

        ordered_years = sorted(unique_months_by_year.keys())

        def month_order(month_abbr):
            month_mapping_order = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6, 'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}
            return month_mapping_order.get(month_abbr, 0)

        formatted_result = ', '.join([f"{', '.join(sorted(unique_months_by_year[year], key=month_order))} {year}" for year in ordered_years])
        purpose = "TE for "+ formatted_result
        outgoing_obj = TevOutgoing.objects.filter(dv_no=dv_no).first()
        outgoing_id = outgoing_obj.id

        bridge = TevBridge(purpose = purpose,charges_id = 1, tev_incoming_id = tev_id, tev_outgoing_id = outgoing_id)
        bridge.save()
        PayrolledCharges.objects.filter(incoming_id=tev_id).delete()
        return JsonResponse({'data': 'success'})

    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
  

@csrf_exempt
def retrieve_employee(request):
    dv_no_id = request.POST.get('dv_no_id')
    data = []
    dv_number = TevOutgoing.objects.filter(id=dv_no_id).first()

    list_employee = TevIncoming.objects.filter(status_id=4).order_by('first_name')

    for row in list_employee:
        date_travel_str = row.date_travel
        date_travel_list = [datetime.strptime(date_str.strip(), "%d-%m-%Y").replace(tzinfo=timezone.utc) for date_str in date_travel_str.split(',')]
        date_travel_formatted = ', '.join(date_travel.strftime("%b. %d %Y") for date_travel in date_travel_list)
        first_name = row.first_name if row.first_name else ''
        middle_name = row.middle_name if row.middle_name else ''
        last_name = row.last_name if row.last_name else ''
        final_amount = row.final_amount if row.final_amount else ''
        final_amount = ": Amount: " + f"{Decimal(final_amount):,.2f}"
        emp_fullname = f"{first_name} {middle_name} {last_name} {final_amount} : Date Travel: {date_travel_formatted}".strip()
        item = {
            'id': row.id,
            'name': emp_fullname
        }
        data.append(item)

    response = {
        'data': data,
        'dv_no' : dv_number.dv_no
    }

    return JsonResponse(response)




@csrf_exempt
def delete_box_list(request):
    incoming_id = request.POST.get('emp_id')
    dv_no = request.POST.get('dv_number')
    
    TevBridge.objects.filter(tev_incoming_id=incoming_id).delete()
    TevIncoming.objects.filter(id=incoming_id).update(status_id=4)

    response = {
        'data': 'success'
    }
    return JsonResponse(response)

@csrf_exempt
def out_box_a(request):
    out_list = request.POST.getlist('out_list[]')
    user_id = request.session.get('user_id', 0)
    
    # Convert the out_list items to integers
    out_list_int = [int(item) for item in out_list]

    
    # Update the tev_incoming table
    ids = TevBridge.objects.filter(tev_outgoing_id__in=out_list_int).values_list('tev_incoming_id', flat=True)
    
    TevIncoming.objects.filter(id__in=ids).update(status_id=6)
    
    for item_id  in out_list:
        box_b = TevOutgoing.objects.filter(id=item_id).update(status_id=6,box_b_out=date_time.datetime.now(), out_by = user_id)

    
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
def add_existing_record(request):
    fname = request.POST.get('FFirstName')
    mname = request.POST.get('FMiddleName')
    lname = request.POST.get('FLastname')
    idno = request.POST.get('FIdNumber')
    acctno = request.POST.get('FAccountNumber')
    amount = request.POST.get('FinalAmount')
    remarks = request.POST.get('FRemarks')
    purpose = request.POST.get('FPurpose')
    charges_id = request.POST.get('FCharges')
    user_id = request.session.get('user_id', 0)
    travel_date = request.POST.get('DateTravel')
    range_travel = request.POST.get('RangeTravel')
    outgoing_id = request.POST.get('FOutgoingId')
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
            Q(first_name=fname) & Q(middle_name=mname) & Q(last_name=lname) &
            Q(date_travel__contains=cleaned_date)
        ).values('date_travel')

        if results:
            duplicate_travel.append(cleaned_date)

    if duplicate_travel:
        return JsonResponse({'data': 'error', 'message': duplicate_travel})
    else:
        max_id = TevIncoming.objects.aggregate(Max('id'))['id__max']
        if max_id is not None:
            max_id += 1

        tev_add = TevIncoming(code=g_code,first_name=fname,middle_name = mname, last_name = lname, id_no = idno, account_no = acctno,date_travel = cleaned_dates,original_amount=amount,final_amount = amount,incoming_out = date_time.datetime.now(),slashed_out = date_time.datetime.now(),remarks=remarks,status_id = 5,user_id=user_id)
        tev_add.save()

        bridge = TevBridge(purpose = purpose,charges_id = charges_id, tev_incoming_id = max_id, tev_outgoing_id = outgoing_id)
        bridge.save()

        if tev_add.id:
            system_config = SystemConfiguration.objects.first()
            system_config.transaction_code = g_code
            system_config.save()
        return JsonResponse({'data': 'success', 'g_code': g_code})




@csrf_exempt
def addtevdetails(request):
    
    amount = request.POST.get('final_amount')
    remarks = request.POST.get('remarks')
    status = request.POST.get('status')
    transaction_id = request.POST.get('transaction_id')
    
    if amount =='':
        amount = 0
  
    tev_update = TevIncoming.objects.filter(id=transaction_id).update(final_amount=amount,remarks=remarks,status_id=status)

    return JsonResponse({'data': 'success'})



