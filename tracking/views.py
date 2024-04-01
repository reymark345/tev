from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from main.models import (AuthUser, TevIncoming, SystemConfiguration,RoleDetails, StaffDetails, TevOutgoing, TevBridge, Charges, RolePermissions)
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
import pandas as pd
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from django.utils import timezone
from django.template.defaultfilters import date



@login_required(login_url='login')
@csrf_exempt
def tracking_list(request):
    allowed_roles = ["Admin", "Incoming staff", "Validating staff", "Payroll staff", "Certified staff", "Outgoing staff", "Budget staff", "Journal staff", "Approval staff"] 

    user_id = request.session.get('user_id', 0)

    role_permissions = RolePermissions.objects.filter(user_id=user_id).values('role_id')
    role_details = RoleDetails.objects.filter(id__in=role_permissions).values('role_name')
    role_names = [entry['role_name'] for entry in role_details]
    context = {
        'employee_list' : TevIncoming.objects.filter().order_by('first_name'),
        'permissions' : role_names,
    }
    return render(request, 'tracking/tracking_list.html', context)

              

    # if any(role_name in allowed_roles for role_name in role_names):
    #     context = {
    #         'employee_list' : TevIncoming.objects.filter().order_by('first_name'),
    #         'permissions' : role_names,
    #     }
    #     return render(request, 'tracking/tracking_list.html', context)
    # else:
    #     return render(request, 'pages/unauthorized.html')


