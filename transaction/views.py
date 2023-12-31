from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from main.models import (AuthUser, TevIncoming, SystemConfiguration,RoleDetails, StaffDetails, Cluster, Charges, TevOutgoing, TevBridge, Division)
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
            'role_permission' : role.role_name,
            'cluster' : Cluster.objects.filter().order_by('name'),
            'division' : Division.objects.filter(status=0).order_by('name'),
        }
        return render(request, 'receive/list.html', context)
    else:
        return render(request, 'pages/unauthorized.html')
    
    
@login_required(login_url='login')
def list_payroll(request):
    user_details = get_user_details(request)
    allowed_roles = ["Admin", "Incoming staff", "Validating staff"] 
    role = RoleDetails.objects.filter(id=user_details.role_id).first()
    if role.role_name in allowed_roles:
        context = {
            'charges' : Charges.objects.filter().order_by('name'),
            'cluster' : Cluster.objects.filter().order_by('name'),
            'division' : Division.objects.filter(status=0).order_by('name'),
            'role_permission' : role.role_name,
        }
        return render(request, 'transaction/list.html', context)
    else:
        return render(request, 'pages/unauthorized.html')
    

@login_required(login_url='login')
@csrf_exempt
def assign_payroll(request):
    user_details = get_user_details(request)
    allowed_roles = ["Admin", "Incoming staff", "Validating staff"] 
    role = RoleDetails.objects.filter(id=user_details.role_id).first()
    if role.role_name in allowed_roles:
        user_details = get_user_details(request)
        allowed_roles = ["Admin", "Payroll staff"] 
        context = {
            'role_permission' : role.role_name,
        }
        return render(request, 'transaction/list.html', context)
    else:
        return render(request, 'pages/unauthorized.html')    
    
    
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

    allowed_roles = ["Admin", "Incoming staff", "Validating staff"] 
    role = RoleDetails.objects.filter(id=user_details.role_id).first()
    if role.role_name in allowed_roles:
        context = {
            'employee_list' : TevIncoming.objects.filter().order_by('first_name'),
            'role_permission' : role.role_name,
            'dv_number' : TevOutgoing.objects.filter().order_by('id'),
            'cluster' : Cluster.objects.filter().order_by('id'),
            'division' : Division.objects.filter(status=0).order_by('id'),
        }
        return render(request, 'transaction/box_a.html', context)
    else:
        return render(request, 'pages/unauthorized.html')
    
    


