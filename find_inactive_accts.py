#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
  Searches ArcGIS Online(AGO) inactive accounts and save them into a CSV file.
"""

import arcgis.gis
import argparse
import csv
import datetime
import getpass
import time
from our_org_constants import *

__author__ = "Philip Chen"
__license__ = "https://opensource.org/licenses/GPL-3.0 GPL-3.0 License"
__date__ = "2019.08.31"
__version__ = "1.0.0"
__status__ = "Tested on Python 3.7, ArcGIS API 1.5.2"


parser = argparse.ArgumentParser()
parser.add_argument("-u", "--user", help="Administrator username")
parser.add_argument("-p", "--password", help="Administrator password")
parser.add_argument("-t", "--termcode", default="201900", help="Termcode 201910 etc")
parser.add_argument("-c", "--cut_off_month", default="2019.05", help="Inactive before 2019.05")
parser.add_argument("-v", "--verbose", action="store_true", help="Increase output verbosity")

args = parser.parse_args()

print("Hello admin ...\n")

admin_id = args.user
while not admin_id:
    admin_id = input("Please provide your AGO username: ")

admin_pw = args.password
while not admin_pw:
    admin_pw = getpass.getpass(prompt="Please provide your AGO password: ")

cut_off_date = datetime.datetime.strptime(args.cut_off_month,"%Y.%m")
verbose = args.verbose

try:
    # Read the log file in append mode
    timestamp = datetime.datetime.now()
    log_filename = "ago_find_inactive_accts_{}.log".format(timestamp.strftime("%Y%m%d"))
    log_file = open(log_filename, 'a')

    log_file.write("\n=============== {} ================\n".format(timestamp.strftime("%A %H:%M")))

    print("Connecting... ")
    our_AGO = arcgis.gis.GIS(OUR_AGO_URL, admin_id, admin_pw)

    # If necessary apply post search filter
    search_results = our_AGO.users.search(max_users=MAX_NUMBER_OF_RETURNS)
    accounts = []
    for acct in search_results:
        if acct.username.startswith(args.termcode):
            accounts.append(acct)

    number_of_accounts = len(accounts)
    if number_of_accounts > 0:
        msg = "Total {} account(s) found.\n".format(str(number_of_accounts))
        print(msg)
        log_file.write(msg)
        # org_content_manager = arcgis.gis.ContentManager(our_AGO)
        org_content_manager = our_AGO.content
    else:
        print("NO account found")
        log_file.write("\nNO account found\n")

    # Read the csv file in write mode
    inactive_accts_file = "ago_inactive_accounts.csv"
    with open(inactive_accts_file, 'w', newline="") as inactive_accts_csv:
        field_names = ('First Name', 'Last Name', 'UserID', 'Created On', 'Last Login')
        csv_writer = csv.DictWriter(inactive_accts_csv, fieldnames=field_names)
        csv_writer.writeheader()

        for acct in accounts:
            first_name = acct.firstName
            last_name = acct.lastName
            login_id = acct.username

            acct_created_on = time.localtime(acct.created / 1000)
            created_on = "{}/{}/{}".format(acct_created_on[0], acct_created_on[1], acct_created_on[2])
            created_date = datetime.datetime.strptime(created_on, "%Y/%m/%d")

            if acct.lastLogin == -1:
                last_login = "Never"
                last_login_date = datetime.datetime.strptime("2000/01/01","%Y/%m/%d")
            else:
                last_accessed = time.localtime(acct.lastLogin / 1000)
                last_login = "{}/{}/{}".format(last_accessed[0], last_accessed[1], last_accessed[2])
                last_login_date = datetime.datetime.strptime(last_login,"%Y/%m/%d")

            if verbose:
                print("= = = = = = = = = = = = = = = = = =")
                print("[Name] {} {}".format(first_name, last_name))
                print("[UserID] ", login_id)
                print("[Created on] ", created_on)
                print("[Last login] ", last_login)

            if (last_login_date < cut_off_date) and (created_date < cut_off_date):
                csv_writer.writerow({'First Name': first_name,
                                     'Last Name': last_name,
                                     'UserID': login_id,
                                     'Created On': created_on,
                                     'Last Login': last_login})
                if verbose:
                    print("OK for deletion")
            else:
                if verbose:
                    print("Not for deletion")

    log_file.write("\nExiting find_inactive_accts.py\n")

except Exception as ex:
    print(ex)
    log_file.write(str(ex))

finally:
    if log_file:
        log_file.close()
