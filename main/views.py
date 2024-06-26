from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from main.models import (RoleDetails, StaffDetails, TevIncoming, TevOutgoing, TevBridge, RolePermissions, Division)
from django.utils.dateparse import parse_date
from django.db.models import Count, Case, When, IntegerField, Subquery
from datetime import timedelta, date
from django.db.models.functions import TruncMonth
from django.db.models import Q


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

    year = int("2024")

    received = TevIncoming.objects.filter(
        incoming_in__year=year
    )

    reviewed = TevIncoming.objects.filter(
        Q(date_reviewed__isnull=False) & Q(date_reviewed__year=year)
    )

    returned_ = TevIncoming.objects.filter(
        status_id=3,
        date_reviewed__isnull=False,
        date_reviewed__year=year
    ).exclude(code__in=Subquery(duplicated_codes)).values('code').distinct()


    payrolled_ = TevIncoming.objects.filter(
        date_payrolled__year=year
    )

    outgoing_monthly_counts = TevBridge.objects.filter(
        tev_outgoing__otg_d_received__year=year
    ).annotate(
        month=TruncMonth('tev_outgoing__otg_d_received')
    ).values('month').annotate(count=Count('tev_outgoing__id')).order_by('month')

    budget_monthly_counts = TevBridge.objects.filter(
        tev_outgoing__b_d_received__year=year
    ).annotate(
        month=TruncMonth('tev_outgoing__b_d_received')
    ).values('month').annotate(count=Count('tev_outgoing__id')).order_by('month')

    journal_monthly_counts = TevBridge.objects.filter(
        tev_outgoing__j_d_received__year=year
    ).annotate(
        month=TruncMonth('tev_outgoing__j_d_received')
    ).values('month').annotate(count=Count('tev_outgoing__id')).order_by('month')

    approval_monthly_counts = TevBridge.objects.filter(
        tev_outgoing__a_d_received__year=year
    ).annotate(
        month=TruncMonth('tev_outgoing__a_d_received')
    ).values('month').annotate(count=Count('tev_outgoing__id')).order_by('month')


    received_monthly_counts = received.annotate(month=TruncMonth('incoming_in')).values('month').annotate(count=Count('id')).order_by('month')
    reviewed_monthly_counts = reviewed.annotate(month=TruncMonth('date_reviewed')).values('month').annotate(count=Count('id')).order_by('month')

    returned_monthly_counts = TevIncoming.objects.filter(
        code__in=Subquery(returned_),
        status_id=3,
        date_reviewed__year=year
    ).annotate(month=TruncMonth('date_reviewed')).values('month').annotate(count=Count('id')).order_by('month')

    payrolled_monthly_counts = payrolled_.annotate(month=TruncMonth('date_payrolled')).values('month').annotate(count=Count('id')).order_by('month')

    received_counts = [0] * 12
    reviewed_counts = [0] * 12
    returned_counts = [0] * 12
    payrolled_counts = [0] * 12
    outgoing_counts = [0] * 12
    budget_counts = [0] * 12
    journal_counts = [0] * 12
    approval_counts = [0] * 12

    for entry in received_monthly_counts:
        month = entry['month'].month
        received_counts[month - 1] = entry['count']

    for entry in reviewed_monthly_counts:
        month = entry['month'].month
        reviewed_counts[month - 1] = entry['count']
    
    for entry in returned_monthly_counts:
        month = entry['month'].month
        returned_counts[month - 1] = entry['count']

    for entry in payrolled_monthly_counts:
        month = entry['month'].month
        payrolled_counts[month - 1] = entry['count']

    for entry in outgoing_monthly_counts:
        month = entry['month'].month
        outgoing_counts[month - 1] = entry['count']

    for entry in budget_monthly_counts:
        month = entry['month'].month
        budget_counts[month - 1] = entry['count']

    for entry in journal_monthly_counts:
        month = entry['month'].month
        journal_counts[month - 1] = entry['count']

    for entry in approval_monthly_counts:
        month = entry['month'].month
        approval_counts[month - 1] = entry['count']

    context = {
        'received_counts': received_counts,
        'reviewed_counts': reviewed_counts,
        'returned_counts': returned_counts,
        'payrolled_counts': payrolled_counts,
        'outgoing_counts': outgoing_counts,
        'budget_counts': budget_counts,
        'journal_counts': journal_counts,
        'approval_counts': approval_counts,
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

    if "Admin" in role_names:
        return render(request, 'admin_profile.html',context) 
    elif any(role_name in allowed_roles for role_name in role_names):
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
                updated_at__range=(day_start, day_end)
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

@login_required(login_url='login')
@csrf_exempt
def generate_accomplishment_admin(request):
    if request.method == 'POST':
        FStartDate = request.POST.get('start_date')
        FEndDate = request.POST.get('end_date')

        start_date = parse_date(FStartDate)
        end_date = parse_date(FEndDate)
        if not start_date or not end_date:
            return JsonResponse({'error': 'Invalid date format'}, status=400)
        if start_date > end_date:
            return JsonResponse({'error': 'Start date must be before end date'}, status=400)
        results = []
        for single_date in daterange(start_date, end_date):
            day_start = single_date
            day_end = single_date + timedelta(days=1)

            # sonny count start
            received_count_sonny = TevIncoming.objects.filter(
                user_id=5,
                updated_at__range=(day_start, day_end)
            ).count()

            reviewed_count_sonny = TevIncoming.objects.filter(
                reviewed_by=5,
                date_reviewed__range=(day_start, day_end)
            ).count()

            payrolled_count_sonny = TevIncoming.objects.filter(
                payrolled_by=5,
                date_payrolled__range=(day_start, day_end)
            ).count()
            # end

            # carl count start
            received_count_carl = TevIncoming.objects.filter(
                user_id=3,
                updated_at__range=(day_start, day_end)
            ).count()

            reviewed_count_carl = TevIncoming.objects.filter(
                reviewed_by=3,
                date_reviewed__range=(day_start, day_end)
            ).count()

            payrolled_count_carl = TevIncoming.objects.filter(
                payrolled_by=3,
                date_payrolled__range=(day_start, day_end)
            ).count()
            # end

            # jhoannah count start
            received_count_jhoannah = TevIncoming.objects.filter(
                user_id=6,
                updated_at__range=(day_start, day_end)
            ).count()

            reviewed_count_jhoannah = TevIncoming.objects.filter(
                reviewed_by=6,
                date_reviewed__range=(day_start, day_end)
            ).count()

            payrolled_count_jhoannah = TevIncoming.objects.filter(
                payrolled_by=6,
                date_payrolled__range=(day_start, day_end)
            ).count()
            # end

            # bernard count start
            received_count_bernard = TevIncoming.objects.filter(
                user_id=4,
                updated_at__range=(day_start, day_end)
            ).count()

            reviewed_count_bernard = TevIncoming.objects.filter(
                reviewed_by=4,
                date_reviewed__range=(day_start, day_end)
            ).count()

            payrolled_count_bernard = TevIncoming.objects.filter(
                payrolled_by=4,
                date_payrolled__range=(day_start, day_end)
            ).count()
            # end
            results.append({
                'date': single_date.strftime('%B %d, %Y'),
                'received_sonny': received_count_sonny,
                'reviewed_sonny': reviewed_count_sonny,
                'payrolled_sonny': payrolled_count_sonny,
                'received_carl': received_count_carl,
                'reviewed_carl': reviewed_count_carl,
                'payrolled_carl': payrolled_count_carl,
                'received_jhoannah': received_count_jhoannah,
                'reviewed_jhoannah': reviewed_count_jhoannah,
                'payrolled_jhoannah': payrolled_count_jhoannah,
                'received_bernard': received_count_bernard,
                'reviewed_bernard': reviewed_count_bernard,
                'payrolled_bernard': payrolled_count_bernard
            })
        return JsonResponse(results, safe=False)
    
@csrf_exempt
def logout(request):
    auth_logout(request)
    request.session.flush()
    return redirect("landing")
