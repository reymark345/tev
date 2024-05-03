from rest_framework import serializers
from main.models import (TevOutgoing)


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = TevOutgoing
        fields = ['dv_no', 'status_id']