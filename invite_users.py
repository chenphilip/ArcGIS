#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
  Script to read email list from a csv file and send out invite emails to users.
"""
__author__ = "Philip Chen"
__license__ = "https://opensource.org/licenses/GPL-3.0 GPL-3.0 License"
__date__ = "2019.02.23"
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
parser.add_argument("-r", "--role", default="Publisher_LocalOnly", help="Role will be assigned to the users")

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
log_filename = "ago_invite_emails_{}.log".format(timestamp.strftime("%Y%m%d"))
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


	# loop through and create users
	number_of_acct = 0
	with open("invitees.csv", 'r') as user_list_csv:
		users = csv.DictReader(user_list_csv)
		for user in users:
			first_name = user['First Name']
			last_name = user['Last Name']
			user_name = user['Username']
			email_addr = user['myBcit Email']
			print(first_name, last_name, user_name, email_addr)

			email_str_length = len(email_addr)
			if email_str_length > 12:
				log_file.write("\nEmail user: {}".format(user_name))
				try:
	                # Syntax and default values:
    	            #   invite(email, role='org_user', level=2, provider=None,
                    #   must_approve=False, expiration='1 Day', validate_email=True)
					outcome = our_AGO.users.invite(	email=email_addr,
													role=acct_role,
                                                    level=2,
                                                    expiration='1 Week',
                                                    validate_email=True)
					if outcome:
						number_of_acct += 1
						log_file.write(" email to {} sent successfully\n".format(email_addr))
						arc_pro_license.assign(username=user_name, entitlements=OUR_ARC_PRO_ENTITLEMENTS)
						arcgis.gis.User(our_AGO, user_name).esri_access = True
                    else:
                        log_file.write(" *Failed to email {} *\n".format(email_addr))
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

