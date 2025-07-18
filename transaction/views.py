from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from main.models import (AuthUser, TevIncoming, SystemConfiguration,RoleDetails, StaffDetails, Cluster, Charges, TevOutgoing, TevBridge, Division, PayrolledCharges, RolePermissions, RemarksLib, Remarks_r, LibProjectSrc)
import json 
from django.core import serializers
from datetime import datetime, timedelta
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
from decimal import Decimal, InvalidOperation
from decimal import Decimal, ROUND_HALF_UP
from django.utils import timezone
from django.db import transaction
import pytz
from django.template.defaultfilters import date
from django.db.models import CharField
from django.db.models.functions import Cast
from django.db.utils import OperationalError
from django.utils.html import strip_tags
from django.db.models import Sum
from main.database_selector import get_finance_db_alias
from main.decorators import mfa_required

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

def get_finance_connection(year):
    if year == '2023':
        return 'finance'
    elif year == '2024':
        return 'finance_2024'
    elif year == '2025':
        return 'finance_2025'
    else:
        return 'testttt'
    

@mfa_required
def list(request):
    user_id = request.session.get('user_id', 0)
    allowed_roles = ["Admin", "Incoming staff", "Validating staff"] 
    role_permissions = RolePermissions.objects.filter(user_id=user_id).values('role_id')
    role_details = RoleDetails.objects.filter(id__in=role_permissions).values('role_name')
    role_names = [entry['role_name'] for entry in role_details]

    if any(role_name in allowed_roles for role_name in role_names):
        context = {
            'role_permission' : role_names,
            'cluster' : Cluster.objects.filter().order_by('name'),
            'division' : Division.objects.filter(status=0).order_by('name'),
        }
        return render(request, 'receive/list.html', context)
    else:
        return render(request, 'pages/unauthorized.html')
    
    
@mfa_required
def list_payroll(request):
    allowed_roles = ["Admin", "Incoming staff", "Validating staff","Payroll staff", "Certified staff"] 
    user_id = request.session.get('user_id', 0)
    role_permissions = RolePermissions.objects.filter(user_id=user_id).values('role_id')
    role_details = RoleDetails.objects.filter(id__in=role_permissions).values('role_name')
    role_names = [entry['role_name'] for entry in role_details]
    if any(role_name in allowed_roles for role_name in role_names):
        context = {
            'remarks_list' : RemarksLib.objects.filter(status=1).order_by('name'),
            'charges' : Charges.objects.filter().order_by('name'),
            'cluster' : Cluster.objects.filter().order_by('name'),
            'division' : Division.objects.filter(status=0).order_by('name'),
            'permissions' : role_names,
        }
        return render(request, 'transaction/p_payroll_list.html', context)
    else:
        return render(request, 'pages/unauthorized.html')
    

@mfa_required
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
         
    
@mfa_required
@csrf_exempt
def save_payroll(request):
    allowed_roles = ["Admin", "Incoming staff", "Validating staff"] 
    user_id = request.session.get('user_id', 0)

    role_permissions = RolePermissions.objects.filter(user_id=user_id).values('role_id')
    role_details = RoleDetails.objects.filter(id__in=role_permissions).values('role_name')
    role_names = [entry['role_name'] for entry in role_details]

    # if role.role_name in allowed_roles:
    if any(role_name in allowed_roles for role_name in role_names):
        allowed_roles = ["Admin", "Payroll staff"] 
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
    
@mfa_required
def get_payees(request):
    search_term = request.GET.get('term', '').strip()  # Get search term

    with connections['libraries_isps'].cursor() as cursor:
        sql = """
            SELECT supplier_id AS payee_id, supplier_name AS payee_name
            FROM lib_supplier
            WHERE supplier_name LIKE %s
            UNION ALL
            SELECT others_payee_id AS payee_id, name AS payee_name
            FROM lib_others_payee
            WHERE name LIKE %s
            LIMIT 50
        """
        cursor.execute(sql, (f"%{search_term}%", f"%{search_term}%"))
        lib_isps = cursor.fetchall()

    payees = [{'id': row[0], 'text': row[1]} for row in lib_isps]
    
    return JsonResponse({'results': payees})

@mfa_required
def box_a(request):
    allowed_roles = ["Admin", "Incoming staff", "Validating staff", "Payroll staff", "Certified staff"] 
    user_id = request.session.get('user_id', 0)
    role_permissions = RolePermissions.objects.filter(user_id=user_id).values('role_id')
    role_details = RoleDetails.objects.filter(id__in=role_permissions).values('role_name')
    role_names = [entry['role_name'] for entry in role_details]

    with connections['libraries_isps'].cursor() as cursor:
        sql = """
            SELECT supplier_id AS payee_id, supplier_name AS payee_name, 'lib_supplier' AS source_table
            FROM lib_supplier
            UNION ALL
            SELECT others_payee_id AS payee_id, name AS payee_name, 'lib_others_payee' AS source_table
            FROM lib_others_payee
        """
        cursor.execute(sql) 
        lib_isps = cursor.fetchall()

    payees = [{'id': row[0], 'text': row[1]} for row in lib_isps]
    

    if any(role_name in allowed_roles for role_name in role_names):
        context = {
            'employee_list': TevIncoming.objects.order_by('first_name'),
            'permissions': role_names,
            'dv_number': TevOutgoing.objects.order_by('id'),
            'cluster': Cluster.objects.order_by('id'),
            'payee': payees,
            'division': Division.objects.order_by('id'),
            'charges': Charges.objects.order_by('name')
        }
        return render(request, 'transaction/p_printing.html', context)
    else:
        return render(request, 'pages/unauthorized.html')
    
@mfa_required
def outgoing_list(request):
    allowed_roles = ["Admin","Outgoing staff"] 
    user_id = request.session.get('user_id', 0)
    role_permissions = RolePermissions.objects.filter(user_id=user_id).values('role_id')
    role_details = RoleDetails.objects.filter(id__in=role_permissions).values('role_name')
    role_names = [entry['role_name'] for entry in role_details]
    if any(role_name in allowed_roles for role_name in role_names):
        context = {
            'employee_list' : TevIncoming.objects.filter().order_by('first_name'),
            'permissions' : role_names,
            'dv_number' : TevOutgoing.objects.filter(status_id__in =[6,8,9]).order_by('id'),
            'cluster' : Cluster.objects.filter().order_by('id'),
            'division' : Division.objects.filter(status=0).order_by('id'),
            'charges' : Charges.objects.filter().order_by('name')

        }
        return render(request, 'transaction/p_outgoing.html', context)
    else:
        return render(request, 'pages/unauthorized.html')
    
@mfa_required
def budget_list(request):
    allowed_roles = ["Admin","Budget staff"] 
    user_id = request.session.get('user_id', 0)
    role_permissions = RolePermissions.objects.filter(user_id=user_id).values('role_id')
    role_details = RoleDetails.objects.filter(id__in=role_permissions).values('role_name')
    role_names = [entry['role_name'] for entry in role_details]


    if any(role_name in allowed_roles for role_name in role_names):
        context = {
            'employee_list' : TevIncoming.objects.filter().order_by('first_name'),
            'permissions' : role_names,
            'dv_number' : TevOutgoing.objects.filter(status_id__in =[9,10,11]).order_by('id'),
            'cluster' : Cluster.objects.filter().order_by('id'),
            'division' : Division.objects.filter(status=0).order_by('id'),
            'charges' : Charges.objects.filter().order_by('name')

        }
        return render(request, 'transaction/p_budget.html', context)
    else:
        return render(request, 'pages/unauthorized.html')
    
@mfa_required
def journal_list(request):
    allowed_roles = ["Admin","Journal staff","Certified staff"] 
    user_id = request.session.get('user_id', 0)
    role_permissions = RolePermissions.objects.filter(user_id=user_id).values('role_id')
    role_details = RoleDetails.objects.filter(id__in=role_permissions).values('role_name')
    role_names = [entry['role_name'] for entry in role_details]
    if any(role_name in allowed_roles for role_name in role_names):
        context = {
            'employee_list' : TevIncoming.objects.filter().order_by('first_name'),
            'permissions' : role_names,
            'dv_number' : TevOutgoing.objects.filter(status_id__in =[11,12,13]).order_by('id'),
            'cluster' : Cluster.objects.filter().order_by('id'),
            'division' : Division.objects.filter(status=0).order_by('id'),
            'charges' : Charges.objects.filter().order_by('name')

        }
        return render(request, 'transaction/p_journal.html', context)
    else:
        return render(request, 'pages/unauthorized.html')
    
