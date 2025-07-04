from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from main.models import (AuthUser, TevIncoming, SystemConfiguration,RoleDetails, StaffDetails, Cluster, Charges, TevOutgoing, TevBridge, Division, RemarksLib, RolePermissions, FareMatrix, MeansofTransportation, \
                         LibProvinces, LibMunicipalities, LibBarangays)
import math
from django.core.serializers import serialize
from django.db import IntegrityError
from decimal import Decimal, InvalidOperation
import datetime as date
from django.db.models import Q, Max
import json
from django.utils.html import strip_tags
from main.decorators import mfa_required
 
@mfa_required 
def division(request):
    if not request.session.get('user_id') or not request.session.get('mfa_verified'):
        return redirect('login')
    allowed_roles = ["Admin", "Incoming staff", "Validating staff", "Payroll staff"] 
    user_id = request.session.get('user_id', 0)
    role_permissions = RolePermissions.objects.filter(user_id=user_id).values('role_id')
    role_details = RoleDetails.objects.filter(id__in=role_permissions).values('role_name')
    role_names = [entry['role_name'] for entry in role_details]

    if any(role_name in allowed_roles for role_name in role_names):
        context = {
            'division' : Division.objects.filter(status=0).order_by('name'),
            'cluster' : Cluster.objects.filter().order_by('name'),
            'permissions' : role_names,
        }
        return render(request, 'libraries/division.html', context)
    else:
        return redirect('login')

@mfa_required
def charges(request):
    if not request.session.get('user_id') or not request.session.get('mfa_verified'):
        return redirect('login')
    allowed_roles = ["Admin", "Incoming staff", "Validating staff", "Payroll staff"] 
    user_id = request.session.get('user_id', 0)
    role_permissions = RolePermissions.objects.filter(user_id=user_id).values('role_id')
    role_details = RoleDetails.objects.filter(id__in=role_permissions).values('role_name')
    role_names = [entry['role_name'] for entry in role_details]
    if any(role_name in allowed_roles for role_name in role_names):
        context = {
            'charges' : Charges.objects.filter().order_by('name'),
            'cluster' : Cluster.objects.filter().order_by('name'),
            'permissions' : role_names,
        }
        return render(request, 'libraries/charges.html', context)
    else:
        return redirect('login')
    
@mfa_required    
def remarks(request):
    if not request.session.get('user_id') or not request.session.get('mfa_verified'):
        return redirect('login')
    allowed_roles = ["Admin", "Incoming staff", "Validating staff", "Payroll staff"] 
    user_id = request.session.get('user_id', 0)
    role_permissions = RolePermissions.objects.filter(user_id=user_id).values('role_id')
    role_details = RoleDetails.objects.filter(id__in=role_permissions).values('role_name')
    role_names = [entry['role_name'] for entry in role_details]
    
    if any(role_name in allowed_roles for role_name in role_names):
        context = {
            'permissions' : role_names,
        }
        return render(request, 'libraries/remarks.html', context)
    else:
        return redirect('login')

@mfa_required    
def fare_matrix(request):
    if not request.session.get('user_id') or not request.session.get('mfa_verified'):
        return redirect('login')
    allowed_roles = ["Admin", "Incoming staff", "Validating staff", "Payroll staff"] 
    user_id = request.session.get('user_id', 0)
    role_permissions = RolePermissions.objects.filter(user_id=user_id).values('role_id')
    role_details = RoleDetails.objects.filter(id__in=role_permissions).values('role_name')
    role_names = [entry['role_name'] for entry in role_details]

    if any(role_name in allowed_roles for role_name in role_names):
        context = {
            'm_o_t' : MeansofTransportation.objects.filter(),
            'permissions' : role_names,
            'provinces' : LibProvinces.objects.filter(psgc_region = "160000000")
        }
        return render(request, 'libraries/fare_matrix.html', context)
    else:
        return redirect('login')

