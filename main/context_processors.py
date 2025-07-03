from main.models import AuthUser

def user_info(request):
    user_id = request.session.get('user_id')
    user = AuthUser.objects.filter(id=user_id).first() if user_id else None
    return {
        'first_name': user.first_name if user else '',
        'last_name': user.last_name if user else '',
        'user_fullname': f"{user.first_name} {user.last_name}" if user else '',
        'user': user,
    }
