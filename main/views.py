from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from main.models import (RoleDetails, StaffDetails, TevIncoming, TevOutgoing, TevBridge, RolePermissions, Division, AuthUser, Charges, PayrolledCharges)
from django.utils.dateparse import parse_date
from django.db.models import Count, Case, When, IntegerField, Subquery
from datetime import timedelta, date
from django.db.models.functions import TruncMonth
from django.db.models import Q
import datetime
from .forms import LoginForm, OTPForm
from django.conf import settings
import requests
import pyotp
import qrcode
import io
from main.decorators import mfa_required


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
    if request.session.get('user_id') and request.session.get('mfa_verified'):
        return redirect("dashboard")

    if request.method == 'POST':
        form = LoginForm(request.POST)
        recaptcha_token = request.POST.get('g-recaptcha-response')
        recaptcha_response = requests.post(
            settings.RECAPTCHA_VERIFY_URL,
            data={
                'secret': settings.RECAPTCHA_SECRET_KEY,
                'response': recaptcha_token
            }
        )
        recaptcha_result = recaptcha_response.json()
        if not (recaptcha_result.get('success') and recaptcha_result.get('score', 0) > 0.5):
            messages.error(request, 'CAPTCHA validation failed, Try again.')
            return render(request, 'login.html', {'form': form})
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                mfa_status = AuthUser.objects.filter(username=username).values_list('mfa_enabled', flat=True).first()
                request.session['user_id'] = user.id
                request.session['username'] = user.username
                request.session['fullname'] = user.first_name + user.last_name
                if mfa_status:
                    request.session['pre_2fa_user_id'] = user.id
                    return redirect('mfa-verify')
                else:
                    request.session['mfa_verified'] = True
                    return redirect('dashboard')
            else:
                messages.error(request, 'Invalid Username or Password.')
        else:
            messages.error(request, 'Form validation failed.')
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})




def dashboard(request):
    # Custom session check for MFA
    if not request.session.get('user_id') or not request.session.get('mfa_verified'):
        return redirect('login')

    allowed_roles = ["Admin", "Incoming staff", "Validating staff", "Payroll staff" , "Certified staff"] 
    user_id = request.session.get('user_id', 0)
    year = datetime.datetime.now().year
 
    role_permissions = RolePermissions.objects.filter(user_id=user_id).values('role_id')
    role_details = RoleDetails.objects.filter(id__in=role_permissions).values('role_name')
    role_names = [entry['role_name'] for entry in role_details]

    uploaded = TevIncoming.objects.filter(is_upload =1, incoming_in__year=year).count()
    incoming = TevIncoming.objects.filter(status_id=1, incoming_in__year=year).count()
    checking = TevIncoming.objects.filter(status_id=2, incoming_in__year=year).count()
    approved = TevIncoming.objects.filter(status_id=7, incoming_in__year=year).count()
    duplicated_codes = TevIncoming.objects.values('code').annotate(code_count=Count('code')).filter(code_count__gt=1, incoming_in__year=year).values('code')
    returned = TevIncoming.objects.filter(status_id=3, incoming_in__year=year).exclude(code__in=Subquery(duplicated_codes)).values('code').distinct().count()
    for_payroll = TevIncoming.objects.filter(status_id=4, incoming_in__year=year).count()
    payrolled = TevIncoming.objects.filter(status_id=5, incoming_in__year=year).count()
    outgoing = TevIncoming.objects.filter(status_id__in=[8,9], incoming_in__year=year).count()
    ongoing = TevIncoming.objects.filter(status_id=6, incoming_in__year=year).count()
    budget = TevIncoming.objects.filter(status_id__in=[10,11], incoming_in__year=year).count()
    journal = TevIncoming.objects.filter(status_id__in=[12,13], incoming_in__year=year).count()
    approval = TevIncoming.objects.filter(status_id__in=[14,15], incoming_in__year=year).count()
    box_a = TevOutgoing.objects.filter().count()

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

    # donut chart
    c_list = list(Charges.objects.order_by('id').values_list('name', flat=True))
    p_charges_counts = PayrolledCharges.objects.values('charges_id').annotate(count=Count('charges_id')).order_by('charges_id')
    p_counts_list = list(p_charges_counts.values_list('count', flat=True))
    #end

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
        'charges_list': c_list,
        'payroll_c_list': p_counts_list,
        'users' : AuthUser.objects.filter().exclude(id=1).order_by('first_name').select_related(),
        'current_year' : year
    }
    if any(role_name in allowed_roles for role_name in role_names):
        return render(request, 'dashboard.html',context)
    
    elif "Administrative" in role_names:
        return redirect("status")
        
    elif "Budget staff" in role_names:
        return redirect("budget-list")  
    
    elif "Approval staff" in role_names:
        return redirect("approval-list")  
    else:
        return redirect("travel-history")
    