@mfa_required    
def means_of_transportation(request):
    if not request.session.get('user_id') or not request.session.get('mfa_verified'):
        return redirect('login')
    allowed_roles = ["Admin", "Incoming staff", "Validating staff", "Payroll staff"] 
    user_id = request.session.get('user_id', 0)
    role_permissions = RolePermissions.objects.filter(user_id=user_id).values('role_id')
    role_details = RoleDetails.objects.filter(id__in=role_permissions).values('role_name')
    role_names = [entry['role_name'] for entry in role_details]
    
    if any(role_name in allowed_roles for role_name in role_names):
        context = {
            'permissions' : role_names,
        }
        return render(request, 'libraries/means_of_transportation.html', context)
    else:
        return redirect('login')
    

@mfa_required    
@csrf_exempt
def division_add(request):
    division = strip_tags(request.POST.get('Division'))
    acrym = strip_tags(request.POST.get('Acronym'))
    divchief = strip_tags(request.POST.get('Chief'))
    ap_designation = strip_tags(request.POST.get('APDesignation'))
    approval = strip_tags(request.POST.get('Approval'))
    c_designation = strip_tags(request.POST.get('CDesignation'))
    section_head = strip_tags(request.POST.get('SectionHead'))
    sh_designation = strip_tags(request.POST.get('SHDesignation'))


    user_id = request.session.get('user_id', 0)
    try:
        division_add = Division(name=division,acronym = acrym, chief = divchief,c_designation=c_designation,approval= approval, ap_designation = ap_designation, section_head = section_head, sh_designation = sh_designation, created_by = user_id)
        division_add.save()
        return JsonResponse({'data': 'success'})
    except IntegrityError as e:
        return JsonResponse({'data': 'error'})
    
@mfa_required    
@csrf_exempt
def division_update(request):
    id = request.POST.get('ItemID')
    division = strip_tags(request.POST.get('Division'))
    acrym = strip_tags(request.POST.get('Acronym'))
    divchief = strip_tags(request.POST.get('Chief'))
    c_designate = strip_tags(request.POST.get('CDesignation'))
    approval = strip_tags(request.POST.get('Approval'))
    ap_designation = strip_tags(request.POST.get('APDesignation'))
    section_head = strip_tags(request.POST.get('SectionHead'))
    sh_designation = strip_tags(request.POST.get('SHDesignation'))
    user_id = request.session.get('user_id', 0)
    Division.objects.filter(id=id).update(name=division,acronym = acrym, chief = divchief,c_designation=c_designate,approval= approval, ap_designation = ap_designation,  section_head = section_head, sh_designation = sh_designation, created_by = user_id,updated_at =date.datetime.now())
    return JsonResponse({'data': 'success'})

@mfa_required    
def division_edit(request):
    id = request.GET.get('id')
    items = Division.objects.get(pk=id)
    data = serialize("json", [items])
    return HttpResponse(data, content_type="application/json")
    
