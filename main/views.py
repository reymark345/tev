from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from main.models import (RoleDetails, StaffDetails, TevIncoming, TevOutgoing, RolePermissions, Division)
from django.utils.dateparse import parse_date
from django.db.models import Count, Case, When, IntegerField, Subquery
from datetime import timedelta, date


def index(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    else:
        return redirect("landing")
    
@csrf_exempt
def landing(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    return render(request, 'landing_page.html')


@csrf_exempt
def login(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            request.session['user_id'] = user.id
            request.session['username'] = user.username
            request.session['fullname'] = user.first_name + user.last_name
            return redirect("dashboard")
        else:
            messages.error(request, 'Invalid Username and Password.')

    return render(request, 'login.html')


@login_required(login_url='login')
def dashboard(request):
    allowed_roles = ["Admin", "Incoming staff", "Validating staff", "Payroll staff" , "Certified staff"] 
    user_id = request.session.get('user_id', 0)

    role_permissions = RolePermissions.objects.filter(user_id=user_id).values('role_id')
    role_details = RoleDetails.objects.filter(id__in=role_permissions).values('role_name')
    role_names = [entry['role_name'] for entry in role_details]

    uploaded = TevIncoming.objects.filter(is_upload =1).count()
    incoming = TevIncoming.objects.filter(status_id=1).count()
    checking = TevIncoming.objects.filter(status_id=2).count()
    approved = TevIncoming.objects.filter(status_id=7).count()
    duplicated_codes = TevIncoming.objects.values('code').annotate(code_count=Count('code')).filter(code_count__gt=1).values('code')
    returned = TevIncoming.objects.filter(status_id=3).exclude(code__in=Subquery(duplicated_codes)).values('code').distinct().count()
    for_payroll = TevIncoming.objects.filter(status_id=4).count()
    payrolled = TevIncoming.objects.filter(status_id=5).count()
    outgoing = TevIncoming.objects.filter(status_id__in=[8,9]).count()
    ongoing = TevIncoming.objects.filter(status_id=6).count()
    budget = TevIncoming.objects.filter(status_id__in=[10,11]).count()
    journal = TevIncoming.objects.filter(status_id__in=[12,13]).count()
    approval = TevIncoming.objects.filter(status_id__in=[14,15]).count()
    box_a = TevOutgoing.objects.filter().count()

    context = {
        'uploaded': uploaded,
        'user_role': "test",
        'incoming': incoming,
        'checking': checking,
        'approved': approved,
        'returned': returned,
        'payroll': for_payroll,
        'payrolled': payrolled,
        'outgoing': outgoing,
        'budget': budget,
        'journal': journal,
        'approval': approval,
        'ongoing': ongoing,
        'box_a': box_a,
        'permissions' : role_names,
    }
    if any(role_name in allowed_roles for role_name in role_names):
        return render(request, 'dashboard.html',context)
    else:
        return redirect("status")
    
@login_required(login_url='login')
def profile(request):
    allowed_roles = ["Admin", "Incoming staff", "Validating staff", "Payroll staff" , "Certified staff"] 
    user_id = request.session.get('user_id', 0)


    role_permissions = RolePermissions.objects.filter(user_id=user_id).values('role_id')
    role_details = RoleDetails.objects.filter(id__in=role_permissions).values('role_name')
    role_names = [entry['role_name'] for entry in role_details]
    path = StaffDetails.objects.filter(user_id = user_id).first()
    division = Division.objects.filter(id = path.division_id).first()

    context = {
        'id_number': path.id_number, 
        'position': path.position, 
        'sex': path.sex,  
        'division_name': division.name, 
        'image_path': path.image_path,
        'permissions' : role_names,
    }
    if any(role_name in allowed_roles for role_name in role_names):
        return render(request, 'profile.html',context)
    else:
        return redirect("status")
    

    
def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days) + 1):
        yield start_date + timedelta(n)


@login_required(login_url='login')
@csrf_exempt
def generate_accomplishment(request):
    if request.method == 'POST':
        FStartDate = request.POST.get('start_date')
        FEndDate = request.POST.get('end_date')
        start_date = parse_date(FStartDate)
        end_date = parse_date(FEndDate)
        if not start_date or not end_date:
            return JsonResponse({'error': 'Invalid date format'}, status=400)
        user_id = request.session.get('user_id', 0)
        if start_date > end_date:
            return JsonResponse({'error': 'Start date must be before end date'}, status=400)
        results = []
        for single_date in daterange(start_date, end_date):
            day_start = single_date
            day_end = single_date + timedelta(days=1)

            received_count = TevIncoming.objects.filter(
                user_id=user_id,
                incoming_in__range=(day_start, day_end)
            ).count()

            reviewed_count = TevIncoming.objects.filter(
                reviewed_by=user_id,
                date_reviewed__range=(day_start, day_end)
            ).count()

            payrolled_count = TevIncoming.objects.filter(
                payrolled_by=user_id,
                date_payrolled__range=(day_start, day_end)
            ).count()

            results.append({
                'date': single_date.strftime('%B %d, %Y'),
                'received': received_count,
                'reviewed': reviewed_count,
                'payrolled': payrolled_count
            })
        return JsonResponse(results, safe=False)
@csrf_exempt
def logout(request):
    auth_logout(request)
    request.session.flush()
    return redirect("landing")
