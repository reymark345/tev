from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from main.models import (RoleDetails, StaffDetails)


def get_user_details(request):
    return StaffDetails.objects.filter(user_id=request.user.id).first()


def index(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    else:
        return redirect("login")


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
    allowed_roles = ["Admin", "Incoming staff", "Validating staff"] 
   
    user_details = get_user_details(request)
    role = RoleDetails.objects.filter(id=user_details.role_id).first()
    context = {
        'role_permission' : role.role_name,
    }
    if role.role_name in allowed_roles:
        return render(request, 'dashboard.html',context)
    else:
        return redirect("travel-history")

@csrf_exempt
def logout(request):
    auth_logout(request)
    request.session.flush()
    return redirect("login")
