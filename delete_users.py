#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
  Delete user accounts based on the search results.
"""

import csv
from arcgis.gis import *
import argparse
import time
import bcit_constants

__author__ = 'Philip Chen'
__license__ = 'https://opensource.org/licenses/GPL-3.0 GPL-3.0 License'
__date__ = '2019.01.12'
__version__ = '1.0.0'
__status__ = 'Tested on Python 3.6, ArcGIS API 1.5.2'

def display_account_info( portal_user, verbose ):
	
	print('===============================================================\n')
	print('[First name] ', portal_user.firstName, '[Last name] ', portal_user.lastName)
	print('[Username] ', portal_user.username, '[Email] ', portal_user.email)
	print('[Description] ', portal_user.description)
	
	print('====================================')
	account_created = time.localtime(portal_user.created/1000)
	print('Created on: {}/{}/{}'.format(account_created[0], account_created[1], account_created[2]))

	if portal_user.lastLogin == -1:
		print('Last active: Never')
	else:
		last_accessed = time.localtime(portal_user.lastLogin/1000)
		print('Last active: {}/{}/{}'.format(last_accessed[0], last_accessed[1], last_accessed[2]))

	#print('====================================')
	#print('\nMy privileges: ' + str(portal_user.privileges))
	
	if verbose:
		print('====================================')
		quota = portal_user.storageQuota
		used = portal_user.storageUsage
		pc_usage = round((used / quota)*100, 2)
		print('Storage usage: {:2.1%}'.format(pc_usage) )
	
		print('====================================')
		user_groups = portal_user.groups
		group_number = len(user_groups)
		print('Member of ', str(group_number), ' groups')
		# groups are returned as a dictionary. Lets print the first dict as a sample
		i = 0
		while i < group_number:
			print(user_groups[i])
			i += 1

		#print('====================================')
		#print('[Role] ', portal_user.role, '[Multi-factor Auth] ', portal_user.mfaEnabled, '[Provider] ', portal_user.provider, '[User type] ', portal_user.userType)
	
# End of function display_account_info()

parser = argparse.ArgumentParser()
parser.add_argument('-u','--user', default='myID', help='Administrator username')
parser.add_argument('-p','--password', default='mypassword', help='Administrator password')
parser.add_argument('-t','--termcode', default='201900', help='Termcode 201910 etc')
parser.add_argument('-f', '--file', default='users_list.csv', help='CSV file path and filename')
parser.add_argument('-v', '--verbose', action='store_true', help='ncrease output verbosity')
parser.add_argument('-c', '--commit', action='store_true', help='Delete users for real')

args = parser.parse_args()

try:
	# Read the csv file in write mode
	user_list_csv = open(args.file, 'w', newline='')
	field_names = ['First Name', 'Last Name', 'Username']
	csv_writer = csv.DictWriter(user_list_csv, fieldnames=field_names)
	csv_writer.writeheader()

	print('Connecting... ')
	bcit_online = GIS(bcit_constants.BCIT_ARCGIS_ONLINE_URL, args.user, args.password)

	# Look up users
	# display_account_info(bcit_online.users.me)
	# Users search syntax and default values:
	#   search(query=None, sort_field=['username'|'created'], sort_order='asc', max_users=100,
	#           outside_org=False, exclude_system=False, user_type=None, role=None)
	# accounts = bcit_online.users.search(query='philip', sort_field='created', max_users=200)
	accounts = bcit_online.users.search(max_users=200)
	# If necessary apply post search filter
	accounts = [acct for acct in accounts if acct.username.startswith(args.termcode)]
	account_total = len(accounts)
	print('Total ', str(account_total), ' account(s) found')
	print('DISPLAY USER ACCOUNTS')
	for acct in accounts:
		display_account_info( acct, args.verbose )
		csv_writer.writerow( {  'First Name': acct.firstName,
                                'Last Name': acct.lastName,
                                'Username': acct.username } )
		if args.commit:
			print('\n* Deleting [', acct.username, '] ... ')
			acct.delete()

	if not args.commit:
		print('\n\n** This is a dry run, use --commit to delete users **\n')

	user_list_csv.close()

except Exception as ex:
	# Just print(ex) is cleaner and more likely what you want
	if hasattr(ex, 'message'):
		print(ex.message)
	else:
		print(ex)