@csrf_exempt
def view_stats_year(request):
    if not request.session.get('user_id') or not request.session.get('mfa_verified'):
        return redirect('login')

    if request.method == 'POST':
        year = request.POST.get('year')

        user_id = request.session.get('user_id', 0)

        role_permissions = RolePermissions.objects.filter(user_id=user_id).values('role_id')
        role_details = RoleDetails.objects.filter(id__in=role_permissions).values('role_name')
        role_names = [entry['role_name'] for entry in role_details]

        uploaded = TevIncoming.objects.filter(is_upload =1,incoming_in__year=year).count()
        incoming = TevIncoming.objects.filter(status_id=1,incoming_in__year=year).count()
        checking = TevIncoming.objects.filter(status_id=2,incoming_in__year=year).count()
        approved = TevIncoming.objects.filter(status_id=7,incoming_in__year=year).count()
        duplicated_codes = TevIncoming.objects.values('code').annotate(code_count=Count('code')).filter(code_count__gt=1,incoming_in__year=year).values('code')
        returned = TevIncoming.objects.filter(status_id=3,incoming_in__year=year).exclude(code__in=Subquery(duplicated_codes)).values('code').distinct().count()
        for_payroll = TevIncoming.objects.filter(status_id=4,incoming_in__year=year).count()
        payrolled = TevIncoming.objects.filter(status_id=5,incoming_in__year=year).count()
        outgoing = TevIncoming.objects.filter(status_id__in=[8,9],incoming_in__year=year).count()
        ongoing = TevIncoming.objects.filter(status_id=6,incoming_in__year=year).count()
        budget = TevIncoming.objects.filter(status_id__in=[10,11],incoming_in__year=year).count()
        journal = TevIncoming.objects.filter(status_id__in=[12,13],incoming_in__year=year).count()
        approval = TevIncoming.objects.filter(status_id__in=[14,15],incoming_in__year=year).count()
        box_a = TevOutgoing.objects.filter().count()

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

        return JsonResponse({
            'received_counts': received_counts,
            'reviewed_counts': reviewed_counts,
            'payrolled_counts': payrolled_counts,
            'outgoing_counts': outgoing_counts,
            'budget_counts': budget_counts,
            'journal_counts': journal_counts,
            'approval_counts': approval_counts,
            'returned_counts': returned_counts,
            'uploaded': uploaded,
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
            'permissions' : role_names
        })

