from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from main.models import (AuthUser, TevIncoming, SystemConfiguration,RoleDetails, StaffDetails, Cluster, Charges, TevOutgoing, TevBridge, Division, RemarksLib, RolePermissions, FareMatrix, MeansofTransportation)
import math
from django.core.serializers import serialize
from django.db import IntegrityError
from decimal import Decimal, InvalidOperation
import datetime as date
from django.db.models import Q, Max
 
@login_required(login_url='login')
def division(request):
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
        return render(request, 'pages/unauthorized.html')

@login_required(login_url='login')
def charges(request):
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
        return render(request, 'pages/unauthorized.html')
    
    
@login_required(login_url='login')
def remarks(request):
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
        return render(request, 'pages/unauthorized.html')
    
@login_required(login_url='login')
def fare_matrix(request):
    allowed_roles = ["Admin", "Incoming staff", "Validating staff", "Payroll staff"] 
    user_id = request.session.get('user_id', 0)
    role_permissions = RolePermissions.objects.filter(user_id=user_id).values('role_id')
    role_details = RoleDetails.objects.filter(id__in=role_permissions).values('role_name')
    role_names = [entry['role_name'] for entry in role_details]
    
    if any(role_name in allowed_roles for role_name in role_names):
        context = {
            'm_o_t' : MeansofTransportation.objects.filter(),
            'permissions' : role_names,
        }
        return render(request, 'libraries/fare_matrix.html', context)
    else:
        return render(request, 'pages/unauthorized.html')
    
@login_required(login_url='login')
def means_of_transportation(request):
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
        return render(request, 'pages/unauthorized.html')
    


    
@csrf_exempt
def division_add(request):
    division = request.POST.get('Division')
    acrym = request.POST.get('Acronym')
    divchief = request.POST.get('Chief')
    ap_designation = request.POST.get('APDesignation')
    approval = request.POST.get('Approval')
    c_designation = request.POST.get('CDesignation')
    user_id = request.session.get('user_id', 0)
    try:
        division_add = Division(name=division,acronym = acrym, chief = divchief,c_designation=c_designation,approval= approval, ap_designation = ap_designation,created_by = user_id)
        division_add.save()
        return JsonResponse({'data': 'success'})
    except IntegrityError as e:
        return JsonResponse({'data': 'error'})
    
    
@csrf_exempt
def division_update(request):
    id = request.POST.get('ItemID')
    division = request.POST.get('Division')
    acrym = request.POST.get('Acronym')
    divchief = request.POST.get('Chief')
    c_designate = request.POST.get('CDesignation')
    approval = request.POST.get('Approval')
    ap_designation = request.POST.get('APDesignation')
    user_id = request.session.get('user_id', 0)

    if Division.objects.filter(name=division, status = 0).exclude(id=id):
        return JsonResponse({'data': 'error', 'message': 'Duplicate Division'})
    else:
        # division_add = Division(name=division,acronym = acrym, chief = divchief,c_designation=c_designate,approval= approval, ap_designation = ap_designation,created_by = user_id, status=0)
        Division.objects.filter(id=id).update(name=division,acronym = acrym, chief = divchief,c_designation=c_designate,approval= approval, ap_designation = ap_designation,created_by = user_id,updated_at =date.datetime.now())

        return JsonResponse({'data': 'success'})
    
def division_edit(request):
    id = request.GET.get('id')
    items = Division.objects.get(pk=id)
    data = serialize("json", [items])
    return HttpResponse(data, content_type="application/json")
    
    
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



@csrf_exempt
def charges_add(request):
    charges = request.POST.get('Charges')
    user_id = request.session.get('user_id', 0)
    charges_add = Charges(name=charges, created_by = user_id)
    try:
        charges_add.save()
        return JsonResponse({'data': 'success'})
    except IntegrityError as e:
        return JsonResponse({'data': 'error'})
    
@csrf_exempt
def charges_update(request):
    id = request.POST.get('ItemID')
    charges = request.POST.get('Charges')


    if Charges.objects.filter(name=charges).exclude(id=id):
        return JsonResponse({'data': 'error', 'message': 'Duplicate Charges'})
    else:
        Charges.objects.filter(id=id).update(name=charges)
        return JsonResponse({'data': 'success'})
    
    
def charges_edit(request):
    id = request.GET.get('id')
    items = Charges.objects.get(pk=id)
    data = serialize("json", [items])
    return HttpResponse(data, content_type="application/json")
    
    
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

@csrf_exempt
def remarks_add(request):
    remarks = request.POST.get('Remarks')
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
    
