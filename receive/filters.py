#filters.py
from django.contrib.auth.models import User
# from .models import 
from main.models import (AuthUser, TevIncoming, SystemConfiguration,RoleDetails, StaffDetails, TevOutgoing, TevBridge)
import django_filters


class UserFilter(django_filters.FilterSet):
    class Meta:
        model = TevIncoming
        fields = ['first_name']
