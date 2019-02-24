#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
  Script to read account list from a csv file and create appropriate users in the portal.
"""
__author__ = "Philip Chen"
__license__ = "https://opensource.org/licenses/GPL-3.0 GPL-3.0 License"
__date__ = "2019.02.24"
__version__ = "1.0.0"
__status__ = "Tested on Python 3.7, ArcGIS API 1.5.2"

import arcgis.gis
import argparse
import csv
import datetime
import getpass
import time
from our_org_constants import *

#read cmd line args
parser = argparse.ArgumentParser()
parser.add_argument("-u", "--user", help="Administrator username")
parser.add_argument("-p", "--password", help="Administrator password")
parser.add_argument("-t", "--termcode", default="201900", help="Termcode 201910 etc")
parser.add_argument("-r", "--role", default="Publisher_LocalOnly", help="Role will be assigned to the users")
parser.add_argument("-f", "--file", default="new_users.csv", help="Input CSV file path and filename")

args = parser.parse_args()

print("Hello admin ...\n")

admin_id = args.user
while not admin_id:
	admin_id = input("Please provide your AGO username: ")

admin_pw = args.password
while not admin_pw:
	admin_pw = getpass.getpass(prompt="Please provide your AGO password: ")

# Read the log file in append mode
timestamp = datetime.datetime.now()
log_filename = "ago_new_account_{}.log".format(timestamp.strftime("%Y%m%d"))
log_file = open(log_filename, 'a')

log_file.write("\n=============== {} ================\n".format(timestamp.strftime("%A %H:%M")) )

try:
	print("Connecting... ")
	our_AGO = arcgis.gis.GIS(OUR_AGO_URL, admin_id, admin_pw)

	avail_roles = arcgis.gis.RoleManager(our_AGO).all()
	for role in avail_roles:
		if role.name == args.role:
			print(role.role_id, role.name, role.description)
			acct_role = role

	arc_pro_license = our_AGO.admin.license.get('ArcGIS Pro')

	# loop through and create users
	number_of_acct = 0
	with open(args.file, 'r') as user_list_csv:
		users = csv.DictReader(user_list_csv)
		for user in users:
			first_name = user['First Name']
			last_name = user['Last Name']
			bann_id = user['Id ']
			email_addr = user['myBcit Email']
			print (first_name, last_name, bann_id, email_addr)

			email_str_length = len(email_addr)
			if email_str_length > 12:
				email_name = email_addr.split('@')[0]
				user_name = (args.termcode + "_" + email_name).lower()
				acct_description = "Auto-created for " + args.termcode

				temp_password = pwgen()
				print(temp_password)
				log_file.write("\nCreating user: {}".format(user_name))
				try:
	                # Syntax and default values:
    	            #   create(username, password, firstname, lastname, email, description=None,
        	        #           role='org_user', provider='arcgis', idp_username=None, level=2,
            	    #           thumbnail=None, user_type='creator', credits=-1, groups=None)
					result = our_AGO.users.create(	username=user_name,
													password=temp_password,
													firstname=first_name,
													lastname=last_name,
													email=email_addr,
													description=acct_description,
													role=acct_role)
					if result:
						number_of_acct += 1
						log_file.write(" *created successfully*\n")
						arc_pro_license.assign(username=user_name, entitlements=OUR_ARC_PRO_ENTITLEMENTS)
						arcgis.gis.User(our_AGO, user_name).esri_access = True
				except Exception as add_ex:
					print(add_ex)
					print("\nAn exception occured during creating user: " + user_name)
					log_file.write("\nAn exception occured during creating user: " + user_name)
					log_file.write("\n")
					log_file.write(str(add_ex))
	log_file.write("\nTotal {} accounts created\n".format(number_of_acct))

except Exception as ex:
	# Just print(ex) is cleaner and more likely what you want
	print(ex)
	log_file.write(str(ex))

log_file.close()

