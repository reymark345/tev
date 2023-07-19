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
        
class TevIncoming(models.Model):
    code = models.CharField(max_length=128, blank=True, null=True)
    name = models.CharField(max_length=128, blank=True, null=True)
    id_no = models.CharField(max_length=128, blank=True, null=True)
    original_amount = models.DecimalField(max_digits=30, decimal_places=10, blank=True, null=True)
    final_amount = models.DecimalField(max_digits=30, decimal_places=10, blank=True, null=True , default=0)
    incoming_in = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    incoming_out = models.DateTimeField(blank=True, null=True)
    slashed_out = models.DateTimeField(blank=True, null=True)
    remarks = models.CharField(max_length=128, blank=True, null=True)
    purpose = models.CharField(max_length=255, blank=True, null=True)
    status = models.IntegerField(max_length=128, blank=True, null=True,default=1)
    user_id = models.CharField(max_length=128, blank=True, null=True)
    
    class Meta:
        managed = True
        db_table = 'tev_incoming'
        
class TevOutgoing(models.Model):
    dv_no = models.CharField(max_length=128, blank=True, null=True)
    cluster = models.CharField(max_length=128, blank=True, null=True)
    responsibility_center = models.CharField(max_length=128, blank=True, null=True)
    box_date_out = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    box_b_in = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    box_b_out = models.DateTimeField(blank=True, null=True)
    box_c_out = models.DateTimeField(blank=True, null=True)
    ard_in = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    ard_out = models.DateTimeField(blank=True, null=True)
    user_id = models.CharField(max_length=128, blank=True, null=True)
    
    class Meta:
        managed = True
        db_table = 'tev_outgoing'
        
class Charges(models.Model):
    name = models.CharField(max_length=128, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'charges'
        
class tev_bridge(models.Model):
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
    role = models.ForeignKey(RoleDetails, models.DO_NOTHING)
    division = models.CharField(max_length=128, blank=True, null=True)
    section = models.CharField(max_length=128, blank=True, null=True)
    position = models.CharField(max_length=128, blank=True, null=True)
    sex = models.CharField(max_length=128, blank=True, null=True)
    address = models.CharField(max_length=128, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    user_id = models.BigIntegerField(unique=True)

    class Meta:
        managed = True
        db_table = 'staff_details'
        
class Status(models.Model):
    name = models.CharField(max_length=128, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    class Meta:
        managed = True
        db_table = 'status'
        
        
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
        
        

        
        


