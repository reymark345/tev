from django.db import models

from datetime import datetime


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
    incoming_in = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    incoming_out = models.DateTimeField(blank=True, null=True)
    slashed_out = models.DateTimeField(blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    status = models.ForeignKey(Status, models.DO_NOTHING,default=1)
    user_id = models.CharField(max_length=128, blank=True, null=True)
    is_upload = models.BooleanField(default=False)
    
    class Meta:
        managed = True
        db_table = 'tev_incoming'
        
class Division(models.Model):
    name = models.CharField(max_length=128, blank=True, null=True)
    acronym = models.CharField(max_length=128, blank=True, null=True)
    chief = models.CharField(max_length=128, blank=True, null=True)
    c_designation = models.CharField(max_length=128, blank=True, null=True)
    approval = models.CharField(max_length=128, blank=True, null=True)
    ap_designation = models.CharField(max_length=128, blank=True, null=True)
    created_by = models.IntegerField()
    created_at = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=50, blank=True, null=True, default=0)

    class Meta:
        managed = True
        db_table = 'division'
        
class TevOutgoing(models.Model):
    dv_no = models.CharField(max_length=128, blank=True, null=True)
    cluster = models.CharField(max_length=128, blank=True, null=True)
    division = models.ForeignKey(Division, models.DO_NOTHING)
    box_date_out = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    box_b_in = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    box_b_out = models.DateTimeField(blank=True, null=True)
    box_c_out = models.DateTimeField(blank=True, null=True)
    ard_in = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    ard_out = models.DateTimeField(blank=True, null=True)
    status = models.ForeignKey(Status, models.DO_NOTHING,default=5)
    user_id = models.CharField(max_length=128, blank=True, null=True)
    out_by = models.CharField(max_length=128, blank=True, null=True)
    is_print = models.BooleanField(default=False)
    
    class Meta:
        managed = True
        db_table = 'tev_outgoing'
        
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
    role = models.ForeignKey(RoleDetails, models.DO_NOTHING)
    id_number = models.CharField(max_length=128, blank=True, null=True)
    division = models.CharField(max_length=128, blank=True, null=True)
    section = models.CharField(max_length=128, blank=True, null=True)
    position = models.CharField(max_length=128, blank=True, null=True)
    sex = models.CharField(max_length=128, blank=True, null=True)
    address = models.CharField(max_length=128, blank=True, null=True)
    created_at = models.DateTimeField(default=datetime.now,blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'staff_details'
        
class SystemConfiguration(models.Model):
    name = models.CharField(max_length=128, blank=True, null=True)
    transaction_code = models.CharField(max_length=128, blank=True, null=True)
    year = models.CharField(max_length=128, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    updated_at = models.DateTimeField(blank=True, null=True, auto_now=True)

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



class RemarksLib(models.Model):
    name = models.CharField(max_length=128, blank=True, null=True)
    created_by = models.IntegerField()
    created_at = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    class Meta:
        managed = True
        db_table = 'remarks_lib'

class Remarks_r(models.Model):
    remarks_lib = models.ForeignKey(RemarksLib, models.DO_NOTHING)
    incoming = models.ForeignKey(TevIncoming, models.DO_NOTHING)
    created_at = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    class Meta:
        managed = True
        db_table = 'remarks_r'
        
        

        
        