@mfa_required
def approval_list(request):
    allowed_roles = ["Admin","Approval staff"] 
    user_id = request.session.get('user_id', 0)
    role_permissions = RolePermissions.objects.filter(user_id=user_id).values('role_id')
    role_details = RoleDetails.objects.filter(id__in=role_permissions).values('role_name')
    role_names = [entry['role_name'] for entry in role_details]
    if any(role_name in allowed_roles for role_name in role_names):
        context = {
            'employee_list' : TevIncoming.objects.filter().order_by('first_name'),
            'permissions' : role_names,
            'dv_number' : TevOutgoing.objects.filter(status_id__in =[13,15,16]).order_by('id'),
            'cluster' : Cluster.objects.filter().order_by('id'),
            'division' : Division.objects.filter(status=0).order_by('id'),
            'charges' : Charges.objects.filter().order_by('name')

        }
        return render(request, 'transaction/p_approval.html', context)
    else:
        return render(request, 'pages/unauthorized.html')
    

@csrf_exempt
def outgoing_load(request):
    adv_filter = request.GET.get('FAdvancedFilter')
    _search = request.GET.get('search[value]')
    _order_dir = request.GET.get('order[0][dir]')
    _order_dash = '-' if _order_dir == 'desc' else ''
    year = request.GET.get('DpYear')
    year = int(year)
    last_two_digits = year % 100
    dv_no_string = f"{last_two_digits:02d}-"
    search_fields = ['dv_no', 'division__name', 'status__name'] 
    filter_conditions = Q()
    allowed_roles = ["Admin"] 
    user_id = request.session.get('user_id', 0)
    role_permissions = RolePermissions.objects.filter(user_id=user_id).values('role_id')
    role_details = RoleDetails.objects.filter(id__in=role_permissions).values('role_name')
    role_names = [entry['role_name'] for entry in role_details]
    division_id = StaffDetails.objects.filter(user_id= user_id).first().division_id
    for field in search_fields:
        filter_conditions |= Q(**{f'{field}__icontains': _search})

    if adv_filter:

        FCluster = request.GET.get('FCluster')
        FDivision = request.GET.get('FDivision')
        FBoxIn = request.GET.get('FBoxIn')
        FDateReceived = request.GET.get('FDateReceived')
        FDateForwarded = request.GET.get('FDateForwarded')
        BoxStatus = request.GET.get('BoxStatus')
        dv_list = request.GET.getlist('ListDv[]')
        if any(role_name in allowed_roles for role_name in role_names):
            item_data = TevOutgoing.objects.filter(dv_no__startswith=dv_no_string, status_id__in = [6,8,9], box_b_in__startswith=year)
            # item_data = TevOutgoing.objects.filter(status_id__in = [6,8,9], box_b_in__startswith=year)
        else:
            item_data = TevOutgoing.objects.filter(dv_no__startswith=dv_no_string, status_id__in = [6,8,9],division_id = division_id, box_b_in__startswith=year)
            # item_data = TevOutgoing.objects.filter(status_id__in = [6,8,9],division_id = division_id, box_b_in__startswith=year)

        if FCluster:
                item_data = item_data.filter(cluster=FCluster)

        if FDivision:
            item_data = item_data.filter(division_id = FDivision)

        if FBoxIn:
            item_data = item_data.filter(box_b_out__icontains=FBoxIn)
        
        if FDateReceived:
            item_data = item_data.filter(otg_d_received__icontains=FDateReceived)

        if FDateForwarded:
            item_data = item_data.filter(otg_d_forwarded__icontains=FDateForwarded)

        if BoxStatus:
            item_data = item_data.filter(status_id=BoxStatus)

        if dv_list:
            item_data = item_data.filter(id__in=dv_list)


    elif _search:
        if any(role_name in allowed_roles for role_name in role_names):
            item_data = TevOutgoing.objects.filter(filter_conditions,dv_no__startswith=dv_no_string, status_id__in = [6,8,9], box_b_in__startswith=year).select_related().distinct().order_by(_order_dash + 'id')
            # item_data = TevOutgoing.objects.filter(filter_conditions, status_id__in = [6,8,9], box_b_in__startswith=year).select_related().distinct().order_by(_order_dash + 'id')
        else:
            item_data = TevOutgoing.objects.filter(filter_conditions, status_id__in = [6,8,9],division_id = division_id, box_b_in__startswith=year).select_related().distinct().order_by(_order_dash + 'id')
    else:
        
        user = AuthUser.objects.filter(id=user_id).first()

        if any(role_name in allowed_roles for role_name in role_names) :
            item_data = TevOutgoing.objects.filter(dv_no__startswith=dv_no_string,status_id__in = [6,8,9], box_b_in__startswith="2025").select_related().distinct().order_by('-id')
            # item_data = TevOutgoing.objects.filter(status_id__in = [6,8,9], box_b_in__startswith=year).select_related().distinct().order_by('-id')
        elif user.is_staff:
            item_data = TevOutgoing.objects.filter(dv_no__startswith=dv_no_string,status_id__in = [6,8,9],division_id__in = [division_id,2,3,4,5,6,7,8,11,12,15,16], box_b_in__startswith="2025").select_related().distinct().order_by('-id')
            # item_data = TevOutgoing.objects.filter(status_id__in = [6,8,9],division_id__in = [division_id,2,3,4,5,6,7,8,11,12,15,16], box_b_in__startswith=year).select_related().distinct().order_by('-id')
        else:
            item_data = TevOutgoing.objects.filter(dv_no__startswith=dv_no_string,status_id__in = [6,8,9],division_id = division_id, box_b_in__startswith="2025").select_related().distinct().order_by('-id')
            # item_data = TevOutgoing.objects.filter(dv_no__startswith=dv_no_string,status_id__in = [6,8,9],division_id = division_id, box_b_in__startswith=year).select_related().distinct().order_by('-id')

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
        userData = AuthUser.objects.filter(id=item.otg_out_user_id)
        if userData.exists():
            full_name = userData[0].first_name + ' ' + userData[0].last_name
        else:
            full_name = ""


        userData_received = AuthUser.objects.filter(id=item.otg_r_user_id)
        if userData_received.exists():
            full_name_receiver = userData_received[0].first_name + ' ' + userData_received[0].last_name
        else:
            full_name_receiver = ""

            
        item = {
            'id': item.id,
            'dv_no': item.dv_no,
            'cluster': item.cluster,
            'division_name': item.division.name,
            'division_chief': item.division.chief,
            'status':item.status_id,
            'box_b_in': item.box_b_in,
            'box_b_out': item.box_b_out,
            'd_received': item.otg_d_received,
            'd_forwarded': item.otg_d_forwarded,
            'received_by': full_name_receiver.title(),
            'user_id': full_name.title(),
            'out_by': full_name.title()
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
def budget_load(request):
    adv_filter = request.GET.get('FAdvancedFilter')
    _search = request.GET.get('search[value]')
    _order_dir = request.GET.get('order[0][dir]')
    _order_dash = '-' if _order_dir == 'desc' else ''
    year = request.GET.get('DpYear')
    year = int(year)
    last_two_digits = year % 100
    dv_no_string = f"{last_two_digits:02d}-"
    search_fields = ['dv_no', 'division__name', 'status__name'] 
    filter_conditions = Q()

    for field in search_fields:
        filter_conditions |= Q(**{f'{field}__icontains': _search})

    if adv_filter:

        FCluster = request.GET.get('FCluster')
        FDivision = request.GET.get('FDivision')
        FBoxIn = request.GET.get('FBoxIn')
        FDateReceived = request.GET.get('FDateReceived')
        FDateForwarded = request.GET.get('FDateForwarded')
        BoxStatus = request.GET.get('BoxStatus')
        dv_list = request.GET.getlist('ListDv[]')
        item_data = TevOutgoing.objects.filter(dv_no__startswith=dv_no_string, status_id__in = [9,10,11])
        if FCluster:
            item_data = item_data.filter(cluster=FCluster)

        if FDivision:
            item_data = item_data.filter(division_id = FDivision)

        if FBoxIn:
            item_data = item_data.filter(box_b_out__icontains=FBoxIn)
        
        if FDateReceived:
            item_data = item_data.filter(b_d_received__icontains=FDateReceived)

        if FDateForwarded:
            item_data = item_data.filter(b_d_forwarded__icontains=FDateForwarded)

        if BoxStatus:
            item_data = item_data.filter(status_id=BoxStatus)

        if dv_list:
            item_data = item_data.filter(id__in=dv_list)

    elif _search:
        item_data = TevOutgoing.objects.filter(filter_conditions,dv_no__startswith=dv_no_string, status_id__in = [9,10,11]).select_related().distinct().order_by(_order_dash + 'id')
    else:
        item_data = TevOutgoing.objects.filter(dv_no__startswith=dv_no_string,status_id__in = [9,10,11]).select_related().distinct().order_by('-id')

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
        userData = AuthUser.objects.filter(id=item.b_out_user_id)
        if userData.exists():
            full_name = userData[0].first_name + ' ' + userData[0].last_name
        else:
            full_name = ""


        userData_received = AuthUser.objects.filter(id=item.b_r_user_id)
        if userData_received.exists():
            full_name_receiver = userData_received[0].first_name + ' ' + userData_received[0].last_name
        else:
            full_name_receiver = ""
        item = {
            'id': item.id,
            'dv_no': item.dv_no,
            'cluster': item.cluster,
            'division_name': item.division.name,
            'division_chief': item.division.chief,
            'status':item.status_id,
            'box_b_in': item.box_b_in,
            'box_b_out': item.otg_d_forwarded,
            'd_received': item.b_d_received,
            'd_forwarded': item.b_d_forwarded,
            'received_by': full_name_receiver.title(),
            'user_id': full_name.title(),
            'out_by': full_name.title()
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

@mfa_required
@csrf_exempt
def journal_load(request):
    adv_filter = request.GET.get('FAdvancedFilter')
    _search = request.GET.get('search[value]')
    _order_dir = request.GET.get('order[0][dir]')
    _order_dash = '-' if _order_dir == 'desc' else ''
    year = request.GET.get('DpYear')
    year = int(year)
    last_two_digits = year % 100
    dv_no_string = f"{last_two_digits:02d}-"
    search_fields = ['dv_no', 'division__name', 'status__name'] 
    filter_conditions = Q()
    for field in search_fields:
        filter_conditions |= Q(**{f'{field}__icontains': _search})

    if adv_filter:

        def dictfetchall(cursor):
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

        FCluster = request.GET.get('FCluster')
        FDivision = request.GET.get('FDivision')
        FBoxIn = request.GET.get('FBoxIn')
        FDateReceived = request.GET.get('FDateReceived')
        FDateForwarded = request.GET.get('FDateForwarded')
        BoxStatus = request.GET.get('BoxStatus')
        dv_list = request.GET.getlist('ListDv[]')
        query = """
            SELECT
                tev_outgoing.id,
                tev_outgoing.dv_no,
                tev_outgoing.cluster,
                division.name AS division,
                division.chief AS division_chief,
                tev_outgoing.status_id,
                tev_outgoing.box_b_in,
                tev_outgoing.b_d_forwarded,
                tev_outgoing.j_d_received,
                tev_outgoing.j_r_user_id,
                tev_outgoing.j_d_forwarded,
                tev_outgoing.j_out_user_id,
                COALESCE(SUM(payrolled_charges.amount), 0) AS charges_amount
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
            LEFT JOIN
                division ON division.id = tev_outgoing.division_id
            WHERE tev_outgoing.status_id IN (11,12,13) AND tev_outgoing.dv_no LIKE %s
        """
        params = [f'%{dv_no_string}%']

        if FCluster:
            query += " AND tev_outgoing.cluster = %s"
            params.append(FCluster)

        if FDivision:
            query += " AND tev_outgoing.division_id = %s"
            params.append(FDivision)

        if FBoxIn:
            query += " AND tev_outgoing.box_b_in LIKE %s"
            params.append(f'%{FBoxIn}%')

        if FDateReceived:
            query += " AND tev_outgoing.j_d_received = %s"
            params.append(FDateReceived)

        if FDateForwarded:
            query += " AND tev_outgoing.j_d_forwarded = %s"
            params.append(FDateForwarded)

        if BoxStatus:
            query += " AND tev_outgoing.status_id = %s"
            params.append(BoxStatus)

        if dv_list:
            placeholders = ', '.join(['%s' for _ in range(len(dv_list))])
            query += f" AND tev_outgoing.id IN ({placeholders})"
            params.extend(dv_list)

        query += "GROUP BY tev_outgoing.id,tev_outgoing.dv_no,tev_outgoing.cluster,tev_outgoing.division_id,tev_outgoing.status_id, tev_outgoing.box_b_in,tev_outgoing.j_d_received,tev_outgoing.j_d_forwarded,tev_outgoing.j_r_user_id,tev_outgoing.j_out_user_id ORDER BY tev_outgoing.b_d_forwarded DESC;"

        with connection.cursor() as cursor:
            cursor.execute(query, params)
            item_data = dictfetchall(cursor)

    elif _search:
        with connection.cursor() as cursor:
            query = """
                SELECT
                    tev_outgoing.id,
                    tev_outgoing.dv_no,
                    tev_outgoing.cluster,
                    division.name AS division,
                    division.chief AS division_chief,
                    tev_outgoing.status_id,
                    tev_outgoing.box_b_in,
                    tev_outgoing.b_d_forwarded,
                    tev_outgoing.j_d_received,
                    tev_outgoing.j_r_user_id,
                    tev_outgoing.j_d_forwarded,
                    tev_outgoing.j_out_user_id,
                    COALESCE(SUM(payrolled_charges.amount), 0) AS charges_amount
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
                LEFT JOIN
                        division ON division.id = tev_outgoing.division_id
                WHERE tev_outgoing.status_id IN (11,12,13)
                AND (
                    tev_outgoing.dv_no LIKE %s
                    OR division.name LIKE %s
                )
                AND tev_outgoing.dv_no LIKE %s
                GROUP BY
                    tev_outgoing.id,tev_outgoing.dv_no,tev_outgoing.cluster,tev_outgoing.division_id,tev_outgoing.status_id, tev_outgoing.box_b_in,tev_outgoing.j_d_received,tev_outgoing.j_d_forwarded,tev_outgoing.j_r_user_id,tev_outgoing.j_out_user_id
                ORDER BY
                    tev_outgoing.b_d_forwarded DESC;
            """
            cursor.execute(query, [f'%{_search}%', f'%{_search}%', f'%{dv_no_string}%'])
            columns = [col[0] for col in cursor.description]
            item_data = [dict(zip(columns, row)) for row in cursor.fetchall()]
    else:
        query = """
                SELECT
                    tev_outgoing.id,
                    tev_outgoing.dv_no,
                    tev_outgoing.cluster,
                    division.name AS division,
                    division.chief AS division_chief,
                    tev_outgoing.status_id,
                    tev_outgoing.b_d_forwarded,
                    tev_outgoing.j_d_received,
                    tev_outgoing.j_r_user_id,
                    tev_outgoing.j_d_forwarded,
                    tev_outgoing.j_out_user_id,
                    COALESCE(SUM(payrolled_charges.amount), 0) AS charges_amount
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
                LEFT JOIN
                        division ON division.id = tev_outgoing.division_id
                WHERE tev_outgoing.status_id IN (11,12,13) AND tev_outgoing.dv_no LIKE %s
                GROUP BY
                        tev_outgoing.id,tev_outgoing.dv_no,tev_outgoing.cluster,tev_outgoing.division_id,tev_outgoing.status_id, tev_outgoing.b_d_forwarded,tev_outgoing.j_d_received,tev_outgoing.j_d_forwarded,tev_outgoing.j_r_user_id,tev_outgoing.j_out_user_id
                ORDER BY
                        tev_outgoing.b_d_forwarded DESC;
        """
        params = [f'%{dv_no_string}%']
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            columns = [col[0] for col in cursor.description]
            item_data = [dict(zip(columns, row)) for row in cursor.fetchall()]

    data = []

    total = len(item_data)

    _start = request.GET.get('start')
    _length = request.GET.get('length')
    if _start and _length:
        start = int(_start)
        length = int(_length)
        page = math.ceil(start / length) + 1
        per_page = length
        item_data = item_data[start:start + length]

    for item in item_data:
        userData = AuthUser.objects.filter(id=item['j_out_user_id'])
        if userData.exists():
            full_name = userData[0].first_name + ' ' + userData[0].last_name
        else:
            full_name = ""


        userData_received = AuthUser.objects.filter(id=item['j_r_user_id'])
        if userData_received.exists():
            full_name_receiver = userData_received[0].first_name + ' ' + userData_received[0].last_name
        else:
            full_name_receiver = ""
            
        new_item = {
            'id': item['id'],
            'dv_no': item['dv_no'],
            'cluster': item['cluster'],
            'division_name': item['division'],
            'division_chief': item['division_chief'],
            'status': item['status_id'],
            'b_d_forwarded': item['b_d_forwarded'],
            'box_b_out': item['j_d_forwarded'],
            'd_received': item['j_d_received'],
            'd_forwarded': item['j_d_forwarded'],
            'amount': item['charges_amount'],
            'received_by': full_name_receiver.title(),
            'user_id': full_name.title(),
            'out_by': full_name.title()
        }

        data.append(new_item)
            
    response = {
        'data': data,
        'page': page,
        'per_page': per_page,
        'recordsTotal': total,
        'recordsFiltered': total,
    }
    return JsonResponse(response)

@mfa_required
@csrf_exempt
def approval_load(request):
    adv_filter = request.GET.get('FAdvancedFilter')
    _search = request.GET.get('search[value]')
    _order_dir = request.GET.get('order[0][dir]')
    _order_dash = '-' if _order_dir == 'desc' else ''
    year = request.GET.get('DpYear')
    year = int(year)
    last_two_digits = year % 100
    dv_no_string = f"{last_two_digits:02d}-"
    search_fields = ['dv_no', 'division__name', 'status__name'] 
    filter_conditions = Q()

    for field in search_fields:
        filter_conditions |= Q(**{f'{field}__icontains': _search})

    if adv_filter:

        FCluster = request.GET.get('FCluster')
        FDivision = request.GET.get('FDivision')
        FBoxIn = request.GET.get('FBoxIn')
        FDateReceived = request.GET.get('FDateReceived')
        FDateForwarded = request.GET.get('FDateForwarded')
        BoxStatus = request.GET.get('BoxStatus')
        dv_list = request.GET.getlist('ListDv[]')
        item_data = TevOutgoing.objects.filter(dv_no__startswith=dv_no_string, status_id__in = [13,14,15])
        if FCluster:
            item_data = item_data.filter(cluster=FCluster)

        if FDivision:
            item_data = item_data.filter(division_id = FDivision)

        if FBoxIn:
            item_data = item_data.filter(box_b_out__icontains=FBoxIn)
        
        if FDateReceived:
            item_data = item_data.filter(a_d_received__icontains=FDateReceived)

        if FDateForwarded:
            item_data = item_data.filter(a_d_forwarded__icontains=FDateForwarded)

        if BoxStatus:
            item_data = item_data.filter(status_id=BoxStatus)

        if dv_list:
            item_data = item_data.filter(id__in=dv_list)

    elif _search:
        item_data = TevOutgoing.objects.filter(filter_conditions,dv_no__startswith=dv_no_string, status_id__in = [13,14,15]).select_related().distinct().order_by(_order_dash + 'id')
    else:
        item_data = TevOutgoing.objects.filter(dv_no__startswith=dv_no_string,status_id__in = [13,14,15]).select_related().distinct().order_by('-id')

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
        userData = AuthUser.objects.filter(id=item.a_out_user_id)
        if userData.exists():
            full_name = userData[0].first_name + ' ' + userData[0].last_name
        else:
            full_name = ""


        userData_received = AuthUser.objects.filter(id=item.a_r_user_id)
        if userData_received.exists():
            full_name_receiver = userData_received[0].first_name + ' ' + userData_received[0].last_name
        else:
            full_name_receiver = ""
        item = {
            'id': item.id,
            'dv_no': item.dv_no,
            'cluster': item.cluster,
            'division_name': item.division.name,
            'division_chief': item.division.chief,
            'status':item.status_id,
            'box_b_in': item.box_b_in,
            'j_d_forwarded': item.j_d_forwarded,
            'd_received': item.a_d_received,
            'd_forwarded': item.a_d_forwarded,
            'received_by': full_name_receiver.title(),
            'user_id': full_name.title(),
            'out_by': full_name.title()
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

    
@mfa_required
def preview_box_a(request):   
    outgoing_id = request.GET.get('id')
    user_id = request.session.get('user_id', 0)

    results = []
    total_final_amount = 0.0
    emp_list_lname = []
    charges_list = []
    data_result = []

    year, ot_id = outgoing_id.split('/')
    year = int(year)
    outgoing_id = int(ot_id)

    finance_database_alias = get_finance_db_alias(year)
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

        if not tev_incoming_ids:
            return render(request, 'pages/not_found.html', {'message': "No Travel assigned on this DV!",'text': "You must assign at least one travel to this DV to view the data" })
        with connection.cursor() as cursor:
            cursor.execute(query, [tuple(tev_incoming_ids)])
            rows = cursor.fetchall()
            for row in rows:
                if row[11] == None:

                    return render(request, 'pages/not_found.html', {'message': "There was a travel record with no assigned charges!",'text': "You must assign charges under this DV"})
                else:
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
        
        outgoing = TevOutgoing.objects.filter(id=outgoing_id).values('dv_no','box_b_in','division__acronym','division__chief','division__c_designation','division__approval','division__ap_designation','division__section_head','division__sh_designation').first()
        dvno = outgoing['dv_no']
        div_acronym = outgoing['division__acronym']
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
            "ap_designation":outgoing['division__ap_designation'],
            "section_head":outgoing['division__section_head'],
            "sh_designation":outgoing['division__sh_designation']
        }

        context = {
            'data' : data_result,
            'dv_number':dvno,
            'acronym':div_acronym,
            'charges_list':charges_list,
            'payroll_date':box_b_in,
            'total_amount':total_final_amount,
            'total_count':'',
            'finance':results,
            'details':designation_result,
            'emp_list_lname':'',
            'user' : full_name  ,
            'position' : position,
            'date_now': timezone.now().date().strftime('%m/%d/%Y'),
        }

        return render(request, 'transaction/preview_print.html', context)
    else:
        return render(request, 'error_template.html', {'error_message': "Missing or invalid 'id' parameter"})
    


@mfa_required
def rd_preview_print(request):
    data = TevIncoming.objects.filter(status=16).order_by('last_name')
    data_result = []

    for item in data:
        date_travel_list = item.date_travel.split(',')
        formatted_dates = []
        for date_str in date_travel_list:
            date_obj = datetime.strptime(date_str.strip(), "%d-%m-%Y")
            formatted_date = date_obj.strftime("%b. %d, %Y")
            formatted_dates.append(formatted_date)
        formatted_date_travel = ', '.join(formatted_dates)

        remarks_qs = Remarks_r.objects.filter(incoming_id=item.id)
        formatted_remarks = []
        for remark in remarks_qs:
            remark_name = f"<u><strong>{remark.remarks_lib.name}</strong></u>"
            if remark.date:
                formatted_remarks.append(f"{remark_name} - {remark.date.strftime('%B %d, %Y')}")
            else:
                formatted_remarks.append(remark_name)
        remarks = "; ".join(formatted_remarks)

        data_dict = {
            "id": item.id,
            "first_name": item.first_name.upper() if item.first_name else "",  
            "middle_name": item.middle_name.upper() if item.middle_name else "",  
            "last_name": item.last_name.upper() if item.last_name else "", 
            "id_no": item.id_no,
            "original_amount": item.original_amount,
            "final_amount": item.final_amount,
            "date_travel": formatted_date_travel,
            "remarks": remarks.upper(),
            "division": item.division.upper() if item.division else "",
            "date_compiled": item.date_reviewed.strftime('%B %d, %Y').upper() if item.date_reviewed else "" 
        }

        data_result.append(data_dict)

    context = {
        'data': data_result,
        'date_now': timezone.now().date().strftime('%B %d, %Y').upper() 
    }
    
    return render(request, 'receive/rd_preview_print.html', context)

@mfa_required
def checking(request):
    allowed_roles = ["Admin", "Incoming staff", "Validating staff"] 
    
    user_id = request.session.get('user_id', 0)
    role_permissions = RolePermissions.objects.filter(user_id=user_id).values('role_id')
    role_details = RoleDetails.objects.filter(id__in=role_permissions).values('role_name')
    role_names = [entry['role_name'] for entry in role_details]
    if any(role_name in allowed_roles for role_name in role_names):
        context = {
            'employee_list' : TevIncoming.objects.filter().order_by('first_name'),
            'role_permission' : role_names,
        }
        return render(request, 'receive/checking.html', context)
    else:
        return render(request, 'pages/unauthorized.html')
    
@mfa_required
@csrf_exempt
def employee_dv(request):
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
            MAX(tb.purpose) AS purpose,  
            dv_no, 
            cl.name as cluster, 
            GROUP_CONCAT(t3.name SEPARATOR ', ') AS multiple_charges 
        FROM tev_incoming AS ti 
        LEFT JOIN tev_bridge AS tb ON tb.tev_incoming_id = ti.id
        LEFT JOIN tev_outgoing AS t_o ON t_o.id = tb.tev_outgoing_id
        LEFT JOIN cluster AS cl ON cl.id = t_o.cluster
        LEFT JOIN payrolled_charges AS t2 ON t2.incoming_id = ti.id
        LEFT JOIN charges AS t3 ON t3.id = t2.charges_id
        WHERE ti.status_id IN (1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16) AND dv_no = %s 
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
        'total':total_amount,
        'payrolled_list': payrolled_list,
        'recordsTotal': total,
        'recordsFiltered': total
    }
    return JsonResponse(response)


@mfa_required
@csrf_exempt
def employee_journal(request):
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
            ti.status_id,
            MAX(tb.purpose) AS purpose,
            GROUP_CONCAT(t3.name SEPARATOR ', ') AS multiple_charges 
        FROM tev_incoming AS ti 
        LEFT JOIN tev_bridge AS tb ON tb.tev_incoming_id = ti.id
        LEFT JOIN tev_outgoing AS t_o ON t_o.id = tb.tev_outgoing_id
        LEFT JOIN cluster AS cl ON cl.id = t_o.cluster
        LEFT JOIN payrolled_charges AS t2 ON t2.incoming_id = ti.id
        LEFT JOIN charges AS t3 ON t3.id = t2.charges_id
        WHERE ti.status_id IN (11,12,13) AND t_o.dv_no = %s
        GROUP BY ti.id, code, first_name, middle_name, last_name, id_no, account_no, final_amount, cl.name, t_o.dv_no
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

    for row in results:
        first_name = row[2] if row[2] else ''  
        middle_name = row[3] if row[3] else '' 
        last_name = row[4] if row[4] else '' 
        emp_fullname = f"{first_name} {middle_name} {last_name}".strip()

        final_amount_str = row[7] 
        final_amount = Decimal(final_amount_str).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        total_amount += final_amount
        item = {
            'id': row[0],  
            'code': row[1], 
            'name': emp_fullname,
            'id_no': row[5],
            'account_no': row[6], 
            'final_amount': final_amount,
            'status': row[8], 
            'purpose': row[9], 
            'multiple_charges': row[10],
            'total': final_amount,
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

@mfa_required
@csrf_exempt
def multiple_charges_details(request):
    pp_id = request.POST.get('payroll_id')
    amt = request.POST.get('amt')
    dv_number = request.POST.get('payroll_id')
    year = request.POST.get('year_now')

    finance_connection = get_finance_connection(year)
    
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

@mfa_required
def payroll_load(request):  

    FIdNumber= request.GET.get('FIdNumber')
    FTransactionCode = request.GET.get('FTransactionCode')
    FDateTravel= request.GET.get('FDateTravel') 
    FIncomingIn= request.GET.get('FIncomingIn')
    FFinalAmount= request.GET.get('FFinalAmount')
    FAdvancedFilter =  request.GET.get('FAdvancedFilter')
    EmployeeList = request.GET.getlist('EmployeeList[]')
    year = request.GET.get('DpYear')

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
        query = """
            SELECT t1.* FROM `tev_incoming` t1 
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

        query += " AND date_travel LIKE %s"
        params.append(f'%{year}%')
        
        query += "GROUP BY t1.id ORDER BY t1.incoming_out DESC;"

        with connection.cursor() as cursor:
            cursor.execute(query, params)
            results = dictfetchall(cursor)

    elif _search:
        with connection.cursor() as cursor:
            query = """
                SELECT t1.* FROM `tev_incoming` t1 
                WHERE t1.status_id = 4
                AND (
                    t1.code LIKE %s
                    OR t1.first_name LIKE %s
                    OR t1.last_name LIKE %s
                    OR t1.id_no LIKE %s
                )
                AND date_travel LIKE %s
                GROUP BY t1.id ORDER BY t1.incoming_out DESC;
            """
            cursor.execute(query, [f'%{_search}%', f'%{_search}%', f'%{_search}%', f'%{_search}%', f'%{year}%'])
            columns = [col[0] for col in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
    else:
        query = """
            SELECT t1.* FROM `tev_incoming` t1
            WHERE t1.status_id = 4 
            AND date_travel LIKE %s
            GROUP BY t1.id ORDER BY t1.incoming_out DESC;
        """
        with connection.cursor() as cursor:
            cursor.execute(query, [f'%{year}%'])
            # cursor.execute(query)
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
        item_data = results[start:start + length]

    data = []

    for item in results: 
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
            'status': item['status_id']
         
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

@mfa_required
def payroll_list_load(request):
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
            'date_travel': item['date_travel'],
            'final_amount': item['final_amount'],
            'incoming_in': item['incoming_in'],
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

@mfa_required
@csrf_exempt
def box_load(request):
    adv_filter = request.GET.get('FAdvancedFilter')
    _search = request.GET.get('search[value]')
    _order_dir = request.GET.get('order[0][dir]')
    _order_dash = '-' if _order_dir == 'desc' else ''
    _order_col_num = request.GET.get('order[0][column]')
    year = request.GET.get('DpYear')

    year = int(year)
    last_two_digits = year % 100
    dv_no_string = f"{last_two_digits:02d}-"
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
        item_data = TevOutgoing.objects.filter(dv_no__startswith=dv_no_string,status_id__in = [5,6,8,9,10,11])


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
        item_data = TevOutgoing.objects.filter().filter(filter_conditions,dv_no__startswith=dv_no_string,status_id__in = [5,6,8,9,10,11]).select_related().distinct().order_by(_order_dash + 'id')
        # item_data = TevOutgoing.objects.filter().filter(filter_conditions,box_b_in__year=year,status_id__in = [5,6,8,9,10,11]).select_related().distinct().order_by(_order_dash + 'id')
    else:
        # item_data = TevOutgoing.objects.filter(box_b_in__year=year,status_id__in = [5,6,8,9,10,11]).select_related().distinct().order_by('-id')
        item_data = TevOutgoing.objects.filter(dv_no__startswith=dv_no_string,status_id__in = [5,6,8,9,10,11]).select_related().distinct().order_by('-id')
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

@mfa_required
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

@mfa_required
def item_edit(request):
    id = request.GET.get('id')
    items = TevIncoming.objects.get(pk=id)
    data = serialize("json", [items])
    return HttpResponse(data, content_type="application/json")

@mfa_required
@csrf_exempt
def update_status(request):
    return JsonResponse({'data': 'success'})


@mfa_required
@csrf_exempt
def dv_number_lib(request):
    dv_list = TevOutgoing.objects.values_list('dv_no', flat=True)
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

@mfa_required
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

@mfa_required
@csrf_exempt
def update_multiple_charges(request):
    if request.method == 'POST':

        amount_list = request.POST.getlist('amount[]') 
        charges_id = request.POST.getlist('charges_id[]')
        incoming_id = request.POST.get('incoming_id')
        amt_issued = request.POST.get('amt_issued')
        dv_number = request.POST.get('dv_number')
        year = request.POST.get('year_now')
        finance_connection = get_finance_connection(year)
        charges_total = PayrolledCharges.objects.filter(incoming_id=incoming_id).aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
        amt_issued_dec = Decimal(amt_issued) 
        amt_dec = amt_issued_dec - charges_total 

        if amt_dec != Decimal('0'):
            with transaction.atomic():
                with connections[finance_connection].cursor() as cursor:
                    cursor.execute("""
                        UPDATE transactions
                        SET amt_certified = amt_certified + %s
                        WHERE dv_no = %s
                    """, [amt_dec, dv_number])

        TevIncoming.objects.filter(id=incoming_id).update(final_amount=amt_issued)
        PayrolledCharges.objects.filter(incoming_id=incoming_id).delete()

        for amt, ch_id in zip(amount_list, charges_id):
            PayrolledCharges.objects.create(
                incoming_id=incoming_id,
                amount=amt,
                charges_id=ch_id
            )

        return JsonResponse({'data': 'success'})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@mfa_required    
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
 
@mfa_required
@csrf_exempt
def payroll_add_charges(request):
    if request.method == 'POST':
        incoming_id = request.POST.get('incoming_id')
        amt = request.POST.get('amt')
        charge_id = request.POST.get('charge_id')
        dv_number = request.POST.get('dv_number')
        year = request.POST.get('year_now')

        if not amt:
            return JsonResponse({'data': 'Amount is required'}, status=400)

        try:
            amt = float(amt)  # Convert amt to float for calculations
        except ValueError:
            return JsonResponse({'data': 'Invalid amount'}, status=400)
        
        finance_connection = get_finance_connection(year)  

        try:
            with transaction.atomic():
                # Insert into PayrolledCharges table
                PayrolledCharges.objects.create(amount=amt, charges_id=charge_id, incoming_id=incoming_id)

                # Update amt_certified in transactions table
                with connections[finance_connection].cursor() as cursor:
                    cursor.execute("""
                        UPDATE transactions
                        SET amt_certified = amt_certified + %s
                        WHERE dv_no = %s
                    """, [amt, dv_number])

            return JsonResponse({'data': 'success'})

        except Exception as e:
            return JsonResponse({'data': str(e)}, status=500)

    return JsonResponse({'data': 'Invalid request method'}, status=400)

    
@mfa_required   
@csrf_exempt
def remove_charges(request):
    if request.method == 'POST':
        incoming_id = request.POST.get('incoming_id')
        charge_id = request.POST.get('charge_id')
        amt = request.POST.get('amt')
        year = request.POST.get('year_now')
        try:
            PayrolledCharges.objects.filter(incoming_id=incoming_id).delete()
            PayrolledCharges(amount=amt,charges_id=charge_id,incoming_id =incoming_id).save()
            return JsonResponse({'data': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
    
@mfa_required
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

@mfa_required   
@csrf_exempt
def transmittal_details(request):
    data_result = []
    year = request.GET.get('year')
    selected_dv = request.GET.getlist('selectedDv')
    dv_no_query = TevOutgoing.objects.filter(id__in=selected_dv).values_list("dv_no", flat=True)
    dv_no_tuple = tuple(dv_no_query)
    # Determine the finance database connection based on the year
    finance_connection_map = {
        '2023': 'finance',
        '2024': 'finance_2024',
        '2025': 'finance_2025',
    }
    finance_connection = finance_connection_map.get(year)

    if not finance_connection:
        return render(request, 'pages/not_found.html', {
            'message': "Invalid Year",
            'text': "The selected year is not supported."
        })
    # Query default_db (port 3306)
    with connections['default'].cursor() as default_cursor:
        default_query = """
            SELECT
                tev_outgoing.dv_no,
                COALESCE(SUM(payrolled_charges.amount), 0) AS charges_amount
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
            WHERE
                tev_outgoing.dv_no IN %s
            GROUP BY
                tev_outgoing.dv_no
            ORDER BY
                tev_outgoing.dv_no;
        """
        default_cursor.execute(default_query, [dv_no_tuple])
        default_results = {row[0]: row[1] for row in default_cursor.fetchall()}  # Map dv_no -> charges_amount
    # Query finance_db (port 3307)
    with connections[finance_connection].cursor() as finance_cursor:
        finance_query = """
            SELECT
                dv_no,
                payee,
                modepayment
            FROM
                transactions
            WHERE
                dv_no IN %s
            ORDER BY
                dv_no;
        """
        finance_cursor.execute(finance_query, [dv_no_tuple])
        finance_results = {row[0]: {'payee': row[1], 'modepayment': row[2]} for row in finance_cursor.fetchall()}  # Map dv_no -> details

    # Merge results
    if not finance_results:
        return render(request, 'pages/not_found.html', {
            'message': "DV not found",
            'text': f"No dvs found that match in INFIMOS {finance_connection}"
        })
    
    elif any(charges_amount == 0 or charges_amount is None for charges_amount in default_results.values()):
        for dv_no, charges_amount in default_results.items():
            if charges_amount == 0 or charges_amount is None:
                return render(request, 'pages/not_found.html', {'message': "Invalid Amount Charges",'text': "There is travel with no assigned Charges!" })
            
    for dv_no, charges_amount in default_results.items():
        if dv_no in finance_results: 
            finance_data = finance_results[dv_no]
            data_dict = {
                "dv_no": dv_no,
                "payee": finance_data['payee'],
                "modepayment": finance_data['modepayment'],
                "date": datetime.now().strftime("%Y-%m-%d"),
                "charges_amount": charges_amount
            }
            data_result.append(data_dict)
        else:
            print(f"Warning: DV No: {dv_no} missing in {finance_connection}.")
    if not data_result:
        return render(request, 'pages/not_found.html', {'message': "Review Travel First",'text': "You must assign at least one travel to this DV to view the data" })
    
    elif any(d['charges_amount'] == 0 or d['charges_amount'] is None for d in data_result):
        return render(request, 'pages/not_found.html', {
            'message': "Invalid Amount Charges",
            'text': "There is travel with no assigned Charges!"
        })

    response = {'data': data_result}
    return render(request, 'transaction/preview_transmittal.html', response)

@mfa_required
@csrf_exempt
def add_dv(request):
    if request.method == 'POST':
        user_id = request.session.get('user_id', 0)
        cluster_id = request.POST.get('Cluster')
        project_source = request.POST.get('ProjectSource')
        purpose = request.POST.get('Purpose')
        year = request.POST.get('DpYear')
        div_id = request.POST.get('Division')
        payee_id = request.POST.get('PayeeId')
        payee_name = request.POST.get('PayeeName')
        source_table = request.POST.get('SourceTable')

        formatted_date_now = datetime.now().strftime('%Y-%m-%d')

        user = AuthUser.objects.filter(id=user_id).first()
        full_name = f"{user.first_name} {user.last_name}" if user else "NULL"
        user_name = f"{user.username}" if user else "NULL"
        finance_connection = get_finance_connection(year)
        finance_query = """
            SELECT _value
            FROM _config
            WHERE _handler = "GENERATE_DV"
            LIMIT 1
        """

        with connections[finance_connection].cursor() as cursor:
            cursor.execute(finance_query)
            dv_result = cursor.fetchone()
        
        _value = dv_result[0] if dv_result else None

        if _value:
            prefix, number = _value.rsplit('-', 1)
            yy, mm = prefix.split('-')
            current_month = f"{datetime.now().month:02d}"
            
            if mm != current_month:
                mm = current_month
            
            old_number = str(int(number)).zfill(4)
            new_number = str(int(number) + 1).zfill(4)
            generated_dv = f"{yy}-{mm}-{old_number}" 
            new_generated_dv = f"{yy}-{mm}-{new_number}" 
            dv_yr = yy
            dv_month = mm
            dv_sequence = old_number
            insert_query = """
                INSERT INTO transactions (dv_no, dv_date, payee, modepayment, amt_certified, approval_date, recon, alobs_item, prov_id, mun_id, brgy_id, userlog, scaned_voucher, submit_coa, accountable, projectsrc_id, payee_table_name, payee_id, is_active)  
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            """

            update_query = """
                UPDATE _config
                SET _value = %s
                WHERE _handler = "GENERATE_DV"
            """

            outgoing = TevOutgoing(dv_no=generated_dv, cluster=cluster_id, box_b_in=datetime.now(), user_id=user_id, division_id=div_id)
            outgoing.save()

            with connections[finance_connection].cursor() as cursor:
                cursor.execute(insert_query, (generated_dv, formatted_date_now, payee_name, purpose, 0, None, 0, 0, 0, 0, 0, user_name, None, None, full_name, project_source, source_table, payee_id, 0))
                cursor.execute("SELECT LAST_INSERT_ID()")
                transaction_id = cursor.fetchone()[0]
                insert_trans_payeename_query = """
                    INSERT INTO trans_payeename (transaction_id, dv_no, dv_yr, dv_month, dv_sequence, is_cancel, is_multiple, validate_budget)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(insert_trans_payeename_query, (transaction_id, generated_dv, dv_yr, dv_month, dv_sequence, 0, 0, 0))
                checklist_items = [249, 46, 47, 48, 49, 250, 50, 51, 52, 248]
                insert_checklist_query = """
                    INSERT INTO tbl_transaction_checklist (transaction_id, checklist_transaction_id, checklist_id, is_active)
                    VALUES (%s, %s, %s, %s)
                """

                for checklist_id in checklist_items:
                    cursor.execute(insert_checklist_query, (transaction_id, 7, checklist_id, 0))
                cursor.execute(update_query, [new_generated_dv])

            return JsonResponse({'data': 'success', 'dv_no': new_generated_dv})
        return JsonResponse({'data': 'error', 'message': 'No value found'})

    else:
        return JsonResponse({'data': 'error', 'message': 'Invalid request method'})
    
@mfa_required
@csrf_exempt
def add_emp_dv(request):
    if request.method == 'POST':
        user_id = request.session.get('user_id', 0)
        tev_id = request.POST.get('tev_id')
        dv_no = request.POST.get('dv_no')
        TevIncoming.objects.filter(id=tev_id).update(status_id=5, updated_at = date_time.datetime.now(), date_payrolled = date_time.datetime.now(), payrolled_by = user_id)
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
    
@mfa_required
@csrf_exempt
def add_emp_journal(request):
    if request.method == 'POST':
        user_id = request.session.get('user_id', 0)
        tev_id = request.POST.get('tev_id')
        dv_no = request.POST.get('dv_no')
        box_b = TevIncoming.objects.filter(id=tev_id).update(status_id=12, updated_at = date_time.datetime.now())
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
  
@mfa_required
@csrf_exempt
def retrieve_employee(request):
    dv_no_id = request.POST.get('dv_no_id')
    data = []
    
    try:
        # Ensure dv_no_id is valid
        dv_no_id = int(dv_no_id)  # or validate according to your requirements
        dv_number = TevOutgoing.objects.filter(id=dv_no_id).first()
        
        if dv_number is None:
            return JsonResponse({'error': 'DV number not found'}, status=404)

        list_employee = TevIncoming.objects.filter(status_id=4).order_by('first_name')

        for row in list_employee:
            date_travel_list = [
                datetime.strptime(date_str.strip(), "%d-%m-%Y").replace(tzinfo=pytz.UTC) 
                for date_str in row.date_travel.split(',')
            ]
            date_travel_formatted = ', '.join(date_travel.strftime("%b. %d %Y") for date_travel in date_travel_list)

            final_amount = row.final_amount or 0
            try:
                # Try converting to Decimal
                final_amount_decimal = Decimal(final_amount)
            except (InvalidOperation, ValueError):
                final_amount_decimal = Decimal(0)

            emp_fullname = f"{row.first_name or ''} {row.middle_name or ''} {row.last_name or ''} : Amount: {final_amount_decimal:,.2f} : Date Travel: {date_travel_formatted}".strip()

            data.append({
                'id': row.id,
                'name': emp_fullname
            })

        response = {
            'data': data,
            'dv_no': dv_number.dv_no,
            'status': dv_number.status_id
        }
        
        return JsonResponse(response)

    except (ValueError, TypeError) as e:
        return JsonResponse({'error': 'Invalid input'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@mfa_required
@csrf_exempt
def delete_box_list(request):
    if request.method == 'POST':
        incoming_id = request.POST.get('emp_id')
        dv_number = request.POST.get('dv_number')
        year = request.POST.get('year_now')
        finance_connection = get_finance_connection(year)

        try:
            charges = PayrolledCharges.objects.filter(incoming_id=incoming_id)
            with transaction.atomic():
                final_amount = TevIncoming.objects.filter(id=incoming_id).values_list('final_amount', flat=True).first()

                if final_amount is None:
                    return JsonResponse({'status': 'error', 'message': 'final_amount not found'}, status=400)
                
                if charges.exists():
                    with connections[finance_connection].cursor() as cursor:
                        cursor.execute("""
                            SELECT amt_certified FROM transactions WHERE dv_no = %s
                        """, [dv_number])
                        result = cursor.fetchone()

                        if result:
                            current_amt_certified = result[0]
                            if current_amt_certified >= final_amount:
                                cursor.execute("""
                                    UPDATE transactions
                                    SET amt_certified = GREATEST(amt_certified - %s, 0)
                                    WHERE dv_no = %s
                                """, [final_amount, dv_number])

                TevBridge.objects.filter(tev_incoming_id=incoming_id).delete()
                TevIncoming.objects.filter(id=incoming_id).update(status_id=4, date_payrolled=None, payrolled_by=None)

            return JsonResponse({'data': 'success', 'message': 'Record deleted and amount subtracted'})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)



@mfa_required
@csrf_exempt
def update_amt(request):
    incoming_id = request.POST.get('emp_id')
    amt = request.POST.get('amount')
    pp = request.POST.get('purpose')
    dv_number = request.POST.get('dv_number')
    year = request.POST.get('year_now')
    finance_connection = get_finance_connection(year)

    charges_total = PayrolledCharges.objects.filter(incoming_id=incoming_id).aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
    amt_issued_dec = Decimal(amt) 
    amt_dec = amt_issued_dec - charges_total 
    
    try:
        with transaction.atomic():


            with connections[finance_connection].cursor() as cursor:
                cursor.execute("""
                    UPDATE transactions
                    SET amt_certified = amt_certified + %s
                    WHERE dv_no = %s
                """, [amt_dec, dv_number])

            data = PayrolledCharges.objects.select_for_update().filter(incoming_id=incoming_id)
            if len(data) == 1:
                data.update(amount=amt)

            TevBridge.objects.filter(tev_incoming_id=incoming_id).update(purpose=pp)
            TevIncoming.objects.filter(id=incoming_id).update(final_amount=amt)

    except Exception as e:
        response = {'error': str(e)}
        return JsonResponse(response, status=500)

    response = {'data': 'success'}
    return JsonResponse(response)

@mfa_required
@csrf_exempt
def out_box_a(request):
    out_list = request.POST.getlist('out_list[]')
    user_id = request.session.get('user_id', 0)
    missing_items = []
    out_list_int = [int(item) for item in out_list]
    for check_dv in out_list_int:
        check_no_assigned = TevBridge.objects.filter(tev_outgoing_id=check_dv).values_list('tev_incoming_id', flat=True)
        if not check_no_assigned:
            missing_items.append(check_dv)
    if missing_items:
        return JsonResponse({'message': "Travel selected no assign DV please review",'text': "You must assign at least one travel to this DV to view the data" })
    else:
        result_id = TevBridge.objects.filter(tev_outgoing_id__in=out_list_int).values_list('tev_incoming_id', flat=True)
        result_list = [item for item in result_id]
        for check_charges in result_list:
            check_no_charges = PayrolledCharges.objects.filter(incoming_id=check_charges).values_list('incoming_id', flat=True)
            if not check_no_charges:
                missing_items.append(check_charges)
        if missing_items:
            return JsonResponse({'message': "Travel selected no assigned Amount Charges",'text': "You must assign at least one charges to this DVs" })
        else:
            ids = TevBridge.objects.filter(tev_outgoing_id__in=out_list_int).values_list('tev_incoming_id', flat=True)
            TevIncoming.objects.filter(id__in=ids).update(status_id=6)
            for item_id  in out_list:
                TevOutgoing.objects.filter(id=item_id).update(status_id=6,box_b_out=date_time.datetime.now(), out_by = user_id)
            return JsonResponse({'data': 'success'})

@mfa_required
@csrf_exempt
def receive_otg(request):
    missing_items = []
    out_list = request.POST.getlist('out_list[]')
    user_id = request.session.get('user_id', 0)
    out_list_int = [int(item) for item in out_list]

    for status_id in out_list_int:
        check_status = TevOutgoing.objects.filter(id=status_id, status_id=9).values_list('dv_no', flat=True)
        if check_status:
            status = [item for item in check_status]
            missing_items.extend(status)

    if missing_items:
        return JsonResponse({'data': ', '.join(map(str, missing_items)), 'message' : 'Selected DVs is already Forwarded'})
    else:
        ids = TevBridge.objects.filter(tev_outgoing_id__in=out_list_int).values_list('tev_incoming_id', flat=True)
        
        TevIncoming.objects.filter(id__in=ids).update(status_id=8)
        
        for item_id  in out_list:
            TevOutgoing.objects.filter(id=item_id).update(status_id=8,otg_d_received=date_time.datetime.now(), otg_r_user_id = user_id)
        return JsonResponse({'data': 'success'})

@mfa_required
@csrf_exempt
def forward_otg(request):
    missing_items = []
    out_list = request.POST.getlist('out_list[]')
    user_id = request.session.get('user_id', 0)
    out_list_int = [int(item) for item in out_list]
    for status_id in out_list_int:
        check_status = TevOutgoing.objects.filter(id=status_id, status_id=6).values_list('dv_no', flat=True)
        if check_status:
            status = [item for item in check_status]
            missing_items.extend(status)
    if missing_items:
        return JsonResponse({'data':'Dvs must receive first!','message': ', '.join(map(str, missing_items))})
    else:
        ids = TevBridge.objects.filter(tev_outgoing_id__in=out_list_int).values_list('tev_incoming_id', flat=True)
        TevIncoming.objects.filter(id__in=ids).update(status_id=9)
        for item_id  in out_list:
            TevOutgoing.objects.filter(id=item_id).update(status_id=9,otg_out_user_id = user_id,otg_d_forwarded=date_time.datetime.now())
        return JsonResponse({'data': 'success'})

@mfa_required
@csrf_exempt
def receive_budget(request):
    missing_items = []
    out_list = request.POST.getlist('out_list[]')
    user_id = request.session.get('user_id', 0)
    out_list_int = [int(item) for item in out_list]

    for status_id in out_list_int:
        check_status = TevOutgoing.objects.filter(id=status_id, status_id=11).values_list('dv_no', flat=True)
        if check_status:
            status = [item for item in check_status]
            missing_items.extend(status)

    if missing_items:
        return JsonResponse({'data': ', '.join(map(str, missing_items)), 'message' : 'Selected DVs is already Forwarded'})
    else:
        ids = TevBridge.objects.filter(tev_outgoing_id__in=out_list_int).values_list('tev_incoming_id', flat=True)
        
        TevIncoming.objects.filter(id__in=ids).update(status_id=10)
        
        for item_id  in out_list:
            TevOutgoing.objects.filter(id=item_id).update(status_id=10,b_d_received=date_time.datetime.now(), b_r_user_id = user_id)
        return JsonResponse({'data': 'success'})

@mfa_required  
@csrf_exempt
def forward_budget(request):
    try:
        missing_items = []
        out_list = request.POST.getlist('out_list[]')
        user_id = request.session.get('user_id', 0)
        out_list_int = [int(item) for item in out_list]
        for status_id in out_list_int:
            check_status = TevOutgoing.objects.filter(id=status_id, status_id=9).values_list('dv_no', flat=True)
            if check_status:
                status = [item for item in check_status]
                missing_items.extend(status)
        if missing_items:
            return JsonResponse({'data': 'Dvs must receive first!', 'message': ', '.join(map(str, missing_items))})
        else:
            ids = TevBridge.objects.filter(tev_outgoing_id__in=out_list_int).values_list('tev_incoming_id', flat=True)
            TevIncoming.objects.filter(id__in=ids).update(status_id=11)
            for item_id in out_list:
                TevOutgoing.objects.filter(id=item_id).update(status_id=11, b_out_user_id=user_id, b_d_forwarded=date_time.datetime.now())
            return JsonResponse({'data': 'success'})
    except Exception as e:
        return JsonResponse({'data': 'error', 'message': str(e)})

@mfa_required
@csrf_exempt
def receive_journal(request):
    missing_items = []
    journal_date = request.POST.get('journal_date')
    out_list = request.POST.getlist('out_list[]')
    user_id = request.session.get('user_id', 0)
    out_list_int = [int(item) for item in out_list]

    for status_id in out_list_int:
        check_status = TevOutgoing.objects.filter(id=status_id, status_id=13).values_list('dv_no', flat=True)
        if check_status:
            status = [item for item in check_status]
            missing_items.extend(status)

    if missing_items:
        return JsonResponse({'data': ', '.join(map(str, missing_items)), 'message': 'Selected DVs are already Forwarded'})
    else:
        ids = TevBridge.objects.filter(tev_outgoing_id__in=out_list_int).values_list('tev_incoming_id', flat=True)
        TevIncoming.objects.filter(id__in=ids).update(status_id=12)
        dv_list = []

        if journal_date:
            journal_date_obj = datetime.strptime(journal_date, '%Y-%m-%d %H:%M')
            
            for item_id in out_list:
                tev_outgoing = TevOutgoing.objects.filter(id=item_id).first()
                b_d_forwarded = tev_outgoing.b_d_forwarded
                if b_d_forwarded <= journal_date_obj:
                    TevOutgoing.objects.filter(id=item_id).update(
                        status_id=12,
                        j_d_received=journal_date_obj,
                        j_r_user_id=user_id
                    )
                else:
                    dv_list.append(tev_outgoing.dv_no)
        else:
            for item_id in out_list:
                TevOutgoing.objects.filter(id=item_id).update(
                    status_id=12,
                    j_d_received=date_time.datetime.now(),
                    j_r_user_id=user_id
                )
        if dv_list:
            return JsonResponse({'data': 'invalid', 'message': 'The Budget forwarded date must be beyond the Journal date.','dv_no':', '.join(dv_list)})
    return JsonResponse({'data': 'success'})

@mfa_required
@csrf_exempt
def forward_journal(request):
    missing_items = []
    journal_date = request.POST.get('journal_date')
    out_list = request.POST.getlist('out_list[]')
    user_id = request.session.get('user_id', 0)
    out_list_int = [int(item) for item in out_list]
    year = request.POST.get('year')
    finance_connection = get_finance_connection(year)
    
    finance_data = connections[finance_connection]

    for status_id in out_list_int:
        check_status = TevOutgoing.objects.filter(id=status_id, status_id=11).values_list('dv_no', flat=True)
        if check_status:
            status = [item for item in check_status]
            missing_items.extend(status)
    if missing_items:
        return JsonResponse({'data':'Dvs must receive first!','message': ', '.join(map(str, missing_items))})
    else:
        dv_list = []
        if journal_date:
            journal_date_obj = datetime.strptime(journal_date, '%Y-%m-%d %H:%M')

            for item_id in out_list:
                tev_outgoing = TevOutgoing.objects.filter(id=item_id).first()
                j_d_received = tev_outgoing.j_d_received
                if j_d_received <= journal_date_obj:
                    TevOutgoing.objects.filter(id=item_id).update(status_id=13,j_out_user_id=user_id,j_d_forwarded=journal_date_obj)
                    dv_no_values = TevOutgoing.objects.filter(id__in=out_list_int).values_list('dv_no', flat=True)
                    with transaction.atomic():
                        for dv in dv_no_values:
                            with finance_data.cursor() as cursor:
                                actual_date = datetime.now()
                                query = f"""
                                UPDATE transactions SET approval_date = %s WHERE dv_no = %s
                                """
                                params = [actual_date, dv]
                                cursor.execute(query, params)
                else:
                    dv_list.append(tev_outgoing.dv_no)
        else:
            ids = TevBridge.objects.filter(tev_outgoing_id__in=out_list_int).values_list('tev_incoming_id', flat=True)
            TevIncoming.objects.filter(id__in=ids).update(status_id=13)
            for item_id in out_list:
                TevOutgoing.objects.filter(id=item_id).update(status_id=13,j_out_user_id=user_id,j_d_forwarded=datetime.now())

            dv_no_values = TevOutgoing.objects.filter(id__in=out_list_int).values_list('dv_no', flat=True)
            with transaction.atomic():
                for dv in dv_no_values:
                    with finance_data.cursor() as cursor:
                        actual_date = datetime.now()
                        query = f"""
                        UPDATE transactions SET approval_date = %s WHERE dv_no = %s
                        """
                        params = [actual_date, dv]
                        cursor.execute(query, params)

        if dv_list:
            return JsonResponse({'data': 'invalid', 'message': 'The Journal forwarded date must be beyond the Journal date received.','dv_no':', '.join(dv_list)})
    
    return JsonResponse({'data': 'success'})



@mfa_required
@csrf_exempt
def receive_approval(request):
    missing_items = []
    out_list = request.POST.getlist('out_list[]')
    user_id = request.session.get('user_id', 0)
    out_list_int = [int(item) for item in out_list]

    for status_id in out_list_int:
        check_status = TevOutgoing.objects.filter(id=status_id, status_id=15).values_list('dv_no', flat=True)
        if check_status:
            status = [item for item in check_status]
            missing_items.extend(status)

    if missing_items:
        return JsonResponse({'data': ', '.join(map(str, missing_items)), 'message' : 'Selected DVs is already Forwarded'})
    else:
        ids = TevBridge.objects.filter(tev_outgoing_id__in=out_list_int).values_list('tev_incoming_id', flat=True)
        
        TevIncoming.objects.filter(id__in=ids).update(status_id=14)
        
        for item_id  in out_list:
            TevOutgoing.objects.filter(id=item_id).update(status_id=14,a_d_received=date_time.datetime.now(), a_r_user_id = user_id)
        return JsonResponse({'data': 'success'})
     
@mfa_required
@csrf_exempt
def forward_approval(request):
    missing_items = []
    out_list = request.POST.getlist('out_list[]')
    user_id = request.session.get('user_id', 0)
    out_list_int = [int(item) for item in out_list]
    for status_id in out_list_int:
        check_status = TevOutgoing.objects.filter(id=status_id, status_id=13).values_list('dv_no', flat=True)
        if check_status:
            status = [item for item in check_status]
            missing_items.extend(status)
    if missing_items:
        return JsonResponse({'data':'Dvs must receive first!','message': ', '.join(map(str, missing_items))})
    else:
        ids = TevBridge.objects.filter(tev_outgoing_id__in=out_list_int).values_list('tev_incoming_id', flat=True)
        TevIncoming.objects.filter(id__in=ids).update(status_id=15)
        for item_id  in out_list:
            TevOutgoing.objects.filter(id=item_id).update(status_id=15,a_out_user_id = user_id,a_d_forwarded=date_time.datetime.now())
        return JsonResponse({'data': 'success'})

@mfa_required
@csrf_exempt
def tev_details(request):
    tev_id = request.POST.get('tev_id')
    tev = TevIncoming.objects.filter(id=tev_id).first()
    data = {
        'data': model_to_dict(tev)
    }
    return JsonResponse(data)

@mfa_required
@csrf_exempt
def tevemployee(request):
    tev_id = request.POST.get('tev_id')
    qs_object = TevIncoming.objects.filter(id=tev_id).first()
    if qs_object:
        data = serializers.serialize('json', [qs_object])
        return JsonResponse({'data': data})
    else:
        return JsonResponse({'data': None})

@mfa_required
@csrf_exempt
def addtev(request):
    
    employeename = request.POST.get('employeename')
    amount = request.POST.get('amount')
    remarks = request.POST.get('remarks')
    user_id = request.session.get('user_id', 0)
    
    tev_add = TevIncoming(employee_name=employeename,original_amount=amount,incoming_remarks=remarks,user_id=user_id)
    tev_add.save()

    return JsonResponse({'data': 'success'})

@mfa_required
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



@mfa_required
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

@mfa_required
@csrf_exempt
def get_project_src(request):
    data = []
    cluster_id = request.GET.get('cluster_id')
    project_src = LibProjectSrc.objects.filter(cluster_id=cluster_id)
    for item in project_src:
        item_entry = {
            'id': item.id,
            'name': item.name  
        }
        data.append(item_entry)

    return JsonResponse({'data': data})

    






