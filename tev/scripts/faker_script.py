from faker import Faker
from main.models import SystemConfiguration, StaffDetails, RoleDetails
import numpy as np

fake = Faker()
Faker.seed(313)
middle_name = ['N','A','A','B']
role_details = ['Admin','Incoming staff','Validating staff','Payroll staff', 'Certified staff']


for roles in role_details:
    role = RoleDetails(role_name=roles)
    role.save()

system_configuration_db = SystemConfiguration(name='Acounting Section', transaction_code = '23-05-00000', year='2023')
system_configuration_db.save()

userdb = StaffDetails(division='Finance Management Division',section ='Accounting sectiion', position ='CMT II', sex = 'Male', address='J.P. Rizal', user_id = '1', role_id = '1')
userdb.save()



