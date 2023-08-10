from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from main.models import (AuthUser, TevIncoming, SystemConfiguration,RoleDetails, StaffDetails, Cluster, Charges, TevOutgoing, TevBridge)



def get_user_details(request):
    return StaffDetails.objects.filter(user_id=request.user.id).first()

@login_required(login_url='login')
def division(request):
    user_details = get_user_details(request)
    allowed_roles = ["Admin", "Incoming staff", "Validating staff"] 
    role = RoleDetails.objects.filter(id=user_details.role_id).first()
    if role.role_name in allowed_roles:
        context = {
            'charges' : Charges.objects.filter().order_by('name'),
            'cluster' : Cluster.objects.filter().order_by('name'),
            'role_permission' : role.role_name,
        }
        return render(request, 'libraries/division.html', context)
    else:
        return render(request, 'pages/unauthorized.html')

@login_required(login_url='login')
def charges(request):
    user_details = get_user_details(request)
    allowed_roles = ["Admin", "Incoming staff", "Validating staff"] 
    role = RoleDetails.objects.filter(id=user_details.role_id).first()
    if role.role_name in allowed_roles:
        context = {
            'charges' : Charges.objects.filter().order_by('name'),
            'cluster' : Cluster.objects.filter().order_by('name'),
            'role_permission' : role.role_name,
        }
        return render(request, 'libraries/charges.html', context)
    else:
        return render(request, 'pages/unauthorized.html')

