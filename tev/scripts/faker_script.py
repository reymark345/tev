from faker import Faker
from main.models import SystemConfiguration, StaffDetails, RoleDetails,Cluster,Charges
import numpy as np

fake = Faker()
Faker.seed(313)
middle_name = ['N','A','A','B']
role_details = ['Admin','Incoming staff','Validating staff','Payroll staff', 'Certified staff']
cluster = ['Cluster 01','Cluster 02','Cluster 03','Cluster 04', 'Cluster 05', 'Cluster 06', 'Cluster 07']
charges = ['AICS','Socpen','Disaster','CCAM', '4PS']


for roles in role_details:
    role = RoleDetails(role_name=roles)
    role.save()
    
for clus in cluster:
    cl = Cluster(name=clus)
    cl.save()

for charge in charges:
    ch = Charges(name=charge)
    ch.save()

system_configuration_db = SystemConfiguration(name='Acounting Section', transaction_code = '23-05-00000', year='2023')
system_configuration_db.save()

userdb = StaffDetails(division='Finance Management Division',section ='Accounting sectiion', position ='CMT II', sex = 'Male', address='J.P. Rizal', user_id = '1', role_id = '1')
userdb.save()



