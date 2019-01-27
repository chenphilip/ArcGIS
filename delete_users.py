#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
  To delete ArcGIS Online(AGO) account and contents based on the search results.
"""

import csv
import arcgis.gis
import argparse
import time
import our_org_constants

__author__ = "Philip Chen"
__license__ = "https://opensource.org/licenses/GPL-3.0 GPL-3.0 License"
__date__ = "2019.01.26"
__version__ = "1.2.0"
__status__ = "Tested on Python 3.6, ArcGIS API 1.5.2"

def search_contents(content_manager, user_name):
	try:
		content_query = "owner:{}".format(user_name)
		user_contents = our_AGO.content.search(	query=content_query,
												max_items=500,
												sort_field="modified",
												sort_order="asc")
		return user_contents
	except Exception as ex:
		# Just print(ex) is cleaner and more likely what you want
		if hasattr(ex, "message"):
			print(ex.message)
		else:
			print(ex)

# end of function search_contents()

def display_account_info( portal_user, content_manager, verbose ):
	
	print("===============================================================\n")
	print("[First name] ", portal_user.firstName, "[Last name] ", portal_user.lastName)
	print("[Username] ", portal_user.username, "[Email] ", portal_user.email)
	print("[Description] ", portal_user.description, "[ESRI access]", portal_user.esri_access)
	
	print("====================================")
	account_created = time.localtime(portal_user.created/1000)
	print("Created on: {}/{}/{}".format(account_created[0], account_created[1], account_created[2]))

	if portal_user.lastLogin == -1:
		print("Last active: Never")
	else:
		last_accessed = time.localtime(portal_user.lastLogin/1000)
		print("Last active: {}/{}/{}".format(last_accessed[0], last_accessed[1], last_accessed[2]))

	#print("====================================")
	#print("\nMy privileges: " + str(portal_user.privileges))
	
	if verbose:
		print("====================================")
		quota = portal_user.storageQuota
		used = portal_user.storageUsage
		pc_usage = round((used / quota)*100, 2)
		print("Storage usage: {:2.1%}".format(pc_usage) )
	
		print("====================================")
		user_items = search_contents(content_manager, portal_user.username)
		number_of_items = len(user_items)
		print("The user has {} items".format(number_of_items) )
		# item are returned as a list.
		for user_item in user_items:
			print(user_item)

		print("====================================")
		# folders are returned as a list.
		user_folders = portal_user.folders
		number_of_folders = len(user_folders)
		print("Has ", str(number_of_folders), " folders")
		for user_folder in user_folders:
			print(user_folder)

		print("====================================")
		user_groups = portal_user.groups
		number_of_groups = len(user_groups)
		print("Member of ", str(number_of_groups), " groups")
		# groups are returned as a dictionary. Lets print the first dict as a sample
		for user_group in user_groups:
			print(user_group)

		print("====================================")
		print("[Role] ", portal_user.role)

# end of function display_account_info()

def delete_account_and_assets( portal_user, content_manager, available_licenses, verbose ):
	"""
	AGO does not allow you to delete users until you have dealt with that users' items and groups.
	"""

	try:
		portal_user_name = portal_user.username

		if verbose: print("Disable ESRI site access ...")
		portal_user.esri_access = False

		# delete user's items
		user_items = search_contents(content_manager, portal_user_name)
		number_of_items = len(user_items)
		# item are returned as a list.
		if number_of_items > 0:
			result = content_manager.delete_items(user_items)
			if result:
				if verbose: print("Deleted user {:2} items".format(number_of_items))
				time.sleep(5)
			else:
				print("**Delete user items FAILED**")
		else:
			if verbose: print(portal_user_name, " has no items")

		# folders are stored in a list.
		for user_folder in portal_user.folders:
			folder_name = user_folder['title']
			if portal_user_name == user_folder['username'] :
				if verbose: print("Deleting folders", folder_name)
				content_manager.delete_folder(folder_name, owner=portal_user_name)
				time.sleep(5)

		# groups are stored in a list.
		user_groups = portal_user.groups
		number_of_groups = len(user_groups)
		print(portal_user_name, "Member of {} groups".format(number_of_groups))
		# groups are returned as a dictionary
		for user_group in user_groups:
			if verbose: print("Removing from ", user_group)
			not_removed_users = user_group.remove_users([portal_user_name])
			print(not_removed_users)

		# revoking licenses
		for license in available_licenses:
			result = license.revoke(username=portal_user_name, entitlements='*')
			if result:
				if verbose: print(license, "revoked")
			else:
				print("**Revoking ", license, " FAILED ***")
			time.sleep(5)

		# delete user account
		if verbose: print("Deleting user ", portal_user_name, " ID ..." )
		#portal_user.delete()

	except Exception as ex:
		# Just print(ex) is cleaner and more likely what you want
		if hasattr(ex, "message"):
			print(ex.message)
		else:
			print(ex)

# end of function delete_account_and_assets()

parser = argparse.ArgumentParser()
parser.add_argument("-u","--user", default="myID", help="Administrator username")
parser.add_argument("-p","--password", default="mypassword", help="Administrator password")
parser.add_argument("-t","--termcode", default="201900", help="Termcode 201910 etc")
parser.add_argument("-f", "--file", default="users_list.csv", help="CSV file path and filename")
parser.add_argument("-v", "--verbose", action="store_true", help="Increase output verbosity")
parser.add_argument("-c", "--commit", action="store_true", help="Delete users for real")

args = parser.parse_args()

try:
	# Read the csv file in write mode
	user_list_csv = open(args.file, "w", newline="")
	field_names = ['First Name', 'Last Name', 'Username']
	csv_writer = csv.DictWriter(user_list_csv, fieldnames=field_names)
	csv_writer.writeheader()

	print("Connecting... ")
	our_AGO = arcgis.gis.GIS(	our_org_constants.OUR_AGO_URL,
								args.user,
								args.password)

	verbose = args.verbose
	commit = args.commit
	# Look up licenses
	# item are returned as a list.
	our_licenses = our_AGO.admin.license.all()
	#print("====================================")
	#number_of_licenses = len(our_licenses)
	#print("School has {} licenses".format(number_of_licenses) )
	#for license in our_licenses:
	#	print(license)

	# Look up users
	# display_account_info(our_AGO.users.me)
	# Users search syntax and default values:
	#   search(query=None, sort_field=['username'|'created'], sort_order="asc", max_users=100,
	#           outside_org=False, exclude_system=False, user_type=None, role=None)
	# accounts = our_AGO.users.search(query="philip", sort_field="created", max_users=200)
	accounts = our_AGO.users.search(max_users=200)
	# If necessary apply post search filter
	accounts = [acct for acct in accounts if acct.username.startswith(args.termcode)]
	number_of_accounts = len(accounts)
	if number_of_accounts > 0:
		print("Total ", str(number_of_accounts), " account(s) found")
	else:
		print("NO account found")

	for acct in accounts:
		csv_writer.writerow( {  'First Name': acct.firstName,
                                'Last Name': acct.lastName,
                                'Username': acct.username } )

		if commit:
			print("\n* Deleting user {} and assets ... ".format(acct.username) )
			delete_account_and_assets(acct, our_AGO.content, our_licenses, verbose)
		else:
			display_account_info(acct, our_AGO.content, verbose)

	if not commit:
		print("\n\n** This is a dry run, use --commit to delete users **\n")

	user_list_csv.close()

except Exception as ex:
	# Just print(ex) is cleaner and more likely what you want
	if hasattr(ex, "message"):
		print(ex.message)
	else:
		print(ex)