@login_required(login_url='login')
def preview_box_a(request):
    finance_database_alias = 'finance'    
    outgoing_id = request.GET.get('id')
    user_id = request.session.get('user_id', 0)
    
    results = []
    total_final_amount = 0
    emp_list_code = []
    emp_list_lname = []
    charges_list = []
    
    userData = AuthUser.objects.filter(id=user_id)
    full_name = userData[0].first_name + ' ' + userData[0].last_name

    designation = StaffDetails.objects.filter(user_id= user_id)
    position = designation[0].position
    
    
    if outgoing_id:
        tev_incoming_ids = TevBridge.objects.filter(tev_outgoing_id=outgoing_id).values_list('tev_incoming_id', flat=True)
        
        
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
        
        for item in te_lname:
            total_final_amount += item['final_amount']
            final_amount = item['final_amount']
            charge_name = item['tevbridge__charges__name']

            existing_charge = next((charge for charge in charges_list if charge['charges'] == charge_name), None)
            if existing_charge:
                # If it exists, accumulate the final_amount
                existing_charge['final_amount'] += final_amount
            else:
                charges = {
                    "final_amount": final_amount,
                    "charges": charge_name,
                }
                charges_list.append(charges)

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
            
        outgoing = TevOutgoing.objects.filter(id=outgoing_id).values('dv_no','box_b_in','division__chief','division__c_designation','division__approval','division__ap_designation').first()
        dvno = outgoing['dv_no']
        
        
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
            'dv_number':dvno,
            'charges_list':charges_list,
            'payroll_date':box_b_in,
            'total_amount':total_final_amount,
            'total_count':result_count,
            'finance':results,
            'details':designation_result,
            'emp_list_lname':emp_list_lname,
            'user' : full_name,
            'position' : position
        }
        
        return render(request, 'transaction/print_box_a.html', context)
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
    
    idd = request.POST.get('dv_id')
    dv_no = TevOutgoing.objects.filter(id=idd).values('dv_no','is_print','id').first()

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
        SELECT ti.id, code, first_name, middle_name, last_name,id_no,account_no, final_amount, tb.purpose, dv_no, ch.name, cl.name FROM tev_incoming AS ti 
        LEFT JOIN tev_bridge AS tb ON tb.tev_incoming_id = ti.id
        LEFT JOIN tev_outgoing AS t_o ON t_o.id = tb.tev_outgoing_id
        LEFT JOIN charges AS ch ON ch.id = tb.charges_id
        LEFT JOIN cluster AS cl ON cl.id = t_o.cluster
        WHERE ti.status_id IN (1, 2, 4, 5, 6, 7) AND dv_no = %s    
    """

    with connection.cursor() as cursor:
        cursor.execute(query, (dvno,))
        results = cursor.fetchall()
        
    column_names = ['id','code', 'first_name','middle_name', 'last_name','id_no','account_no', 'final_amount','purpose','dv_no','charges','cluster']
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
        
        final_amount = float(row['final_amount'])
        total_amount += final_amount
        item = {
            'id': row['id'],
            'code': row['code'],
            'name': emp_fullname,
            'id_no': row['id_no'],
            'account_no': row['account_no'],
            'final_amount': row['final_amount'],
            'purpose': row['purpose'],
            'dv_no': row['dv_no'],
            'charge':row['charges'],
            'cluster':row['cluster'],
            'total':total_amount,
            
        }
        data.append(item)
        

    #     _start = request.GET.get('start') if request.GET.get('start') else 0
    #     _length = request.GET.get('length') if request.GET.get('length') else 0
        
    # if _start and _length:
    #     start = int(_start)
    #     length = int(_length)
    #     page = math.ceil(start / length) + 1
    #     per_page = length
    #     results = results[start:start + length]
                    
    total = len(data)    
          
    response = {
        'data': data,
        'charges': charges_list,
        'is_print': dv_no['is_print'],
        'dv_number':dv_no['dv_no'],
        'outgoing_id':dv_no['id'],
        'recordsTotal': total,
        'recordsFiltered': total,
        'total_amount':total_amount
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

        query = """
            SELECT * FROM `tev_incoming` WHERE status_id = 4
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

        with connection.cursor() as cursor:
            cursor.execute(query, params)
            results = dictfetchall(cursor)

            print (results)

    
    elif _search:
        query = TevIncoming.objects.filter(status_id=4).filter(filter_conditions).select_related().distinct().order_by(_order_dash + 'id')
    else:
        query = """
            SELECT * FROM `tev_incoming` WHERE status_id = 4
        """

        # item_data = TevIncoming.objects.filter(status_id=4).select_related().distinct().order_by(_order_dash + 'id')

    # item_data = (TevIncoming.objects.filter(status_id=4).select_related().distinct().order_by('-id').reverse())
    
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





    # d.FAdvancedFilter = FAdvancedFilter.val()
    # d.BoxDvNo = BoxDvNo.val()
    # d.FCluster = FCluster.val()
    # d.FDivision = FDivision.val()
    # d.FBoxIn = FBoxIn.val()
    # d.FBoxOut = FBoxOut.val()
    # d.BoxStatus = BoxStatus.val()



    _search = request.GET.get('search[value]')
    _order_dir = request.GET.get('order[0][dir]')
    _order_dash = '-' if _order_dir == 'desc' else ''
    _order_col_num = request.GET.get('order[0][column]')
    status_txt = ''
    status_txt = '5' if _search == 'outgoing' else '6'
     
    # item_data = (TevOutgoing.objects.filter().select_related().distinct().order_by('-id').reverse())
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

        item_data = TevOutgoing.objects.all()

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
        item_data = TevOutgoing.objects.filter().filter(filter_conditions).select_related().distinct().order_by(_order_dash + 'id')
    else:
        item_data = TevOutgoing.objects.filter().select_related().distinct().order_by('-id')

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


# @csrf_exempt
# def item_update(request):
#     id = request.POST.get('ItemID')
#     emp_name = request.POST.get('EmployeeName')
#     amount = request.POST.get('OriginalAmount')
#     remarks = request.POST.get('Remarks')
#     tev_update = TevIncoming.objects.filter(id=id).update(name=emp_name,original_amount=amount,remarks=remarks)
#     return JsonResponse({'data': 'success'})


@csrf_exempt
def update_status(request):
    id = request.POST.get('dv_id')
    tev_update = TevOutgoing.objects.filter(dv_no=id).update(is_print=True)
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
def delete_box_list(request):
    incoming_id = request.POST.get('emp_id')
    dv_no = request.POST.get('dv_number')
    
    deleteBridge, _ = TevBridge.objects.filter(tev_incoming_id=incoming_id).delete()
    delete, _ = TevIncoming.objects.filter(id=incoming_id).delete()

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



