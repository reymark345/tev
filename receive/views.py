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
    # print(data)
    # print("testdawa")
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

    query = """
        SELECT code,name,date_travel,ti.status,original_amount,final_amount,incoming_in,incoming_out, tb.purpose, dv_no FROM tev_incoming AS ti 
        LEFT JOIN tev_bridge AS tb ON tb.tev_incoming_id = ti.id
        LEFT JOIN tev_outgoing AS t_o ON t_o.id = tb.tev_outgoing_id
        WHERE ti.status IN (1, 2, 4, 5 , 7)
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
        
    column_names = ['code', 'name', 'date_travel','status','original_amount', 'final_amount', 'incoming_in', 'incoming_out', 'purpose','dv_no']
    finance_data = []

    for finance_row in results:
        finance_dict = dict(zip(column_names, finance_row))
        finance_data.append(finance_dict)
    
    data = []
    for row in finance_data:
        amt_certified = ''
        amt_journal = ''
        amt_budget = ''
        if row['dv_no']:
            
            finance_query = """
                SELECT dv_no, amt_certified, amt_journal, amt_budget 
                FROM transactions 
                WHERE dv_no = %s
            """
            with connections[finance_database_alias].cursor() as cursor2:
                cursor2.execute(finance_query, (row['dv_no'],))
                finance_results = cursor2.fetchall()
                
            if finance_results:
                
                amt_certified = finance_results[0][1]
                amt_journal = finance_results[0][2]
                amt_budget = finance_results[0][3]
                
        
   
    
        item = {
            'code': row['code'],
            'name': row['name'],
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
            'amt_budget': amt_budget
        }
        data.append(item)
        
        _start = request.GET.get('start')
        _length = request.GET.get('length')
        
    if _start and _length:
        start = int(_start)
        length = int(_length)
        page = math.ceil(start / length) + 1
        per_page = length
        results = results[start:start + length]
                
        
        print("finance_data11")
        print(row['code'])
        
    total = len(finance_results)    
          
    response = {
        'data': data,
        'page': page,
        'per_page': per_page,
        'recordsTotal': total,
        'recordsFiltered': total,
    }
    return JsonResponse(response)


    
 
    
    
    
            


        
        
        
        
        

        
        
    # for row in te_dict:
        
                    
    #     print(te_dict)
    #     print("te_dict1")
    #     print(row)
        
    #     finance_query = """
    #         SELECT dv_no, amt_certified, amt_journal, amt_budget 
    #         FROM transactions 
    #         WHERE dv_no = %s
    #     """
    #     with connections[finance_database_alias].cursor() as cursor2:
    #         cursor2.execute(finance_query, (row[8],))
    #         finance_results = cursor2.fetchall()
            
            
    #     print(finance_results)
        

    #     total = len(results)

    #     _start = request.GET.get('start')
    #     _length = request.GET.get('length')

    #     if _start and _length:
    #         start = int(_start)
    #         length = int(_length)
    #         page = math.ceil(start / length) + 1
    #         per_page = length
    #         results = results[start:start + length]

    #     data = []
        
    #     for row in results:
    #         item = {
    #             'id': row[0],
    #             'code': row[1],
    #             'name': row[2],
    #             'id_no': row[3],
    #             'account_no': row[4],
    #             'date_travel': row[5],
    #             'original_amount': row[6],
    #             'final_amount': row[7],
    #             'incoming_in': row[8],
    #             'incoming_out': row[9],
    #             'slashed_out': row[10],
    #             'remarks': row[11],
    #             'purpose': row[12],
    #             'status': row[13],
    #             'user_id': row[14]
        
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
    
    
    


# def tracking_load(request):
#     finance_database_alias = 'finance'
#     dv_no_list = TevOutgoing.objects.order_by('id').values_list('dv_no', flat=True)
    

#     query = """
#         SELECT dv_no, amt_certified, amt_journal, amt_budget 
#         FROM transactions 
#         WHERE dv_no IN %s
#     """
#     params = [tuple(dv_no_list)]
    

#     with connections[finance_database_alias].cursor() as cursor:
#         cursor.execute(query, params)
#         results = cursor.fetchall()
        
        
#     print("results")
#     print(results)


#     dv_no_values = [result[0] for result in results]
#     dv_no_to_result = {result[0]: result for result in results}
    
    
# # Format the dv_no_values list
#     formatted_values = []
#     for dv_no in dv_no_values:
#         result = dv_no_to_result.get(dv_no)
#         if result:
#             amt_certified = result[1]
#             amt_journal = result[2]
#             amt_budget = result[3]
#             formatted_values.append([dv_no, amt_certified, amt_journal, amt_budget])
#         else:
#             formatted_values.append([dv_no])

#     print("Formatted dv_no_values:")
#     print(formatted_values)

#     tev_outgoing_ids = TevOutgoing.objects.filter(dv_no__in=dv_no_values).order_by('id').values_list('id', flat=True)