def tracking_load(request):
    total = 0
    data = []
    _search = request.GET.get('search[value]')
    _order_dir = request.GET.get('order[0][dir]')
    _order_dash = '-' if _order_dir == 'desc' else ''
    _order_col_num = request.GET.get('order[0][column]')

    FIdNumber= request.GET.get('FIdNumber')
    FStatus= request.GET.get('FStatus') 
    FTransactionCode = request.GET.get('FTransactionCode')
    FDateTravel= request.GET.get('FDateTravel') 
    NDVNumber= request.GET.get('NDVNumber') 
    DpYear= request.GET.get('DpYear') 


    if DpYear == "2023":
        finance_database_alias = 'finance' 
    else:
        finance_database_alias = 'finance_2024' 

    year = int(DpYear) % 100
    formatted_year = str(year)+"-"
    
    EmployeeList = request.GET.getlist('EmployeeList[]')
    FAdvancedFilter =  request.GET.get('FAdvancedFilter')

    search_fields = ['code', 'first_name', 'last_name', 'dv_no'] 
    filter_conditions = Q()

    for field in search_fields:
        filter_conditions |= Q(**{f'{field}__icontains': _search})

    if FAdvancedFilter:

        with connection.cursor() as cursor:

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
                WHERE (tev_outgoing.dv_no LIKE %s OR tev_outgoing.dv_no IS NULL)
            """
            params = [f'{formatted_year}%']

            if FTransactionCode:
                query += " AND tev_incoming.code = %s"
                params.append(FTransactionCode)

            if FDateTravel:
                query += " AND tev_incoming.date_travel LIKE %s"
                params.append(f'%{FDateTravel}%')

            if FStatus:

                if FStatus == "5":
                    FStatus = (4,5,6)
                    query += " AND tev_incoming.status_id IN %s"
                    params.append(FStatus)

                elif FStatus == "8" or FStatus == "9":
                    FStatus = (6,8,9)
                    query += " AND tev_incoming.status_id IN %s"
                    params.append(FStatus)

                elif FStatus == "10" or FStatus == "11":
                    FStatus = (9,10,11)
                    query += " AND tev_incoming.status_id IN %s"
                    params.append(FStatus)

                elif FStatus == "12" or FStatus == "13":
                    FStatus = (11,12,13)
                    query += " AND tev_incoming.status_id IN %s"
                    params.append(FStatus)

                elif FStatus == "14":
                    FStatus = (13,14,15)
                    query += " AND tev_incoming.status_id IN %s"
                    params.append(FStatus)

                else:
                    query += " AND tev_incoming.status_id = %s"
                    params.append(FStatus)


            if EmployeeList:
                placeholders = ', '.join(['%s' for _ in range(len(EmployeeList))])
                query += f" AND tev_incoming.id_no IN ({placeholders})"
                params.extend(EmployeeList)
            query += "ORDER BY tev_incoming.id DESC;"

            cursor.execute(query, params)
            columns = [col[0] for col in cursor.description]
            finance_data = [dict(zip(columns, row)) for row in cursor.fetchall()]


    elif _search:
        with connection.cursor() as cursor:
            query = """
                SELECT
                    tev_incoming.id,
                    tev_incoming.code,
                    tev_incoming.first_name,
                    tev_incoming.middle_name,
                    tev_incoming.last_name,
                    tev_incoming.date_travel,
                    tev_incoming.status_id,
                    tev_incoming.original_amount,
                    tev_incoming.final_amount,
                    tev_incoming.incoming_in,
                    tev_incoming.incoming_out,
                    tev_bridge.purpose AS purposes,
                    tev_outgoing.dv_no AS dv_no
                FROM
                    tev_incoming
                INNER JOIN (
                    SELECT
                        MAX(id) AS max_id
                    FROM
                        tev_incoming
                    GROUP BY
                        code
                ) AS latest_ids ON tev_incoming.id = latest_ids.max_id
                LEFT JOIN
                    tev_bridge ON tev_incoming.id = tev_bridge.tev_incoming_id
                LEFT JOIN
                    tev_outgoing ON tev_bridge.tev_outgoing_id = tev_outgoing.id
                WHERE
                    (tev_incoming.code LIKE %s
                    OR tev_incoming.first_name LIKE %s
                    OR tev_incoming.last_name LIKE %s
                    OR tev_outgoing.dv_no LIKE %s)
                    AND (tev_outgoing.dv_no LIKE %s OR dv_no IS NULL)
                ORDER BY
                    tev_incoming.id DESC;
            """
            cursor.execute(query, [f'%{_search}%', f'%{_search}%', f'%{_search}%', f'%{_search}%', f'%{formatted_year}%'])
            columns = [col[0] for col in cursor.description]
            finance_data = [dict(zip(columns, row)) for row in cursor.fetchall()]
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
                WHERE (tev_outgoing.dv_no LIKE %s OR tev_outgoing.dv_no IS NULL)
                ORDER BY tev_incoming.id DESC;
            """, [f'{formatted_year}%'])


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

        finance_query = """
            SELECT ts.dv_no, ts.amt_certified, ts.amt_journal, ts.amt_budget, tc.check_amount, ts.approval_date
            FROM transactions AS ts
            LEFT JOIN trans_check AS tc ON tc.dv_no = ts.dv_no WHERE ts.dv_no = %s
        """
        if row['dv_no']:
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
    allowed_roles = ["Admin", "Incoming staff", "Validating staff"] 
    fullname = ''
    total_amount = 0
    charges_list = []
    data = []  
    
    idd = request.POST.get('dv_id')
    incoming = TevIncoming.objects.filter(id=idd).first()
    query = """ 
        SELECT 
                ti.id, 
                ti.code, 
                ti.id_no,
                ti.original_amount, 
                ti.final_amount, 
                ti.status_id, 
                GROUP_CONCAT(tb.purpose SEPARATOR ', ') AS purposes,
                ti.incoming_in,
                ti.incoming_out,
                CONCAT_WS(' ', ui.first_name, ui.last_name) AS incoming_by,
                ti.date_payrolled,
                CONCAT_WS(' ', pb.first_name, pb.last_name) AS payrolled_by,
                t_o.dv_no, 
                t_o.box_b_out,
                t_o.otg_d_received,
                CONCAT_WS(' ', ot_r.first_name, ot_r.last_name) AS otg_r_user_id,
                t_o.otg_d_forwarded,
                CONCAT_WS(' ', ot_f.first_name, ot_f.last_name) AS otg_out_user_id,
                t_o.b_d_received,
				CONCAT_WS(' ', b_r.first_name, b_r.last_name) AS b_r_user_id,
                t_o.b_d_forwarded,
                CONCAT_WS(' ', b_f.first_name, b_f.last_name) AS b_out_user_id,

                t_o.j_d_received,
				CONCAT_WS(' ', j_r.first_name, j_r.last_name) AS j_r_user_id,
                t_o.j_d_forwarded,
                CONCAT_WS(' ', j_f.first_name, j_f.last_name) AS j_out_user_id,

                t_o.a_d_forwarded,
                CONCAT_WS(' ', ob.first_name, ob.last_name) AS out_by,
                ch.name AS charges, 
                cl.name AS cluster,
                GROUP_CONCAT(t3.name SEPARATOR ', ') AS remarks,
                CONCAT_WS(' ', au.first_name, au.last_name) AS forwarded_by,
                CONCAT_WS(' ', rb.first_name, rb.last_name) AS reviewed_by,
                ti.date_reviewed
        FROM 
                tev_incoming AS ti 
        LEFT JOIN 
                tev_bridge AS tb ON tb.tev_incoming_id = ti.id
        LEFT JOIN 
                tev_outgoing AS t_o ON t_o.id = tb.tev_outgoing_id
        LEFT JOIN 
                charges AS ch ON ch.id = tb.charges_id
        LEFT JOIN 
                cluster AS cl ON cl.id = t_o.cluster
        LEFT JOIN 
				auth_user AS ob ON ob.id = t_o.out_by
        LEFT JOIN 
                remarks_r AS t2 ON t2.incoming_id = ti.id
        LEFT JOIN 
                remarks_lib AS t3 ON t3.id = t2.remarks_lib_id
        LEFT JOIN 
				auth_user AS au ON au.id = ti.forwarded_by
        LEFT JOIN 
				auth_user AS rb ON rb.id = ti.reviewed_by
        LEFT JOIN 
				auth_user AS ui ON ui.id = ti.user_id
        LEFT JOIN 
				auth_user AS pb ON pb.id = ti.payrolled_by
        LEFT JOIN 
				auth_user AS ot_r ON ot_r.id = t_o.otg_r_user_id
        LEFT JOIN 
				auth_user AS ot_f ON ot_f.id = t_o.otg_out_user_id
        LEFT JOIN 
                auth_user AS b_r ON b_r.id = t_o.b_r_user_id
        LEFT JOIN 
                auth_user AS b_f ON b_f.id = t_o.b_out_user_id
        LEFT JOIN 
                auth_user AS j_r ON j_r.id = t_o.j_r_user_id
        LEFT JOIN 
                auth_user AS j_f ON j_f.id = t_o.j_out_user_id
        WHERE 
                ti.code LIKE %s
        GROUP BY 
                ti.id, 
                ti.code, 
                ti.id_no,
                ti.original_amount, 
                ti.final_amount, 
                ti.status_id, 
                ti.remarks, 
                ti.incoming_in,
                ti.incoming_out,
                ti.date_payrolled,
                ti.payrolled_by,
                t_o.dv_no,
                t_o.box_b_out,
                t_o.otg_d_received,
                t_o.otg_r_user_id,
                t_o.otg_d_forwarded, 
                t_o.otg_out_user_id,
                t_o.b_d_received,
				t_o.b_r_user_id,
                t_o.b_d_forwarded,
                t_o.b_out_user_id,
                t_o.j_d_received,
				t_o.j_r_user_id,
                t_o.j_d_forwarded,
                t_o.j_out_user_id,
                t_o.a_d_forwarded,
                t_o.out_by,
                ch.name, 
                cl.name
        ORDER BY 
                ti.id DESC;
    """

    with connection.cursor() as cursor:
        cursor.execute(query, [incoming.code])
        results = cursor.fetchall()


    id_number = incoming.id_no

    def format_date(date_str):
        if date_str is not None:
            if isinstance(date_str, datetime):
                return date_str.strftime("%B %d, %Y %I:%M %p")
            else:
                return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S.%f").strftime("%B %d, %Y %I:%M %p")
        else:
            return ''
        
    for row in results:
        incoming_in = row[7]
        incoming_out = row[8]
        incoming = row[9]
        p_date = row[10]
        box_b_out = row[13]
        otg_d_received = row[14]
        otg_r_by = row[15]
        otg_d_f = row[16]
        otg_f_user_id = row[17]

        budget_d_r = row[18]
        budget_r_by = row[19]
        budget = row[20]
        budget_f_by = row[21]

        journal_d_r = row[22]
        journal_r_by = row[23]
        journal = row[24]
        journal_f_by = row[25]

        approval = row[26]
        forwarded_by = row[31]
        date_reviewed = date(row[33], "F j, Y g:i A")


        item = {
            'id': row[0],
            'code': row[1],
            'id_no': row[2],
            'original_amount': row[3],
            'final_amount': row[4],
            'status': row[5],
            'purpose': row[6], 
            'incoming_in': format_date(incoming_in),
            'incoming_out': format_date(incoming_out),
            'incoming_by': incoming.title(),
            'p_d': format_date(p_date),
            'p_by': row[11],
            'dv_no': row[12],
            'p_d_f': format_date(box_b_out),
            'otg_d_received': format_date(otg_d_received),
            'otg_r_by': otg_r_by.title(),
            'otg_d_f': format_date(otg_d_f),
            'otg_f_user': otg_f_user_id.title(),
            'b_d_r': format_date(budget_d_r),
            'b_r_by': budget_r_by.title(),
            'b_d_f': format_date(budget),
            'b_f_by': budget_f_by.title(),

            'j_d_r': format_date(journal_d_r),
            'j_r_by': journal_r_by.title(),
            'j_d_f': format_date(journal),
            'j_f_by': journal_f_by.title(),

            'a_d_f': format_date(approval),
            'p_f_by': row[27],
            'charges': row[28],
            'cluster': row[29],
            'remarks': row[30], 
            'received_forwarded_by': forwarded_by.title(), 
            'reviewed_by': row[32],
            'date_reviewed': date_reviewed, 
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
    user_id = request.session.get('user_id', 0)
    role_permissions = RolePermissions.objects.filter(user_id=user_id).values('role_id')
    role_details = RoleDetails.objects.filter(id__in=role_permissions).values('role_name')
    role_names = [entry['role_name'] for entry in role_details]
    context = {
        'employee_list' : TevIncoming.objects.filter().order_by('first_name'),
        'permissions' : role_names,
    }
    return render(request, 'tracking/travel_history.html', context)

@csrf_exempt
def export_status(request):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT tev_incoming.id,tev_outgoing.dv_no AS dv_no, tev_incoming.code, tev_incoming.account_no, tev_incoming.id_no,tev_incoming.last_name, tev_incoming.first_name, tev_incoming.middle_name,
                    tev_incoming.date_travel, tev_incoming.division, tev_incoming.section, tev_incoming.status_id, au.first_name AS incoming_by,rb.first_name AS reviewed_by,
                    tev_incoming.original_amount, tev_incoming.final_amount, tev_incoming.incoming_in AS date_actual, tev_incoming.updated_at AS date_entry, tev_incoming.date_reviewed,
                    tev_incoming.incoming_out AS date_reviewed_forwarded, tev_bridge.purpose AS purposes
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
            LEFT JOIN auth_user AS au
            ON au.id = tev_incoming.user_id
            LEFT JOIN auth_user AS rb
            ON rb.id = tev_incoming.reviewed_by
            ORDER BY tev_incoming.id DESC;
        """)
        rows = cursor.fetchall()

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename={date}-TRIS-REPORT.xlsx'.format(
        date=datetime.now().strftime('%Y-%m-%d'),
    )

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = 'REPORT'

    header_font = Font(name='Calibri', bold=True)
    centered_alignment = Alignment(horizontal='center')
    border_bottom = Border(
        bottom=Side(border_style='medium', color='FF000000'),
    )
    wrapped_alignment = Alignment(
        vertical='top',
        wrap_text=True
    )
    columns = [
        'DV NO',
        'CODE',
        'ACCOUNT NO',
        'ID NO',
        'LASTNAME',
        'FIRSTNAME',
        'MIDDLE INITIAL',
        'DATE TRAVEL',
        'DIVISION',
        'SECTION',
        'STATUS ID',
        'INCOMING BY',
        'REVIEWED BY',
        'ORIGINAL AMOUNT',
        'FINAL_AMOUNT',
        'DATE ACTUAL RECEIVED',
        'DATE ENTRY',
        'DATE REVIEWED',
        'DATE REVIEWED FORWARDED',
        'PURPOSE',

    ]
    row_num = 1
    for col_num, column_title in enumerate(columns, 1):
        cell = worksheet.cell(row=row_num, column=col_num)
        cell.value = column_title
        cell.font = header_font
        column_letter = get_column_letter(col_num)
        column_dimensions = worksheet.column_dimensions[column_letter]

    for tris in rows:
        row_num += 1
        row = [
            tris[1],  # dv_no
            tris[2],  # code
            tris[3],  # account_no
            tris[4],  # id_no
            tris[5],  # last_name
            tris[6],  # middle_name
            tris[7],  # first_name
            tris[8],  # date_travel
            tris[9],  # division
            tris[10],  # section
            tris[11],  # status_id
            tris[12],  # incoming_by
            tris[13],  # reviewed_by
            tris[14],  # original_amount
            tris[15],  # final_amount
            tris[16],
            tris[17],
            tris[18],
            tris[19],  
            tris[20],  
        ]       
        for col_num, cell_value in enumerate(row, 1):
            cell = worksheet.cell(row=row_num, column=col_num)
            cell.value = cell_value
            column_letter = get_column_letter(col_num)
            column_dimensions = worksheet.column_dimensions[column_letter]
            column_dimensions.width = 20
    workbook.save(response)
    return response
    # return JsonResponse({'data': 'success'})

# @csrf_exempt
# def export_status(request):
#     tris_queryset = TevIncoming.objects.all()
#     response = HttpResponse(
#         content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
#     )
#     response['Content-Disposition'] = 'attachment; filename={date}-TRIS-REPORT.xlsx'.format(
#         date=datetime.now().strftime('%Y-%m-%d'),
#     )
#     workbook = Workbook()
#     worksheet = workbook.active
#     worksheet.title = 'REPORT'

#     header_font = Font(name='Calibri', bold=True)
#     centered_alignment = Alignment(horizontal='center')
#     border_bottom = Border(
#         bottom=Side(border_style='medium', color='FF000000'),
#     )
#     wrapped_alignment = Alignment(
#         vertical='top',
#         wrap_text=True
#     )
#     columns = [
#         'DV NO',
#         'CODE',
#         'ACCOUNT NO',
#         'ID NO',
#         'FIRSTNAME',
#         'MIDDLENAME',
#         'LASTNAME',
#         'DATE TRAVEL',
#         'DIVISION',
#         'SECTION',
#         'STATUS ID',
#         'INCOMING BY',
#         'REVIEWED BY',
#         'ORIGINAL AMOUNT',
#         'FINAL_AMOUNT',
#         'DATE ACTUAL RECEIVED',
#         'DATE ENTRY',
#         'DATE REVIEWED FORWARDED',
#         'USER ID',
#     ]
#     row_num = 1
#     for col_num, (column_title) in enumerate(columns, 1):
#         cell = worksheet.cell(row=row_num, column=col_num)
#         cell.value = column_title
#         cell.font = header_font
#         column_letter = get_column_letter(col_num)
#         column_dimensions = worksheet.column_dimensions[column_letter]

#     for tris in tris_queryset:
#         row_num += 1
#         row = [
#             tris.dv_no,
#             tris.code,
#             tris.account_no,
#             tris.id_no,
#             tris.first_name,
#             tris.middle_name,
#             tris.last_name,
#             tris.date_travel,
#             tris.division,
#             tris.section,
#             tris.status_id,
#             tris.incoming_by,
#             tris.reviewed_by,
#             tris.original_amount,
#             tris.final_amount,
#             tris.date_actual.astimezone(timezone.utc).replace(tzinfo=None) if tris.incoming_in else None,
#             tris.date_entry.astimezone(timezone.utc).replace(tzinfo=None) if tris.updated_at else None,
#             tris.date_reviewed_forwarded,
#             tris.purposes,
#         ]        
#         for col_num, cell_value in enumerate(row, 1):
#             cell = worksheet.cell(row=row_num, column=col_num)
#             cell.value = cell_value
#             column_letter = get_column_letter(col_num)
#             column_dimensions = worksheet.column_dimensions[column_letter]
#             column_dimensions.width = 19
#     workbook.save(response)
#     return response


# @csrf_exempt
# def export_status(request):
#     tris_queryset = TevIncoming.objects.all()

    
#     response = HttpResponse(
#         content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
#     )
#     response['Content-Disposition'] = 'attachment; filename={date}-TRIS-REPORT.xlsx'.format(
#         date=datetime.now().strftime('%Y-%m-%d'),
#     )
#     workbook = Workbook()
#     worksheet = workbook.active
#     worksheet.title = 'REPORT'

#     header_font = Font(name='Calibri', bold=True)
#     centered_alignment = Alignment(horizontal='center')
#     border_bottom = Border(
#         bottom=Side(border_style='medium', color='FF000000'),
#     )
#     wrapped_alignment = Alignment(
#         vertical='top',
#         wrap_text=True
#     )
#     columns = [
#         'CODE',
#         'FIRSTNAME',
#         'MIDDLENAME',
#         'LASTNAME',
#         'ID NO',
#         'ACCOUNT NO',
#         'DATE TRAVEL',
#         'ORIGINAL AMOUNT',
#         'FINAL_AMOUNT',
#         'DATE ACTUAL RECEIVED',
#         'DATE ENTRY',
#         'DIVISION',
#         'SECTION',
#         'USER ID',
#         'STATUS ID',
#     ]
#     row_num = 1
#     for col_num, (column_title) in enumerate(columns, 1):
#         cell = worksheet.cell(row=row_num, column=col_num)
#         cell.value = column_title
#         cell.font = header_font
#         column_letter = get_column_letter(col_num)
#         column_dimensions = worksheet.column_dimensions[column_letter]

#     for tris in tris_queryset:
#         row_num += 1
#         row = [
#             tris.code,
#             tris.first_name,
#             tris.middle_name,
#             tris.last_name,
#             tris.id_no,
#             tris.account_no,
#             tris.date_travel,
#             tris.original_amount,
#             tris.final_amount,
#             tris.incoming_in.astimezone(timezone.utc).replace(tzinfo=None) if tris.incoming_in else None,
#             tris.updated_at.astimezone(timezone.utc).replace(tzinfo=None) if tris.updated_at else None,
#             tris.division,
#             tris.section,
#             tris.user_id,
#             tris.status_id,
#         ]        
#         for col_num, cell_value in enumerate(row, 1):
#             cell = worksheet.cell(row=row_num, column=col_num)
#             cell.value = cell_value
#             column_letter = get_column_letter(col_num)
#             column_dimensions = worksheet.column_dimensions[column_letter]
#             column_dimensions.width = 17
#     workbook.save(response)
#     return response

@login_required(login_url='login')
@csrf_exempt
def travel_calendar(request):
    allowed_roles = ["Admin", "Incoming staff", "Validating staff","Payroll staff","Certified staff", "End user"] 
    user_id = request.session.get('user_id', 0)
    role_permissions = RolePermissions.objects.filter(user_id=user_id).values('role_id')
    role_details = RoleDetails.objects.filter(id__in=role_permissions).values('role_name')
    role_names = [entry['role_name'] for entry in role_details]


    if any(role_name in allowed_roles for role_name in role_names):
        context = {
            'employee_list' : TevIncoming.objects.filter().order_by('first_name'),
            'permissions' : role_names,
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

    _search = request.GET.get('search[value]')
    _order_dir = request.GET.get('order[0][dir]')
    _order_dash = '-' if _order_dir == 'desc' else ''
    _order_col_num = request.GET.get('order[0][column]')

    search_fields = ['code', 'dv_no'] 
    filter_conditions = Q()

    for field in search_fields:
        filter_conditions |= Q(**{f'{field}__icontains': _search})


    if _search:
        with connection.cursor() as cursor:
            query = """
                SELECT code,first_name,middle_name,last_name,date_travel,ti.status_id,original_amount,final_amount,incoming_in,incoming_out, tb.purpose, dv_no, ti.user_id FROM tev_incoming AS ti 
                LEFT JOIN tev_bridge AS tb ON tb.tev_incoming_id = ti.id
                LEFT JOIN tev_outgoing AS t_o ON t_o.id = tb.tev_outgoing_id
                WHERE ti.id_no = %s AND ti.code LIKE %s
                AND t_o.dv_no LIKE %s AND
                (ti.status_id IN (1, 2, 4, 5 ,6, 7) 
                OR (ti.status_id = 3 AND 
                                (
                                                SELECT COUNT(*)
                                                FROM tev_incoming
                                                WHERE code = ti.code
                                ) = 1
                ));
            """
            cursor.execute(query, [f'{id_number}', f'%{_search}%', f'%{_search}%'])
            columns = [col[0] for col in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
    else:
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









