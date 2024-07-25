from rest_framework import serializers
from main.models import (TevOutgoing,TevIncoming)


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = TevOutgoing
        fields = ['dv_no', 'status_id']

class ItemSerializerStatus(serializers.ModelSerializer):
    class Meta:
        model = TevIncoming
        fields = '__all__'