#     result_data = []
#     for i, tev_outgoing_id in enumerate(tev_outgoing_ids):
#         result_data.append((formatted_values[i], tev_outgoing_id))

#     print("Combined data:")
#     for formatted_value, tev_outgoing_id in result_data:
#         print(f"Formatted: {formatted_value}, tev_outgoing_id: {tev_outgoing_id}") 

#     tev_outgoing_ids = TevOutgoing.objects.filter(dv_no__in=dv_no_values).order_by('id').values_list('id', flat=True)
#     print(tev_outgoing_ids)
    
    
#     query = """
#         SELECT t.*
#         FROM tev_incoming t
#         WHERE t.status IN (1, 2, 4, 5 , 7)
#            OR (t.status = 3 AND (
#                SELECT COUNT(*)
#                FROM tev_incoming
#                WHERE code = t.code
#                ) = 1
#            );
#     """

#     with connection.cursor() as cursor:
#         cursor.execute(query)
#         results = cursor.fetchall()

#     total = len(results)

#     _start = request.GET.get('start')
#     _length = request.GET.get('length')

#     if _start and _length:
#         start = int(_start)
#         length = int(_length)
#         page = math.ceil(start / length) + 1
#         per_page = length
#         results = results[start:start + length]

#     data = []
    
#     for row in results:
#         item = {
#             'id': row[0],
#             'code': row[1],
#             'name': row[2],
#             'id_no': row[3],
#             'account_no': row[4],
#             'date_travel': row[5],
#             'original_amount': row[6],
#             'final_amount': row[7],
#             'incoming_in': row[8],
#             'incoming_out': row[9],
#             'slashed_out': row[10],
#             'remarks': row[11],
#             'purpose': row[12],
#             'status': row[13],
#             'user_id': row[14]
      
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
            'account_no': row[4],
            'date_travel': row[5],
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
    
    travel_date = request.POST.get('DateTravel')
    travel_date_stripped = travel_date.strip()
    travel_date_spaces = travel_date_stripped.replace(' ', '')
    
    id = request.POST.get('ItemID')
    data = TevIncoming.objects.filter(id=id).first()
    
    tev_add = TevIncoming(code=data.code,name=data.name,date_travel = travel_date_spaces,original_amount=amount,remarks=remarks,user_id=data.user_id)
    tev_add.save()
    
    
    #tev_update = TevIncoming.objects.filter(id=id).update(name=emp_name,original_amount=amount,remarks=remarks)
    return JsonResponse({'data': 'success'})


# @csrf_exempt
# def item_add(request):
#     employeename = request.POST.get('EmployeeName')
#     amount = request.POST.get('OriginalAmount')
#     travel_date = request.POST.get('DateTravel')
#     remarks = request.POST.get('Remarks')
#     user_id = request.session.get('user_id', 0)
#     g_code = generate_code()


#     if travel_date:
#         # Split the comma-separated date list into individual date strings
#         date_list = travel_date.split(', ')

#         # Convert date strings to datetime objects
#         date_objects = [datetime.datetime.strptime(date_str, "%d-%m-%Y") for date_str in date_list]

#         # Build a Q object to handle multiple date conditions
#         date_conditions = Q()
#         for date in date_objects:
#             date_conditions |= Q(date_travel=date)

#         # Check if the query exists based on the provided criteria
        
        
        
#         query_exists = TevIncoming.objects.filter(Q(name=employeename) & date_conditions).exists()
        
#         print(date_conditions)
#         print("aweee")
        
#         if query_exists:
#             return JsonResponse({'data': 'error', 'message': 'Duplicate Travel'})
#         else:
#             return JsonResponse({'data': 'success', 'g_code': g_code})

#     else:
#         return JsonResponse({'data': 'error', 'message': 'sasasaas'})

# @csrf_exempt
# def item_add(request):
#     employeename = request.POST.get('EmployeeName')
#     amount = request.POST.get('OriginalAmount')
#     travel_date = request.POST.get('DateTravel')
#     remarks = request.POST.get('Remarks')
#     user_id = request.session.get('user_id', 0)
#     g_code = generate_code()

#     # Split the date string into individual dates
#     individual_dates = travel_date.split(',')

#     # Remove spaces from each individual date and rejoin them with a comma
#     cleaned_dates = ','.join(date.strip() for date in individual_dates)

#     if TevIncoming.objects.filter(name=employeename, date_travel=cleaned_dates):
#         return JsonResponse({'data': 'error', 'message': 'Duplicate Travel'})

#     else:
#         tev_add = TevIncoming(code=g_code, name=employeename, date_travel=cleaned_dates, original_amount=amount, remarks=remarks, user_id=user_id)
#         tev_add.save()

#         if tev_add.id:
#             system_config = SystemConfiguration.objects.first()
#             system_config.transaction_code = g_code
#             system_config.save()

#         return JsonResponse({'data': 'success', 'g_code': g_code})

