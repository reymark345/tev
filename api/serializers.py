from rest_framework import serializers
from main.models import (TevOutgoing,TevIncoming)


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = TevOutgoing
        fields = ['dv_no', 'status_id']

class ItemSerializerStatus(serializers.Serializer):
    id = serializers.IntegerField()
    code = serializers.CharField(max_length=100)
    first_name = serializers.CharField(max_length=100)
    middle_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    id_no = serializers.CharField(max_length=100)
    original_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    final_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    status = serializers.CharField(max_length=100)
    purposes = serializers.CharField()
    incoming_in = serializers.DateTimeField()
    incoming_out = serializers.DateTimeField()
    incoming_by = serializers.CharField(max_length=255)
    date_payrolled = serializers.DateTimeField()
    payrolled_by = serializers.CharField(max_length=255)
    dv_no = serializers.CharField(max_length=100)
    box_b_out = serializers.DateTimeField()
    otg_d_received = serializers.DateTimeField()
    otg_r_user_id = serializers.CharField(max_length=255)
    otg_d_forwarded = serializers.DateTimeField()
    otg_out_user_id = serializers.CharField(max_length=255)
    b_d_received = serializers.DateTimeField()
    b_r_user_id = serializers.CharField(max_length=255)
    b_d_forwarded = serializers.DateTimeField()
    b_out_user_id = serializers.CharField(max_length=255)
    j_d_received = serializers.DateTimeField()
    j_r_user_id = serializers.CharField(max_length=255)
    j_d_forwarded = serializers.DateTimeField()
    j_out_user_id = serializers.CharField(max_length=255)
    a_d_received = serializers.DateTimeField()
    a_r_user_id = serializers.CharField(max_length=255)
    a_d_forwarded = serializers.DateTimeField()
    a_out_user_id = serializers.CharField(max_length=255)
    out_by = serializers.CharField(max_length=255)
    charges = serializers.CharField(max_length=255)
    cluster = serializers.CharField(max_length=255)
    remarks = serializers.CharField()
    forwarded_by = serializers.CharField(max_length=255)
    reviewed_by = serializers.CharField(max_length=255)
    date_reviewed = serializers.DateTimeField()

# class ItemSerializerStatus(serializers.ModelSerializer):
#     class Meta:
#         model = TevIncoming
#         fields = '__all__'