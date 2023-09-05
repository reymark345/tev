from faker import Faker
from main.models import SystemConfiguration, StaffDetails, RoleDetails,Cluster,Charges,Division, Status
import numpy as np

fake = Faker()
Faker.seed(313)
middle_name = ['N','A','A','B']
role_details = ['Admin','Incoming staff','Validating staff','Payroll staff', 'Certified staff']
cluster = ['Cluster 01','Cluster 02','Cluster 03','Cluster 04', 'Cluster 05', 'Cluster 06', 'Cluster 07']
charges = ['AICS','Socpen','Disaster','CCAM', '4PS']
division = ['Finance Management Division','Pantawid','DRMD','HRRMD', 'PSD', 'PPD','ORD']
acronym = ['FMD','PTW','DRMD','HRRMD', 'PSD', 'PPD','ORD']
status = ['Pending','For checking','Returned','For payroll', 'Outgoing','Ongoing','Approved' ]



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

system_configuration_db = SystemConfiguration(name='Acounting Section', transaction_code = '23-05-00000', year='2023')
system_configuration_db.save()

userdb = StaffDetails(division='Finance Management Division',section ='Accounting sectiion', position ='CMT II', sex = 'Male', address='J.P. Rizal', user_id = '1', role_id = '1')
userdb.save()