@mfa_required    
def division_load(request):
    division_data = Division.objects.select_related().filter().order_by('-created_at')
    total = division_data.count()

    _start = request.GET.get('start')
    _length = request.GET.get('length')
    if _start and _length:
        start = int(_start)
        length = int(_length)
        page = math.ceil(start / length) + 1
        per_page = length

        division_data = division_data[start:start + length]

    data = []

    for item in division_data:
        userData = AuthUser.objects.filter(id=item.created_by)
        full_name = userData[0].first_name + ' ' + userData[0].last_name
        name = item.name
        chief = item.chief
        item = {
            'id': item.id,
            'name': name.upper(),
            'acronym': item.acronym,
            'chief': item.chief,
            'c_designation': item.c_designation,
            'approval': item.approval,
            'ap_designation': item.ap_designation,
            'section_head': item.section_head,
            'sh_designation': item.sh_designation,
            'created_by': full_name,
            'created_at': item.created_at
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
def charges_add(request):
    charges = strip_tags(request.POST.get('Charges'))
    user_id = request.session.get('user_id', 0)
    charges_add = Charges(name=charges, created_by = user_id)
    try:
        charges_add.save()
        return JsonResponse({'data': 'success'})
    except IntegrityError as e:
        return JsonResponse({'data': 'error'})

@mfa_required    
@csrf_exempt
def charges_update(request):
    id = request.POST.get('ItemID')
    charges = strip_tags(request.POST.get('Charges'))
    if Charges.objects.filter(name=charges).exclude(id=id):
        return JsonResponse({'data': 'error', 'message': 'Duplicate Charges'})
    else:
        Charges.objects.filter(id=id).update(name=charges)
        return JsonResponse({'data': 'success'})
    
@mfa_required    
def charges_edit(request):
    id = request.GET.get('id')
    items = Charges.objects.get(pk=id)
    data = serialize("json", [items])
    return HttpResponse(data, content_type="application/json")
    
@mfa_required    
def charges_load(request):
    charges_data = Charges.objects.select_related().order_by('-created_at')
    total = charges_data.count()

    _start = request.GET.get('start')
    _length = request.GET.get('length')
    if _start and _length:
        start = int(_start)
        length = int(_length)
        page = math.ceil(start / length) + 1
        per_page = length

        charges_data = charges_data[start:start + length]

    data = []

    for item in charges_data:
        userData = AuthUser.objects.filter(id=item.created_by)
        full_name = userData[0].first_name + ' ' + userData[0].last_name

        if item.name != "Multiple":
            name = item.name
            item = {
                'id': item.id,
                'name': name.upper(),
                'created_by': full_name.upper(),
                'created_at': item.created_at
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
def remarks_add(request):
    remarks = strip_tags(request.POST.get('Remarks'))
    user_id = request.session.get('user_id', 0)
    try:
        if RemarksLib.objects.filter(name=remarks):
            return JsonResponse({'data': 'error', 'message': 'Remarks Already Taken'})
        else:
            remarks_ = RemarksLib(name=remarks, created_by = user_id)
            remarks_.save()
            return JsonResponse({'data': 'success'})
    except IntegrityError as e:
        return JsonResponse({'data': 'error'})

@mfa_required    
@csrf_exempt
def remarks_update(request):
    id = request.POST.get('ItemID')
    remarks = strip_tags(request.POST.get('Remarks'))
    if RemarksLib.objects.filter(name=remarks).exclude(id=id):
        return JsonResponse({'data': 'error', 'message': 'Duplicate Remarks'})
    else:
        RemarksLib.objects.filter(id=id).update(name=remarks)
        return JsonResponse({'data': 'success'})

@mfa_required    
@csrf_exempt  
def remarks_edit(request):
    id = request.GET.get('id')
    items = RemarksLib.objects.get(pk=id)
    data = serialize("json", [items])
    return HttpResponse(data, content_type="application/json")

@mfa_required
@csrf_exempt  
def fare_matrix_edit(request):
    id = request.GET.get('id')
    items = FareMatrix.objects.get(pk=id)
    data = serialize("json", [items])
    return HttpResponse(data, content_type="application/json")

@mfa_required
@csrf_exempt  
def means_of_transportation_edit(request):
    id = request.GET.get('id')
    items = MeansofTransportation.objects.get(pk=id)
    data = serialize("json", [items])
    return HttpResponse(data, content_type="application/json")

@mfa_required
@csrf_exempt
def remarks_status_edit(request):
    id = request.POST.get('id')
    status_id = request.POST.get('status')
    RemarksLib.objects.filter(pk=id).update(status=status_id)
    return JsonResponse({'data': 'success'})

@mfa_required
def remarks_load(request):
    charges_data = RemarksLib.objects.select_related().order_by('-created_at')
    total = charges_data.count()

    _start = request.GET.get('start')
    _length = request.GET.get('length')
    if _start and _length:
        start = int(_start)
        length = int(_length)
        page = math.ceil(start / length) + 1
        per_page = length

        charges_data = charges_data[start:start + length]

    data = []

    for item in charges_data:
        userData = AuthUser.objects.filter(id=item.created_by)
        full_name = userData[0].first_name + ' ' + userData[0].last_name
        name = item.name
        item = {
            'id': item.id,
            'name': name.upper(),
            'created_by': full_name.upper(),
            'created_at': item.created_at,
            'status': item.status,
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
def fare_matrix_load(request):
    _search = request.GET.get('search[value]', '').strip()
    filter_conditions = Q()
    search_fields = ['province', 'province_acronym', 'municipality', 'barangay', 'purok'] 


    for field in search_fields:
        filter_conditions |= Q(**{f'{field}__icontains': _search})

    if _search:
        fare_matrix_data = FareMatrix.objects.filter(filter_conditions).order_by('-created_at')
    else:
        fare_matrix_data = FareMatrix.objects.filter().order_by('-created_at')

    total = fare_matrix_data.count()

    _start = request.GET.get('start')
    _length = request.GET.get('length')
    if _start and _length:
        start = int(_start)
        length = int(_length)
        page = math.ceil(start / length) + 1
        per_page = length

        fare_matrix_data = fare_matrix_data[start:start + length]

    data = []

    for item in fare_matrix_data:
        userData = AuthUser.objects.filter(id=item.created_by)
        full_name = userData[0].first_name + ' ' + userData[0].last_name
        
        if item.means_of_transportation_id:
            mot = MeansofTransportation.objects.filter(id=item.means_of_transportation_id).first()
            mot_name = mot.transportation_name if mot else None
        else:
            mot_name = None

        item = {
            'id': item.id,
            'province': item.province,
            'province_acronym': item.province_acronym,
            'municipality': item.municipality,
            'barangay': item.barangay,
            'purok': item.purok,
            'rate_regular_fare': item.rate_regular_fare,
            'means_of_transportation': mot_name,
            'hire_rate_one_way': item.hire_rate_one_way,
            'hire_rate_whole_day': item.hire_rate_whole_day,
            'estimated_duration_of_travel': item.estimated_duration_of_travel,
            'justification': item.justification,
            'remarks': item.remarks,
            'created_by': full_name.upper(),
            'created_at': item.created_at
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
def means_of_transportation_load(request):

    _search = request.GET.get('search[value]', '').strip()
    filter_conditions = Q()
    search_fields = ['transportation_name'] 

    for field in search_fields:
        filter_conditions |= Q(**{f'{field}__icontains': _search})

    if _search:
        transpo_data = MeansofTransportation.objects.filter(filter_conditions).order_by('-created_at')
    else:
        transpo_data = MeansofTransportation.objects.filter().order_by('-created_at')

    total = transpo_data.count()

    _start = request.GET.get('start')
    _length = request.GET.get('length')
    if _start and _length:
        start = int(_start)
        length = int(_length)
        page = math.ceil(start / length) + 1
        per_page = length

        transpo_data = transpo_data[start:start + length]

    data = []


    for item in transpo_data:
        userCreatedBy = AuthUser.objects.filter(id=item.created_by).first()
        created_full_name = f"{userCreatedBy.first_name} {userCreatedBy.last_name}".upper() if userCreatedBy else ""

        userUpdatedBy = AuthUser.objects.filter(id=item.updated_by).first()
        updated_full_name = f"{userUpdatedBy.first_name} {userUpdatedBy.last_name}" if userUpdatedBy else ""


        item = {
            'id': item.id,
            'transportation_name': item.transportation_name,
            'created_by': created_full_name,
            'created_at': item.created_at,
            'updated_by': updated_full_name,
            'updated_at': item.updated_at,
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

# @csrf_exempt
# def fare_matrix_add(request):
#     def parse_decimal(value):
#         try:
#             return Decimal(value) if value else None
#         except InvalidOperation:
#             return None

#     ProvinceName = strip_tags(request.POST.get('ProvinceName_'))
#     ProvinceName2 = strip_tags(request.POST.get('ProvinceName2'))
#     ProvinceAcronym = strip_tags(request.POST.get('ProvinceAcronym2'))
#     MunicipalityName = strip_tags(request.POST.get('MunicipalityName'))
#     MunicipalityName2 = strip_tags(request.POST.get('MunicipalityName2'))
#     BarangayName = strip_tags(request.POST.get('BarangayName'))
#     BarangayName2 = strip_tags(request.POST.get('BarangayName2'))
#     PurokName = strip_tags(request.POST.get('PurokName'))
#     MeansOfTransportation = strip_tags(request.POST.get('MeansOfTransportation'))
#     RateRegularFare = strip_tags(parse_decimal(request.POST.get('RateRegularFare')))
#     HireRateOneWay = strip_tags(parse_decimal(request.POST.get('HireRateOneWay')))
#     HireRateWholeDay = strip_tags(parse_decimal(request.POST.get('HireRateWholeDay')))
#     EstimatedDurationOfTravel = strip_tags(request.POST.get('EstimatedDurationOfTravel'))
#     Justification = strip_tags(request.POST.get('Justification'))
#     DtRemarks = strip_tags(request.POST.get('DtRemarks'))
#     ProvinceCode = strip_tags(request.POST.get('ProvinceCode'))
#     MunicipalityCode = strip_tags(request.POST.get('MunicipalityCode'))
#     BarangayCode = strip_tags(request.POST.get('BarangayCode'))
#     user_id = request.session.get('user_id', 0)
#     try:
#         if FareMatrix.objects.filter(
#             prov_code=ProvinceCode,
#             city_code=MunicipalityCode,
#             brgy_code=BarangayCode,
#             purok=PurokName,
#             means_of_transportation_id = MeansOfTransportation
#         ).exists():
#             return JsonResponse({'data': 'error', 'message': 'Fare Matrix Already Exist'})
#         else:
#             fare_matrix = FareMatrix(
#                 prov_code=ProvinceCode,
#                 city_code=MunicipalityCode,
#                 brgy_code=BarangayCode,
#                 province=ProvinceName2,
#                 province_acronym=ProvinceAcronym,
#                 municipality=MunicipalityName2,
#                 barangay=BarangayName2,
#                 purok=PurokName,
#                 means_of_transportation_id=MeansOfTransportation,
#                 rate_regular_fare=RateRegularFare,
#                 hire_rate_one_way=HireRateOneWay,
#                 hire_rate_whole_day=HireRateWholeDay,
#                 estimated_duration_of_travel=EstimatedDurationOfTravel,
#                 justification=Justification,
#                 remarks=DtRemarks,
#                 created_by=user_id,
#                 created_at=date.datetime.now(),
#             )
#             fare_matrix.save()
#             return JsonResponse({'data': 'success'})
#     except IntegrityError as e:
#         return JsonResponse({'data': 'error'})

@mfa_required
@csrf_exempt
def fare_matrix_add(request):
    def parse_decimal(value):
        try:
            return Decimal(value) if value else Decimal('0.00')  # Ensure valid decimal
        except InvalidOperation:
            return Decimal('0.00')  # Fallback to 0.00 if invalid

    # Get and sanitize inputs
    ProvinceName = strip_tags(request.POST.get('ProvinceName_', ''))
    ProvinceName2 = strip_tags(request.POST.get('ProvinceName2', ''))
    ProvinceAcronym = strip_tags(request.POST.get('ProvinceAcronym2', ''))
    MunicipalityName = strip_tags(request.POST.get('MunicipalityName', ''))
    MunicipalityName2 = strip_tags(request.POST.get('MunicipalityName2', ''))
    BarangayName = strip_tags(request.POST.get('BarangayName', ''))
    BarangayName2 = strip_tags(request.POST.get('BarangayName2', ''))
    PurokName = strip_tags(request.POST.get('PurokName', ''))
    MeansOfTransportation = strip_tags(request.POST.get('MeansOfTransportation', ''))
    RateRegularFare = parse_decimal(request.POST.get('RateRegularFare'))
    HireRateOneWay = parse_decimal(request.POST.get('HireRateOneWay'))
    HireRateWholeDay = parse_decimal(request.POST.get('HireRateWholeDay'))
    EstimatedDurationOfTravel = strip_tags(request.POST.get('EstimatedDurationOfTravel', ''))
    Justification = strip_tags(request.POST.get('Justification', ''))
    DtRemarks = strip_tags(request.POST.get('DtRemarks', ''))
    ProvinceCode = strip_tags(request.POST.get('ProvinceCode', ''))
    MunicipalityCode = strip_tags(request.POST.get('MunicipalityCode', ''))
    BarangayCode = strip_tags(request.POST.get('BarangayCode', ''))
    user_id = request.session.get('user_id', 0)

    try:
        if FareMatrix.objects.filter(
            prov_code=ProvinceCode,
            city_code=MunicipalityCode,
            brgy_code=BarangayCode,
            purok=PurokName,
            means_of_transportation_id=MeansOfTransportation
        ).exists():
            return JsonResponse({'data': 'error', 'message': 'Fare Matrix Already Exist'})

        fare_matrix = FareMatrix(
            prov_code=ProvinceCode,
            city_code=MunicipalityCode,
            brgy_code=BarangayCode,
            province=ProvinceName2,
            province_acronym=ProvinceAcronym,
            municipality=MunicipalityName2,
            barangay=BarangayName2,
            purok=PurokName,
            means_of_transportation_id=MeansOfTransportation,
            rate_regular_fare=RateRegularFare,
            hire_rate_one_way=HireRateOneWay,
            hire_rate_whole_day=HireRateWholeDay,
            estimated_duration_of_travel=EstimatedDurationOfTravel,
            justification=Justification,
            remarks=DtRemarks,
            created_by=user_id,
            created_at=date.datetime.now(),
        )
        fare_matrix.save()
        return JsonResponse({'data': 'success'})

    except IntegrityError:
        return JsonResponse({'data': 'error', 'message': 'Database Integrity Error'})
    
@mfa_required
@csrf_exempt
def fare_matrix_update(request):
    def parse_decimal(value):
        try:
            return Decimal(value) if value else None
        except InvalidOperation:
            return None

    id = request.POST.get('ItemID')
    ProvinceName = strip_tags(request.POST.get('ProvinceName'))
    ProvinceName2 = strip_tags(request.POST.get('ProvinceName2'))
    ProvinceAcronym = strip_tags(request.POST.get('ProvinceAcronym2'))
    MunicipalityName = strip_tags(request.POST.get('MunicipalityName'))
    MunicipalityName2 = strip_tags(request.POST.get('MunicipalityName2'))
    BarangayName = strip_tags(request.POST.get('BarangayName'))
    BarangayName2 = strip_tags(request.POST.get('BarangayName2'))
    PurokName = strip_tags(request.POST.get('PurokName'))
    MeansOfTransportation = strip_tags(request.POST.get('MeansOfTransportation'))
    RateRegularFare = strip_tags(parse_decimal(request.POST.get('RateRegularFare')))
    HireRateOneWay = strip_tags(parse_decimal(request.POST.get('HireRateOneWay')))
    HireRateWholeDay = strip_tags(parse_decimal(request.POST.get('HireRateWholeDay')))
    EstimatedDurationOfTravel = strip_tags(request.POST.get('EstimatedDurationOfTravel'))
    Justification = strip_tags(request.POST.get('Justification'))
    DtRemarks = strip_tags(request.POST.get('DtRemarks'))
    ProvinceCode = strip_tags(request.POST.get('ProvinceCode'))
    MunicipalityCode = strip_tags(request.POST.get('MunicipalityCode'))
    BarangayCode = strip_tags(request.POST.get('BarangayCode'))
    user_id = request.session.get('user_id', 0)
    try:
        if FareMatrix.objects.filter(
            prov_code=ProvinceCode,
            city_code=MunicipalityCode,
            brgy_code=BarangayCode,
            purok=PurokName,
            means_of_transportation_id = MeansOfTransportation
        ).exclude(id=id).exists():
            return JsonResponse({'data': 'error', 'message': 'Fare Matrix Already Exist'})
        else:
            FareMatrix.objects.filter(id=id).update(
                prov_code=ProvinceCode,
                city_code=MunicipalityCode,
                brgy_code=BarangayCode,
                province=ProvinceName2,
                province_acronym=ProvinceAcronym,
                municipality=MunicipalityName2,
                barangay=BarangayName2,
                purok=PurokName,
                means_of_transportation_id=MeansOfTransportation,
                rate_regular_fare=RateRegularFare,
                hire_rate_one_way=HireRateOneWay,
                hire_rate_whole_day=HireRateWholeDay,
                estimated_duration_of_travel=EstimatedDurationOfTravel,
                justification=Justification,
                remarks=DtRemarks,
                updated_by=user_id,
                updated_at=date.datetime.now())
            return JsonResponse({'data': 'success'})
    except IntegrityError as e:
        return JsonResponse({'data': 'error'})
    
@mfa_required
@csrf_exempt
def means_of_transportation_add(request):
    MotName = strip_tags(request.POST.get('MotName'))

    user_id = request.session.get('user_id', 0)
    try:
        if MeansofTransportation.objects.filter(
            transportation_name=MotName,
        ).exists():
            return JsonResponse({'data': 'error', 'message': 'Vehicle Already Exist'})
        else:
            mot = MeansofTransportation(
                transportation_name=MotName,
                created_by=user_id,
                created_at=date.datetime.now(),
            )
            mot.save()
            return JsonResponse({'data': 'success'})
    except IntegrityError as e:
        return JsonResponse({'data': 'error'})

@mfa_required    
@csrf_exempt
def means_of_transportation_update(request):
    id = request.POST.get('ItemID')
    MotName = strip_tags(request.POST.get('MotName'))
    user_id = request.session.get('user_id', 0)

    try:
        if MeansofTransportation.objects.filter(
            transportation_name=MotName,
        ).exclude(id=id).exists():
            return JsonResponse({'data': 'error', 'message': 'Vehicle Already Exist'})
        else:
            MeansofTransportation.objects.filter(id=id).update(
                transportation_name=MotName,
                updated_by=user_id,
                updated_at=date.datetime.now())
            return JsonResponse({'data': 'success'})
    except IntegrityError as e:
        return JsonResponse({'data': 'error'})
    



@mfa_required
@csrf_exempt
def get_lib_mun(request):
    if request.method == "GET":
        prov_id = request.GET.get('prov_id')
        if not prov_id:
            return JsonResponse({'message': 'prov_id is required'}, status=400)
     
        data = LibMunicipalities.objects.filter(psgc_province=prov_id)
        serialized_data = json.loads(serialize('json', data))
        return JsonResponse({'data': serialized_data, 'message': 'success'}, status=200)

    else:
        return JsonResponse({'message': 'Invalid HTTP method. Only GET is allowed.'}, status=405)

@mfa_required    
@csrf_exempt
def get_lib_brgy(request):
    if request.method == "GET":
        mun_id = request.GET.get('mun_id')
        if not mun_id:
            return JsonResponse({'message': 'mun_id is required'}, status=400)

        data = LibBarangays.objects.filter(psgc_mun=mun_id)
        serialized_data = json.loads(serialize('json', data))
        return JsonResponse({'data': serialized_data, 'message': 'success'}, status=200)

    else:
        return JsonResponse({'message': 'Invalid HTTP method. Only GET is allowed.'}, status=405)

