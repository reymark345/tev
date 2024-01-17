from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from main.models import (RoleDetails, StaffDetails, TevIncoming, TevOutgoing, RolePermissions)


def get_user_details(request):
    return StaffDetails.objects.filter(user_id=request.user.id).first()


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
   
    user_details = get_user_details(request)
    role = RoleDetails.objects.filter(id=user_details.role_id).first()


    role_permissions = RolePermissions.objects.filter(user_id=user_id).values('role_id')
    role_details = RoleDetails.objects.filter(id__in=role_permissions).values('role_name')
    role_names = [entry['role_name'] for entry in role_details]

    uploaded = TevIncoming.objects.filter(is_upload = 1).count()
    incoming = TevIncoming.objects.filter(status_id=1).count()
    checking = TevIncoming.objects.filter(status_id=2).count()
    approved = TevIncoming.objects.filter(status_id=7).count()
    returned = TevIncoming.objects.filter(status_id=3).count()
    payroll = TevIncoming.objects.filter(status_id=4).count()
    outgoing = TevIncoming.objects.filter(status_id=5).count()
    ongoing = TevIncoming.objects.filter(status_id=6).count()
    box_a = TevOutgoing.objects.filter().count()

    context = {
        'uploaded': uploaded,
        'user_role': role.role_name,
        'incoming': incoming,
        'checking': checking,
        'approved': approved,
        'returned': returned,
        'payroll': payroll,
        'outgoing': outgoing,
        'ongoing': ongoing,
        'box_a': box_a,
        'permissions' : role_names,
    }
    if any(role_name in allowed_roles for role_name in role_names):
        print("halalalala")
        print(role_names)
        return render(request, 'dashboard.html',context)
    else:
        print(role_names)
        print("nononono")
        return redirect("travel-history")
    
    # if role.role_name in allowed_roles:
    #     return render(request, 'dashboard.html',context)
    # else:
    #     return redirect("travel-history")


# @login_required(login_url='login')
# def dashboard(request):
#     allowed_roles = ["Admin", "Incoming staff", "Validating staff"] 
#     user_id = request.session.get('user_id', 0)
   
#     user_details = get_user_details(request)
#     role = RoleDetails.objects.filter(id=user_details.role_id).first()


#     print("testttdawrole")
#     print(user_details.role_id)
#     print(user_id)
#     print("ngii")

#     uploaded = TevIncoming.objects.filter(is_upload = 1).count()
#     incoming = TevIncoming.objects.filter(status_id=1).count()
#     checking = TevIncoming.objects.filter(status_id=2).count()
#     approved = TevIncoming.objects.filter(status_id=7).count()
#     returned = TevIncoming.objects.filter(status_id=3).count()
#     payroll = TevIncoming.objects.filter(status_id=4).count()
#     outgoing = TevIncoming.objects.filter(status_id=5).count()
#     ongoing = TevIncoming.objects.filter(status_id=6).count()
#     box_a = TevOutgoing.objects.filter().count()

#     context = {
#         'uploaded': uploaded,
#         'user_role': role.role_name,
#         'incoming': incoming,
#         'checking': checking,
#         'approved': approved,
#         'returned': returned,
#         'payroll': payroll,
#         'outgoing': outgoing,
#         'ongoing': ongoing,
#         'box_a': box_a,
#         'role_permission' : role.role_name,
#     }
#     if role.role_name in allowed_roles:
#         return render(request, 'dashboard.html',context)
#     else:
#         return redirect("travel-history")

@csrf_exempt
def logout(request):
    auth_logout(request)
    request.session.flush()
    return redirect("landing")