@csrf_exempt
def item_add(request):
    employeename = request.POST.get('EmployeeName')
    amount = request.POST.get('OriginalAmount')
    travel_date = request.POST.get('DateTravel')
    remarks = request.POST.get('Remarks')
    user_id = request.session.get('user_id', 0)
    g_code = generate_code()
    
    duplicate_travel = []
    individual_dates = travel_date.split(',')
    cleaned_dates = ','.join(date.strip() for date in individual_dates)
    
    for date in individual_dates:
        cleaned_date = date.strip()

        query = """
            SELECT date_travel FROM tev_incoming
            WHERE name = %s
            AND date_travel LIKE %s;
        """

        with connection.cursor() as cursor:
            cursor.execute(query, [employeename, f"%{cleaned_date}%"])
            results = cursor.fetchall()
        if results:
            duplicate_travel.append(cleaned_date)
        
    if duplicate_travel:
        return JsonResponse({'data': 'error', 'message':duplicate_travel})
        
    else:
        tev_add = TevIncoming(code=g_code, name=employeename, date_travel=cleaned_dates, original_amount=amount, remarks=remarks, user_id=user_id)
        tev_add.save()

        if tev_add.id:
            system_config = SystemConfiguration.objects.first()
            system_config.transaction_code = g_code
            system_config.save()

        return JsonResponse({'data': 'success', 'g_code': g_code})

            
        

        
        
        
        
        
        
    #     if TevIncoming.objects.filter(name=employeename, date_travel=cleaned_date):
    #         duplicate_dates.append(cleaned_date)

    # if duplicate_dates:
    #     print(duplicate_dates)
    #     return JsonResponse({'data': 'error', 'message':duplicate_dates})
    







# #mogana
# @csrf_exempt
# def item_addaa(request):
#     employeename = request.POST.get('EmployeeName')
#     amount = request.POST.get('OriginalAmount')
#     travel_date = request.POST.get('DateTravel')
#     remarks = request.POST.get('Remarks')
#     user_id = request.session.get('user_id', 0)
#     g_code = generate_code()

#     # Split the date string into individual dates
#     individual_dates = travel_date.split(',')

#     # Remove spaces from each individual date and rejoin them with a comma
#     cleaned_dates = ','.join(date.strip() for date in individual_dates)

#     if TevIncoming.objects.filter(name=employeename, date_travel=cleaned_dates):
#         return JsonResponse({'data': 'error', 'message': 'Duplicate Travel'})

#     else:
#         tev_add = TevIncoming(code=g_code, name=employeename, date_travel=cleaned_dates, original_amount=amount, remarks=remarks, user_id=user_id)
#         tev_add.save()

#         if tev_add.id:
#             system_config = SystemConfiguration.objects.first()
#             system_config.transaction_code = g_code
#             system_config.save()

#         return JsonResponse({'data': 'success', 'g_code': g_code})

    
# @csrf_exempt
# def item_add(request):
#     employeename = request.POST.get('EmployeeName')
#     amount = request.POST.get('OriginalAmount')
#     travel_date = request.POST.get('DateTravel')
#     remarks = request.POST.get('Remarks')
#     user_id = request.session.get('user_id', 0)
#     g_code = generate_code()

#     # Split the date string into individual dates
#     individual_dates = travel_date.split(',')

#     # Remove spaces from each individual date and rejoin them with a comma
#     cleaned_dates = ','.join(date.strip() for date in individual_dates)
    
#     print("Test")
#     print(cleaned_dates)

#     if TevIncoming.objects.filter(name=employeename, date_travel=cleaned_dates):
#         return JsonResponse({'data': 'error', 'message': 'Duplicate Travel'})

#     else:
#         tev_add = TevIncoming(code=g_code, name=employeename, date_travel=cleaned_dates, original_amount=amount, remarks=remarks, user_id=user_id)
#         tev_add.save()

#         if tev_add.id:
#             system_config = SystemConfiguration.objects.first()
#             system_config.transaction_code = g_code
#             system_config.save()

#         return JsonResponse({'data': 'success', 'g_code': g_code})

    

# @csrf_exempt
# def item_add(request):
#     employeename = request.POST.get('EmployeeName')
#     amount = request.POST.get('OriginalAmount')
#     travel_date = request.POST.get('DateTravel')
#     remarks = request.POST.get('Remarks')
#     user_id = request.session.get('user_id', 0)
#     g_code = generate_code()
    
#     travel_date = "29-08-2023, 28-08-2023"
    
#     if TevIncoming.objects.filter(name=employeename,date_travel = travel_date):
#         return JsonResponse({'data': 'error', 'message': 'Duplicate Travel'})
    
#     else:
#         tev_add = TevIncoming(code=g_code,name=employeename,date_travel = travel_date,original_amount=amount,remarks=remarks,user_id=user_id)
#         tev_add.save()
        
#         if tev_add.id:
#             system_config = SystemConfiguration.objects.first()
#             system_config.transaction_code = g_code
#             system_config.save()
            
#         return JsonResponse({'data': 'success', 'g_code': g_code})


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