@mfa_required
def profile(request):
    if not request.session.get('user_id') or not request.session.get('mfa_verified'):
        print('DEBUG: Not authenticated or MFA not verified, redirecting to login')
        return redirect('login')
    allowed_roles = ["Admin", "Incoming staff", "Validating staff", "Payroll staff", "Certified staff"]
    user_id = request.session.get('user_id', 0)
    role_permissions = RolePermissions.objects.filter(user_id=user_id).values('role_id')
    role_details = RoleDetails.objects.filter(id__in=role_permissions).values('role_name')
    role_names = [entry['role_name'] for entry in role_details]

    path = StaffDetails.objects.filter(user_id=user_id).first()
    division = Division.objects.filter(id=path.division_id).first() if path else None
    tris_staff = AuthUser.objects.filter(is_staff=1).exclude(id__in=[1,2,24])
    for user in tris_staff:
        user.first_name = user.first_name.title()
        user.last_name = user.last_name.title()
    context = {
        'staff': tris_staff,
        'id_number': getattr(path, 'id_number', ''),
        'position': getattr(path, 'position', ''),
        'sex': getattr(path, 'sex', ''),
        'division_name': getattr(division, 'name', ''),
        'image_path': getattr(path, 'image_path', ''),
        'permissions': role_names,
    }
    if "Admin" in role_names:

        return render(request, 'admin_profile.html', context)
    elif any(role_name in allowed_roles for role_name in role_names):
        return render(request, 'profile.html', context)
    elif ("Administrative" in role_names or "Claimant" in role_names or
          "Approval staff" in role_names or "Budget staff" in role_names):
        return render(request, 'aa_profile.html', context)
    else:
        return redirect('login')
    
    

    
def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days) + 1):
        yield start_date + timedelta(n)

@mfa_required
@csrf_exempt
def generate_accomplishment(request):
    if not request.session.get('user_id') or not request.session.get('mfa_verified'):
        return redirect('login')
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
    
@mfa_required
@csrf_exempt
def generate_accomplishment_admin(request):
    if not request.session.get('user_id') or not request.session.get('mfa_verified'):
        return redirect('login')
    if request.method == 'POST':
        FStartDate = request.POST.get('start_date')
        FEndDate = request.POST.get('end_date')
        start_date = parse_date(FStartDate)
        end_date = parse_date(FEndDate)
        userId = request.POST.get('user_id')
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
                user_id=userId,
                updated_at__range=(day_start, day_end)
            ).count()
            

            reviewed_count = TevIncoming.objects.filter(
                reviewed_by=userId,
                date_reviewed__range=(day_start, day_end)
            ).count()

            payrolled_count = TevIncoming.objects.filter(
                payrolled_by=userId,
                date_payrolled__range=(day_start, day_end)
            ).count()

            results.append({
                'date': single_date.strftime('%B %d, %Y'),
                'received': received_count,
                'reviewed': reviewed_count,
                'payrolled': payrolled_count
            })
        return JsonResponse(results, safe=False)
    
def mfa_setup(request):
    user = request.user
    if not hasattr(user, 'otp_secret') or not user.otp_secret:
        otp_secret = pyotp.random_base32()
        user.otp_secret = otp_secret
        user.save()
    else:
        otp_secret = user.otp_secret
    otp_uri = pyotp.totp.TOTP(otp_secret).provisioning_uri(name=user.username, issuer_name="TRIPS")
    img = qrcode.make(otp_uri)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    image_stream = buf.getvalue()
    return HttpResponse(image_stream, content_type="image/png")


def mfa_verify(request):
    user_id = request.session.get('pre_2fa_user_id')
    if not user_id:
        return redirect('login')
    user = AuthUser.objects.get(id=user_id)
    if not user.otp_secret:
        otp_secret = pyotp.random_base32()
        user.otp_secret = otp_secret
        user.save()
    if request.method == 'POST':
        form = OTPForm(request.POST)
        if form.is_valid():
            otp_token = form.cleaned_data['otp_token']
            totp = pyotp.TOTP(user.otp_secret)
            if totp.verify(otp_token):
                request.session['mfa_verified'] = True
                if 'pre_2fa_user_id' in request.session:
                    del request.session['pre_2fa_user_id']
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid authentication code.')
        else:
            messages.error(request, 'Invalid form.')
    else:
        form = OTPForm()
    otp_uri = pyotp.totp.TOTP(user.otp_secret).provisioning_uri(name=user.username, issuer_name="TRIPS")
    import base64
    import qrcode
    import io
    img = qrcode.make(otp_uri)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    qr_url = 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode('utf-8')
    return render(request, 'mfa_verify.html', {'form': form, 'qr_url': qr_url})




def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days) + 1):
        yield start_date + timedelta(n)
    
@csrf_exempt
def logout(request):
    auth_logout(request)
    request.session.flush()
    return redirect("landing")
