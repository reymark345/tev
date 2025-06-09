from django.db import models

from datetime import datetime
from django.utils.timezone import now


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class AuthUser(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.IntegerField()
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    is_staff = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'auth_user'


class AuthUserGroups(models.Model):
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_groups'
        unique_together = (('user', 'group'),)


class AuthUserUserPermissions(models.Model):
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_user_permissions'
        unique_together = (('user', 'permission'),)


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.PositiveSmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey(
        'DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'

class Status(models.Model):
    name = models.CharField(max_length=128, blank=True, null=True)
    created_at = models.DateTimeField(default=datetime.now,blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    class Meta:
        managed = True
        db_table = 'status'

class Division(models.Model):
    name = models.CharField(max_length=128, blank=True, null=True)
    acronym = models.CharField(max_length=128, blank=True, null=True)
    chief = models.CharField(max_length=128, blank=True, null=True)
    c_designation = models.CharField(max_length=128, blank=True, null=True)
    approval = models.CharField(max_length=128, blank=True, null=True)
    ap_designation = models.CharField(max_length=128, blank=True, null=True)
    section_head = models.CharField(max_length=128, blank=True, null=True)
    sh_designation = models.CharField(max_length=128, blank=True, null=True)
    created_by = models.IntegerField()
    created_at = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=50, blank=True, null=True, default=0)

    class Meta:
        managed = True
        db_table = 'division'

class Section(models.Model):
    name = models.CharField(max_length=128, blank=True, null=True)
    status = models.CharField(max_length=50, blank=True, null=True, default=0)
    created_by = models.IntegerField()
    created_at = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'section'
        
class TevIncoming(models.Model):
    code = models.CharField(max_length=128, blank=True, null=True)
    first_name = models.CharField(max_length=128, blank=True, null=True)
    middle_name = models.CharField(max_length=128, blank=True, null=True)
    last_name = models.CharField(max_length=128, blank=True, null=True)
    id_no = models.CharField(max_length=128, blank=True, null=True)
    account_no = models.CharField(max_length=128, blank=True, null=True)
    date_travel = models.CharField(max_length=512, blank=True, null=True)
    original_amount = models.DecimalField(max_digits=30, decimal_places=10, blank=True, null=True, default=0)
    final_amount = models.DecimalField(max_digits=30, decimal_places=10, blank=True, null=True , default=0)
    incoming_in = models.DateTimeField(blank=True, null=True)
    incoming_out = models.DateTimeField(blank=True, null=True)
    slashed_out = models.DateTimeField(blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    status = models.ForeignKey(Status, models.DO_NOTHING,default=1)
    user_id = models.CharField(max_length=128, blank=True, null=True)
    date_reviewed = models.DateTimeField(blank=True, null=True)
    reviewed_by = models.CharField(max_length=255, blank=True, null=True)
    forwarded_by = models.CharField(max_length=255, blank=True, null=True)
    contact_no = models.CharField(max_length=255, blank=True, null=True)
    is_upload = models.BooleanField(default=False)
    updated_at = models.DateTimeField(default=datetime.now,blank=True, null=True)
    division = models.CharField(max_length=128, blank=True, null=True)
    section = models.CharField(max_length=128, blank=True, null=True)
    date_payrolled = models.DateTimeField(blank=True, null=True)
    payrolled_by = models.CharField(max_length=255, blank=True, null=True)
    review_date_forwarded = models.DateTimeField(blank=True, null=True)
    review_forwarded_by = models.CharField(max_length=255, blank=True, null=True)
    
    class Meta:
        managed = True
        db_table = 'tev_incoming'
                
class TevOutgoing(models.Model):
    dv_no = models.CharField(max_length=128, blank=True, null=True)
    cluster = models.CharField(max_length=128, blank=True, null=True)
    division = models.ForeignKey(Division, models.DO_NOTHING)
    box_date_out = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    box_b_in = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    box_b_out = models.DateTimeField(blank=True, null=True)
    ard_in = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    ard_out = models.DateTimeField(blank=True, null=True)
    otg_d_received = models.DateTimeField(blank=True, null=True)
    otg_r_user_id = models.CharField(max_length=128, blank=True, null=True)
    otg_d_forwarded = models.DateTimeField(blank=True, null=True)
    otg_out_user_id = models.CharField(max_length=128, blank=True, null=True)
    b_d_received = models.DateTimeField(blank=True, null=True)
    b_r_user_id = models.CharField(max_length=128, blank=True, null=True)
    b_d_forwarded = models.DateTimeField(blank=True, null=True)
    b_out_user_id = models.CharField(max_length=128, blank=True, null=True)
    j_d_received = models.DateTimeField(blank=True, null=True)
    j_r_user_id = models.CharField(max_length=128, blank=True, null=True)
    j_d_forwarded = models.DateTimeField(blank=True, null=True)
    j_out_user_id = models.CharField(max_length=128, blank=True, null=True)
    a_d_received = models.DateTimeField(blank=True, null=True)
    a_r_user_id = models.CharField(max_length=128, blank=True, null=True)
    a_d_forwarded = models.DateTimeField(blank=True, null=True)
    a_out_user_id = models.CharField(max_length=128, blank=True, null=True)
    status = models.ForeignKey(Status, models.DO_NOTHING,default=5)
    user_id = models.CharField(max_length=128, blank=True, null=True)
    out_by = models.CharField(max_length=128, blank=True, null=True)
    is_print = models.BooleanField(default=False)
    
    class Meta:
        managed = True
        db_table = 'tev_outgoing'

class TransactionLogs(models.Model):
    description = models.TextField(blank=True, null=True)
    user_id = models.CharField(max_length=128, blank=True, null=True)
    created_at = models.DateTimeField(default=datetime.now,blank=True, null=True)
    class Meta:
        managed = True
        db_table = 'transaction_logs'
        
class Charges(models.Model):
    name = models.CharField(max_length=128, blank=True, null=True)
    created_by = models.IntegerField()
    created_at = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=50, blank=True, null=True, default=0)

    class Meta:
        managed = True
        db_table = 'charges'
        

        
class TevBridge(models.Model):
    tev_incoming = models.ForeignKey(TevIncoming, models.DO_NOTHING)
    tev_outgoing = models.ForeignKey(TevOutgoing, models.DO_NOTHING)
    charges = models.ForeignKey(Charges, models.DO_NOTHING)
    purpose = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'tev_bridge'
        

        
class RoleDetails(models.Model):
    role_name =  models.CharField(max_length=128, blank=True, null=True)
    created_at = models.DateTimeField(default=datetime.now,blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True, auto_now=True)

    class Meta:
        managed = True
        db_table = 'role_details'
       
class StaffDetails(models.Model):
    user = models.OneToOneField(AuthUser, on_delete=models.CASCADE)
    division = models.ForeignKey(Division, models.DO_NOTHING, default=1)
    id_number = models.CharField(max_length=128, blank=True, null=True)
    section = models.CharField(max_length=128, blank=True, null=True)
    position = models.CharField(max_length=128, blank=True, null=True)
    sex = models.CharField(max_length=128, blank=True, null=True)
    address = models.CharField(max_length=128, blank=True, null=True)
    created_at = models.DateTimeField(default=datetime.now,blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    image_path = models.CharField(max_length=128, blank=True, null=True)
    added_by = models.CharField(max_length=128, blank=True, null=True)
    middle_initial = models.CharField(max_length=128, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'staff_details'


class RolePermissions(models.Model):
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    role = models.ForeignKey(RoleDetails, models.DO_NOTHING)
    created_at = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    class Meta:
        managed = True
        db_table = 'role_permissions'
        
class SystemConfiguration(models.Model):
    name = models.CharField(max_length=128, blank=True, null=True)
    transaction_code = models.CharField(max_length=128, blank=True, null=True)
    year = models.CharField(max_length=128, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    updated_at = models.DateTimeField(blank=True, null=True, auto_now=True)
    date_actual = models.BooleanField(default=True)
    date_limit = models.BooleanField(default=True)
    is_travel_expire = models.BooleanField(default=False)
    days_expire = models.CharField(max_length=128, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'system_configuration'
        
class Cluster(models.Model):
    name = models.CharField(max_length=128, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    class Meta:
        managed = True
        db_table = 'cluster'

class PayrolledCharges(models.Model):
    incoming = models.ForeignKey(TevIncoming, models.DO_NOTHING)
    amount = models.DecimalField(max_digits=30, decimal_places=10, blank=True, null=True , default=0)
    charges = models.ForeignKey(Charges, models.DO_NOTHING)
    created_at = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    class Meta:
        managed = True
        db_table = 'payrolled_charges'

class RemarksLib(models.Model):
    name = models.CharField(max_length=128, blank=True, null=True)
    created_by = models.IntegerField()
    created_at = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    status = models.IntegerField(default=1)

    class Meta:
        managed = True
        db_table = 'remarks_lib'

class Remarks_r(models.Model):
    remarks_lib = models.ForeignKey(RemarksLib, models.DO_NOTHING)
    incoming = models.ForeignKey(TevIncoming, models.DO_NOTHING)
    created_at = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    date = models.DateField(blank=True, null=True)
    class Meta:
        managed = True
        db_table = 'remarks_r'

class Chat(models.Model):
    from_user = models.IntegerField()
    to_user = models.IntegerField()
    message = models.CharField(max_length=50, blank=True, null=True, default=0)
    seen = models.IntegerField(default=0)
    created_at = models.DateTimeField(blank=True, null=True, auto_now_add=True)

    class Meta:
        managed = True
        db_table = 'chat'


class Room(models.Model):
    room_name = models.CharField(max_length=255)

    def __str__(self):
        return self.room_name
    
    def return_room_messages(self):

        return Message.objects.filter(room=self)
    
    def create_new_room_message(self, sender, message):

        new_message = Message(room=self, sender=sender, message=message)
        new_message.save()

class Message(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    sender = models.CharField(max_length=255)
    message = models.TextField()

    def __str__(self):
        return str(self.room)
    
class TravelDestination(models.Model):
    date = models.CharField(max_length=128, blank=True, null=True)
    d_from = models.CharField(max_length=128, blank=True, null=True)
    d_to = models.CharField(max_length=128, blank=True, null=True)
    d_still = models.CharField(max_length=128, blank=True, null=True)
    departure = models.CharField(max_length=128, blank=True, null=True)
    arrival = models.CharField(max_length=128, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'travel_destination'
    
class TravelList(models.Model):
    provinces = models.CharField(max_length=128, blank=True, null=True)
    municipalities = models.CharField(max_length=128, blank=True, null=True)
    purpose = models.TextField(blank=True, null=True)
    created_by = models.CharField(max_length=128, blank=True, null=True)
    created_at = models.DateTimeField(default=datetime.now,blank=True, null=True)
    class Meta:
        managed = True
        db_table = 'travel_list'

class MeansofTransportation(models.Model):
    transportation_name = models.CharField(max_length=128, blank=True, null=True)
    created_by = models.IntegerField()
    created_at = models.DateTimeField(default=datetime.now,blank=True, null=True)
    updated_by = models.IntegerField()
    updated_at = models.DateTimeField(blank=True, null=True)
    class Meta:
        managed = True
        db_table = 'lib_means_of_transportation'


class FareMatrix(models.Model):
    prov_code = models.CharField(max_length=128, blank=True, null=True)
    city_code = models.CharField(max_length=128, blank=True, null=True)
    brgy_code = models.CharField(max_length=128, blank=True, null=True)
    province = models.CharField(max_length=128, blank=True, null=True)
    province_acronym = models.CharField(max_length=128, blank=True, null=True)
    municipality = models.CharField(max_length=128, blank=True, null=True)
    barangay = models.CharField(max_length=255, blank=True, null=True)
    purok = models.CharField(max_length=255, blank=True, null=True)
    means_of_transportation_id = models.CharField(max_length=11, blank=True, null=True)
    rate_regular_fare = models.DecimalField(max_digits=50, decimal_places=10, blank=True, null=True , default=0)
    hire_rate_one_way = models.DecimalField(max_digits=50, decimal_places=10, blank=True, null=True , default=0)
    hire_rate_whole_day = models.DecimalField(max_digits=50, decimal_places=10, blank=True, null=True , default=0)
    estimated_duration_of_travel = models.CharField(max_length=128, blank=True, null=True)
    justification = models.CharField(max_length=255, blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    created_by = models.IntegerField()
    created_at = models.DateTimeField(default=datetime.now,blank=True, null=True)
    updated_by = models.IntegerField()
    updated_at = models.DateTimeField(blank=True, null=True)
    class Meta:
        managed = True
        db_table = 'fare_matrix'


class LibProvinces(models.Model):
    psgc_province = models.IntegerField()
    prov_name = models.CharField(max_length=255, blank=True, null=True)
    psgc_region = models.IntegerField()
    created_at = models.DateTimeField(blank=True, null=True)
    updated_by = models.IntegerField()
    updated_at = models.DateTimeField(blank=True, null=True)
    class Meta:
        managed = True
        db_table = 'lib_provinces'

class LibMunicipalities(models.Model):
    psgc_mun = models.IntegerField()
    mun_name = models.CharField(max_length=255, blank=True, null=True)
    psgc_province = models.IntegerField()
    created_at = models.DateTimeField(blank=True, null=True)
    updated_by = models.IntegerField()
    updated_at = models.DateTimeField(blank=True, null=True)
    class Meta:
        managed = True
        db_table = 'lib_municipalities'

class LibBarangays(models.Model):
    psgc_brgy = models.IntegerField()
    brgy_name = models.CharField(max_length=255, blank=True, null=True)
    psgc_mun = models.IntegerField()
    created_at = models.DateTimeField(blank=True, null=True)
    updated_by = models.IntegerField()
    updated_at = models.DateTimeField(blank=True, null=True)
    class Meta:
        managed = True
        db_table = 'lib_barangays'

class LibProjectSrc(models.Model):
    name = models.CharField(max_length=255, blank=True, null=True)
    cluster_id = models.IntegerField()
    is_active = models.IntegerField()
    is_primary = models.IntegerField()
    created_at = models.DateTimeField(default=now, blank=True, null=True)
    updated_by = models.IntegerField()
    updated_at = models.DateTimeField(blank=True, null=True)
    class Meta:
        managed = True
        db_table = 'lib_project_src'





        
        

        
        


