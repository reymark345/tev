from functools import wraps
from django.shortcuts import redirect
from django.http import HttpRequest

def mfa_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not isinstance(request, HttpRequest):
            return view_func(request, *args, **kwargs)
        if not request.session.get('user_id') or not request.session.get('mfa_verified'):
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view
