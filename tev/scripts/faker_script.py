from faker import Faker
from main.models import SystemConfiguration, StaffDetails, RoleDetails,Cluster,Charges,Division, Status, RemarksLib, RolePermissions
import numpy as np

fake = Faker()
Faker.seed(313)
middle_name = ['N','A','A','B']
role_details = ['Admin','Incoming staff','Validating staff','Payroll staff', 'Certified staff','End user']
cluster = ['Cluster 01','Cluster 02','Cluster 03','Cluster 04', 'Cluster 05', 'Cluster 06', 'Cluster 07']
charges = ['AICS','Socpen','Disaster','CCAM', '4PS', 'Pantawid', 'Multiple']
division = ['Finance Management Division','Pantawid','DRMD','HRRMD', 'PSD', 'PPD','ORD']
acronym = ['FMD','PTW','DRMD','HRRMD', 'PSD', 'PPD','ORD']
status = ['Pending','For checking','Returned','For payroll', 'p_payroll','f_payroll','For approval','r_outgoing','f_outgoing','r_budget','f_nudget','r_journal','f_journal']
remarks = ['NO CA','NO TICKET']


for roles in role_details:
    role = RoleDetails(role_name=roles)
    role.save()
    
for clus in cluster:
    cl = Cluster(name=clus)
    cl.save()

for charge in charges:
    ch = Charges(name=charge,created_by=1)
    ch.save()
    
    
for i in range(len(division)):
    div_val = Division(name=division[i],acronym = acronym[i],chief = fake.name(),c_designation = fake.name(),approval = fake.name(),ap_designation = fake.name(),created_by=1)
    div_val.save()
    
    
for stat in status:
    stat = Status(name=stat)
    stat.save()

for i in range(len(remarks)):
    rem_val = RemarksLib(name=remarks[i],created_by=1)
    rem_val.save()

system_configuration_db = SystemConfiguration(name='Acounting Section', transaction_code = '23-05-00000', year='2023')
system_configuration_db.save()

userdb = StaffDetails(id_number ='16-11810',division='Finance Management Division',section ='Accounting sectiion', position ='CMT II', sex = 'Male', address='J.P. Rizal', user_id = '1', role_id = '1')
userdb.save()

role_p = RolePermissions(role_id ='1',user_id='1')
role_p.save()



