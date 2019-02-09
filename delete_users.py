#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
  To delete ArcGIS Online(AGO) account and contents based on the search results.
"""

import arcgis.gis
import argparse
import csv
import datetime
import getpass
import time
import our_org_constants

__author__ = "Philip Chen"
__license__ = "https://opensource.org/licenses/GPL-3.0 GPL-3.0 License"
__date__ = "2019.02.09"
__version__ = "1.2.5"
__status__ = "Tested on Python 3.7, ArcGIS API 1.5.2"

def search_contents( content_manager, user_name, max_results ):
	try:
		content_query = "owner:{}".format(user_name)
		user_contents = content_manager.search(	query=content_query,
												max_items=max_results,
												sort_field="modified",
												sort_order="desc")
		return user_contents
	except Exception as ex:
		print(ex)

# end of function search_contents()

def display_account_info( portal_user, content_manager, verbose ):
	
	print("===============================================================\n")
	print("[First name] ", portal_user.firstName, "[Last name] ", portal_user.lastName)
	print("[Username] ", portal_user.username, "[ESRI access]", portal_user.esri_access)
	print("[Email] ", portal_user.email)
	
	if portal_user.lastLogin == -1:
		print("Last active: Never")
	else:
		last_accessed = time.localtime(portal_user.lastLogin/1000)
		print("Last active: {}/{}/{}".format(last_accessed[0], last_accessed[1], last_accessed[2]))

	if verbose:
		print("====================================")
		quota = portal_user.storageQuota
		used = portal_user.storageUsage
		pc_usage = round((used / quota)*100, 2)
		print("Storage usage: {:2.1%}".format(pc_usage) )
	
		print("====================================")
		user_items = search_contents(content_manager, portal_user.username, 200)
		number_of_items = len(user_items)
		print("The user has {} items".format(number_of_items) )
		print(type(user_items))
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
		print("[Description] ", portal_user.description)

# end of function display_account_info()

def delete_item_relationships( target_item, verbose ):
	try:
		AGO_RELATIONSHIPS = [	'Map2Service',
								'WMA2Code',
								'Map2FeatureCollection',
								'MobileApp2Code',
								'Service2Data',
								'Service2Service']
		
		for relationship in AGO_RELATIONSHIPS:
			
			related_items = target_item.related_items(relationship, direction='forward')
			for related_item in related_items:
				outcome = target_item.delete_relationship(related_item, relationship)
				if outcome:
					if verbose: print("Deleted FORWARD relationship: ", related_item, relationship)
				else:
					print("**FAILED to delete relationship **: ", related_item, relationship)

			related_items = target_item.related_items(relationship, direction='reverse')
			for related_item in related_items:
				outcome = related_item.delete_relationship(target_item, relationship)
				if outcome:
					if verbose: print("Deleted REVERSE relationship: ", related_item, relationship)
				else:
					print("**FAILED to delete relationship **: ", related_item, relationship)

	except Exception as ex:
		print(ex)

# end of function delete_item_relationships()


def delete_account_and_assets( portal_user, content_manager, available_licenses, verbose ):
	"""
	AGO does not allow you to delete users until you have dealt with that users' items and groups.
	"""

	try:
		portal_user_name = portal_user.username

		if verbose: print("Disable ESRI site access ...")
		portal_user.esri_access = False

		# delete user's items
		while True:
			user_items = search_contents(content_manager, portal_user_name, 10)
			# items are returned as a list.
			number_of_items = len(user_items)
			if number_of_items > 0:
				for user_item in user_items:
					try:
						if user_item.protected:
							if verbose: print("Removing item protection: ", user_item)
							user_item.protect(enable=False)

						delete_item_relationships(user_item, verbose)
						user_item.delete()

					except Exception as ex:
							print(ex)
					print(user_item, user_item.id)

				time.sleep(5)
			else:
				if verbose: print(portal_user_name, " has no items left")
				break

		# folders are stored in a list.
		for user_folder in portal_user.folders:
			folder_name = user_folder['title']
			if portal_user_name == user_folder['username'] :
				outcome = content_manager.delete_folder(folder_name, owner=portal_user_name)
				if outcome:
					if verbose: print("Deleted folder: ", folder_name)
				else:
					print("**FAILED to delete folder **: ", folder_name)

		# groups are stored in a list.
		user_groups = portal_user.groups
		number_of_groups = len(user_groups)
		print(portal_user_name, "Member of {} groups".format(number_of_groups))
		for user_group in user_groups:
			if verbose: print("Removing from ", user_group)
			not_removed_users = user_group.remove_users([portal_user_name])
			print(not_removed_users)

		# revoking licenses
		for license in available_licenses:
			outcome = license.revoke(username=portal_user_name, entitlements='*')
			if outcome:
				if verbose: print(license, "revoked")
			else:
				print("**Revoking ", license, " FAILED ***")
			time.sleep(5)

		# delete user account
		if verbose: print("Deleting user ", portal_user_name, " ID ..." )
		outcome = portal_user.delete()
		return outcome

	except Exception as ex:
		print(ex)

# end of function delete_account_and_assets()

parser = argparse.ArgumentParser()
parser.add_argument("-u", "--user", help="Administrator username")
parser.add_argument("-p", "--password", help="Administrator password")
parser.add_argument("-t", "--termcode", default="201900", help="Termcode 201910 etc")
parser.add_argument("-v", "--verbose", action="store_true", help="Increase output verbosity")
parser.add_argument("-c", "--commit", action="store_true", help="Delete users for real")

args = parser.parse_args()

print("Hello admin ...\n")

admin_id = args.user
while not admin_id:
	admin_id = input("Please provide your AGO username: ")

admin_pw = args.password
while not admin_pw:
	admin_pw = getpass.getpass(prompt="Please provide your AGO password: ")

try:
	# Read the log file in append mode
	timestamp = datetime.datetime.now()
	log_filename = "ago_delete_account_{}.log".format(timestamp.strftime("%Y%m%d"))
	log_file = open(log_filename, 'a')

	if args.commit:
		log_file.write("\n=============== {} ================\n".format(timestamp.strftime("%A %H:%M")) )

	candidates_file_name = "ago_delete_candidates.csv"
	# Read the csv file in write mode
	candidate_list_csv = open(candidates_file_name, 'w', newline="")
	field_names = ['First Name', 'Last Name', 'Username']
	csv_writer = csv.DictWriter(candidate_list_csv, fieldnames=field_names)
	csv_writer.writeheader()

	print("Connecting... ")
	our_AGO = arcgis.gis.GIS(	our_org_constants.OUR_AGO_URL,
								admin_id,
								admin_pw)

	# Look up licenses
	our_licenses = our_AGO.admin.license.all()


	# Look up users
	# accounts = our_AGO.users.search(query="philip")

	# If necessary apply post search filter
	search_results = our_AGO.users.search(max_users=200)
	accounts = []
	for acct in search_results:
		if acct.username.startswith(args.termcode):
			accounts.append(acct)

	number_of_accounts = len(accounts)
	if number_of_accounts > 0:
		print("Total ", str(number_of_accounts), " account(s) found")
		#org_content_manager = arcgis.gis.ContentManager(our_AGO)
		org_content_manager = our_AGO.content
	else:
		print("NO account found")

	for acct in accounts:

		if args.commit:
			print("\n* Deleting user {} and assets ... ".format(acct.username) )
			outcome = delete_account_and_assets(acct, org_content_manager, our_licenses, args.verbose)
			if outcome:
				log_file.write("Deleted user {}'s accounts {} .\n".format(acct.firstName, acct.username) )
			else:
				log_file.write("FAILED to delete user {}'s accounts {} .\n".format(acct.firstName, acct.username) )
		else:
			# it's a dry-run
			csv_writer.writerow( {  'First Name': acct.firstName,
            	                    'Last Name': acct.lastName,
                	                'Username': acct.username } )
			display_account_info(acct, org_content_manager, args.verbose)

	if not args.commit:
		print("\n\n** This is a dry run, use --commit to delete users **\n")

	candidate_list_csv.close()

except Exception as ex:
	print(ex)
	log_file.write(str(ex))

log_file.close()