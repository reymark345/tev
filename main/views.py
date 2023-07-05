from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages


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
    return render(request, 'dashboard.html')


@csrf_exempt
def logout(request):
    auth_logout(request)
    request.session.flush()
    return redirect("login")