@csrf_exempt
def remarks_update(request):
    id = request.POST.get('ItemID')
    charges = request.POST.get('Remarks')


    if RemarksLib.objects.filter(name=charges).exclude(id=id):
        return JsonResponse({'data': 'error', 'message': 'Duplicate Remarks'})
    else:
        RemarksLib.objects.filter(id=id).update(name=charges)
        return JsonResponse({'data': 'success'})
    
@csrf_exempt  
def remarks_edit(request):
    id = request.GET.get('id')
    items = RemarksLib.objects.get(pk=id)
    data = serialize("json", [items])
    return HttpResponse(data, content_type="application/json")

@csrf_exempt  
def fare_matrix_edit(request):
    id = request.GET.get('id')
    items = FareMatrix.objects.get(pk=id)
    data = serialize("json", [items])
    return HttpResponse(data, content_type="application/json")

@csrf_exempt  
def means_of_transportation_edit(request):
    id = request.GET.get('id')
    items = MeansofTransportation.objects.get(pk=id)
    data = serialize("json", [items])
    return HttpResponse(data, content_type="application/json")

@csrf_exempt
def remarks_status_edit(request):
    id = request.POST.get('id')
    status_id = request.POST.get('status')
    RemarksLib.objects.filter(pk=id).update(status=status_id)
    return JsonResponse({'data': 'success'})

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

@csrf_exempt
def fare_matrix_add(request):
    def parse_decimal(value):
        try:
            return Decimal(value) if value else None
        except InvalidOperation:
            return None

    ProvinceName = request.POST.get('ProvinceName')
    ProvinceName2 = request.POST.get('ProvinceName2')
    ProvinceAcronym = request.POST.get('ProvinceAcronym2')
    MunicipalityName = request.POST.get('MunicipalityName')
    MunicipalityName2 = request.POST.get('MunicipalityName2')
    BarangayName = request.POST.get('BarangayName')
    BarangayName2 = request.POST.get('BarangayName2')
    PurokName = request.POST.get('PurokName')
    MeansOfTransportation = request.POST.get('MeansOfTransportation')
    RateRegularFare = parse_decimal(request.POST.get('RateRegularFare'))
    HireRateOneWay = parse_decimal(request.POST.get('HireRateOneWay'))
    HireRateWholeDay = parse_decimal(request.POST.get('HireRateWholeDay'))
    EstimatedDurationOfTravel = request.POST.get('EstimatedDurationOfTravel')
    Justification = request.POST.get('Justification')
    DtRemarks = request.POST.get('DtRemarks')
    ProvinceCode = request.POST.get('ProvinceCode')
    MunicipalityCode = request.POST.get('MunicipalityCode')
    BarangayCode = request.POST.get('BarangayCode')

    user_id = request.session.get('user_id', 0)
    try:
        if FareMatrix.objects.filter(
            prov_code=ProvinceCode,
            city_code=MunicipalityCode,
            brgy_code=BarangayCode,
            purok=PurokName,
            means_of_transportation_id = MeansOfTransportation
        ).exists():
            return JsonResponse({'data': 'error', 'message': 'Fare Matrix Already Exist'})
        else:
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
    except IntegrityError as e:
        return JsonResponse({'data': 'error'})
    
@csrf_exempt
def fare_matrix_update(request):
    def parse_decimal(value):
        try:
            return Decimal(value) if value else None
        except InvalidOperation:
            return None

    id = request.POST.get('ItemID')
    ProvinceName = request.POST.get('ProvinceName')
    ProvinceName2 = request.POST.get('ProvinceName2')
    ProvinceAcronym = request.POST.get('ProvinceAcronym2')
    MunicipalityName = request.POST.get('MunicipalityName')
    MunicipalityName2 = request.POST.get('MunicipalityName2')
    BarangayName = request.POST.get('BarangayName')
    BarangayName2 = request.POST.get('BarangayName2')
    PurokName = request.POST.get('PurokName')
    MeansOfTransportation = request.POST.get('MeansOfTransportation')
    RateRegularFare = parse_decimal(request.POST.get('RateRegularFare'))
    HireRateOneWay = parse_decimal(request.POST.get('HireRateOneWay'))
    HireRateWholeDay = parse_decimal(request.POST.get('HireRateWholeDay'))
    EstimatedDurationOfTravel = request.POST.get('EstimatedDurationOfTravel')
    Justification = request.POST.get('Justification')
    DtRemarks = request.POST.get('DtRemarks')
    ProvinceCode = request.POST.get('ProvinceCode')
    MunicipalityCode = request.POST.get('MunicipalityCode')
    BarangayCode = request.POST.get('BarangayCode')
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
    

@csrf_exempt
def means_of_transportation_add(request):
    MotName = request.POST.get('MotName')

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
    
@csrf_exempt
def means_of_transportation_update(request):
    id = request.POST.get('ItemID')
    MotName = request.POST.get('MotName')
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
 
