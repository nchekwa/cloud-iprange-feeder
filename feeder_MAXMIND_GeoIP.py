#!/usr/bin/env python

import csv
import os
import sys
import socket
import ipaddress
import tarfile
import shutil
import time
import requests
from pprint import pprint 
from datetime import datetime
from zipfile import ZipFile

# Start timer
startTime = time.time()

# API_KEY 
# Define inside this script or
# 1) set linux Environment Variable 'api_key' or 'maxmind_api_key'
#    ie: root@linux:/opt/srx-scripts# export maxmind_api_key=1234567890abcde
#    if you whant to remove Environment Variable use command: unset maxmind_api_key
# 2) use script togethere with argument
#    ie. root@linux:/opt/srx-scripts# python feeder_MAXMIND_GeoIP.py 1234567890abcde

api_key = None

if api_key is None:
    if os.environ.get('api_key') is not None:
        api_key = os.environ.get('api_key')

    if os.environ.get('maxmind_api_key') is not None:
        api_key = os.environ.get('maxmind_api_key')

    if len(sys.argv)>1:
        if sys.argv[1] is not None:
            api_key = sys.argv[1]




# Chekc if file folder exist
name="MAXMIND_GeoIP"
script_path = os.path.dirname(os.path.abspath(__file__))
file_folder = script_path+'/files'
vendor_file_folder = script_path+'/files/'+name
vendor_file_folder_tmp = script_path+'/files/'+name+'-temp'
if not os.path.exists(file_folder):
    os.makedirs(file_folder)
if not os.path.exists(vendor_file_folder):
    os.makedirs(vendor_file_folder)
if not os.path.exists(vendor_file_folder_tmp):
    os.makedirs(vendor_file_folder_tmp)

def read_location(lang = "en"):
    global geoip_path
    csvFilePath = geoip_path+"/GeoLite2-Country-Locations-"+lang+".csv"
    data = dict()
    with open(csvFilePath, encoding='utf-8') as csvf:
        csvReader = csv.DictReader(csvf)
        for rows in csvReader:
            key = rows['geoname_id']
            data[key] = rows
    return(data)


# Functions
def list_prefixes(ipv4=True):
    global geoip_path
    global location
    if ipv4:
        address_family = socket.AF_INET
        ip_type = 4
        csvFilePath = geoip_path+"/GeoLite2-Country-Blocks-IPv4.csv"
    else:
        address_family = socket.AF_INET6
        ip_type = 6
        csvFilePath = geoip_path+"/GeoLite2-Country-Blocks-IPv6.csv"
    
    # Read CSV File
    pfx_dict = {}
    with open(csvFilePath, encoding='utf-8') as csvf:
        csvReader = csv.DictReader(csvf)
        for rows in csvReader:
            key = rows['network']
            rows['type'] = ip_type
            rows['is_in_european_union'] = 0

            # Check if 'geoname_id' exist
            if rows['geoname_id'] != "":
                rows['geoname'] = f"{location[rows['geoname_id']]['continent_code']}_{location[rows['geoname_id']]['continent_name']}"
                rows['is_in_european_union'] = location[rows['geoname_id']]['is_in_european_union']
            else:
                rows['geoname'] = "Unknown"

            # Check if 'geoname_id' exist
            if rows['registered_country_geoname_id'] != "":
                rows['registered_country_geoname'] = f"{location[rows['registered_country_geoname_id']]['country_iso_code']}_{location[rows['registered_country_geoname_id']]['country_name']}"
            else:
                rows['registered_country_geoname'] = "Unknown"

            # Check if 'geoname_id' exist
            if rows['represented_country_geoname_id'] != "":
                rows['represented_country_geoname'] = f"{location[rows['represented_country_geoname_id']]['country_iso_code']}_{location[rows['represented_country_geoname_id']]['country_name']}"
            else:
                rows['represented_country_geoname'] = "Unknown"

            pfx_dict[key] = rows

    # Just for Debug purpose (generate JSON in temp folder if needed)
    #import json
    #with open(csvFilePath+".json", 'w', encoding='utf-8') as jsonf:
    #    jsonf.write(json.dumps(pfx_dict, indent=4))

    pfx_vals = list(pfx_dict.values())
    pfx_vals = sorted(pfx_vals, key=lambda x: socket.inet_pton(address_family, x['network'].split('/')[0]))
    return pfx_vals


def make_tarfile(output_filename, source_dir):
    with tarfile.open(output_filename, "w:gz") as tar:
        tar.add(source_dir, arcname=os.path.basename(source_dir))


def create_info_file(path):
    global geoip_path
    f = open(path, "w")
    f.write("dbDate: "+geoip_path[-8:]+"\n"+
            "generateDate: "+datetime.now().strftime("%Y-%m-%d-%H-%M-%S")+time.strftime("%z", time.gmtime())+"\n")
    f.close()


# Main Script
if __name__ == "__main__":
    # Main Process
    print ('-----------------------------------------------------------------')
    print ("Process: "+(__file__)+" at "+str( datetime.now()) )


    # Download File
    ip_ranges = f"https://download.maxmind.com/app/geoip_download?edition_id=GeoLite2-Country-CSV&license_key={api_key}&suffix=zip"
    try:
        file_zip_dst = vendor_file_folder_tmp+'/GeoLite2-Country-CSV.zip'
        r = requests.get(ip_ranges)
        if r.status_code != 200:
            print("Unable to load %s - %d" % (ip_ranges, r.status_code))
            exit(1)
        open(file_zip_dst, 'wb').write(r.content)

        zf = ZipFile(file_zip_dst, 'r')
        zf.extractall(vendor_file_folder_tmp)
        zf.close()

        # Find Path to Temporary UnZiped GeoIP Folder
        for directory in os.listdir(vendor_file_folder_tmp):
            if directory.startswith("Geo"):
                geoip_path = vendor_file_folder_tmp+"/"+directory

        # We dont need anymore original ZIP file
        os.remove(file_zip_dst)

    except Exception as e:
        print("Unable to load %s - %s" % (ip_ranges, e))
        exit(1)

    downloadTime = time.time()
    
    # Create one big IP dict
    location = read_location()
    prefixes = list()
    prefixes.extend(list_prefixes(ipv4=True))
    prefixes.extend(list_prefixes(ipv4=False))




    # Generate output text files
    file_out = dict()
    file_out['ALL_ipv4'] = list()
    file_out['ALL_ipv6'] = list()
    file_out['ALL'] = list()
    for ip_item in prefixes:
        # ALL - IPv4 and IPv6
        file_out['ALL'].append(str(ip_item['network']))

        if ip_item['type'] == 4:
            file_out['ALL_ipv4'].append(str(ip_item['network']))

        if ip_item['type'] == 6:
            file_out['ALL_ipv6'].append(str(ip_item['network']))

        # continent ALL
        continent = "continent_"+ip_item['geoname'].replace(" ", "_")
        try:
            file_out[continent]
        except:
            file_out[continent] = list()
        file_out[continent].append(str(ip_item['network'])) 

        # continent IPv4/6
        continent = f"{continent}_ipv{ip_item['type']}"
        try:
            file_out[continent]
        except:
            file_out[continent] = list()
        file_out[continent].append(str(ip_item['network'])) 

        # country ALL
        country = "country_"+ip_item['registered_country_geoname'].replace(" ", "_").replace(",", "").replace("ç", "c")
        try:
            file_out[country]
        except:
            file_out[country] = list()
        file_out[country].append(str(ip_item['network'])) 

        # country IPv4/6
        country = f"{country}_ipv{ip_item['type']}"
        try:
            file_out[country]
        except:
            file_out[country] = list()
        file_out[country].append(str(ip_item['network'])) 

    # Remove GeoIP unziped folder
    shutil.rmtree(geoip_path) 

    # Write all information from dict to files
    for key,file_item in file_out.items():
        file_name = vendor_file_folder_tmp+"/"+key
        with open(file_name, 'w') as f:
            for item in file_item:
                f.write("%s\n" % item)

    # Remove previous folder
    if os.path.exists(vendor_file_folder_tmp) == True:
        shutil.rmtree(vendor_file_folder) 

    # Temp will now be current folder
    os.rename(vendor_file_folder_tmp, vendor_file_folder)
    
    # Remove temp folder
    if os.path.exists(vendor_file_folder_tmp) == True:
        shutil.rmtree(vendor_file_folder_tmp) 

    # Create TGZ for feed-server option
    make_tarfile(file_folder+"/"+name+".tgz", vendor_file_folder)

    # Create INFO file
    create_info_file(file_folder+"/"+name+".txt")

    # Print log
    print ('Result:')
    endTime = time.time()
    print (' - download in {0} second'.format(downloadTime - startTime))
    print (' - processing in {0} second'.format(endTime - downloadTime))
    print ('   TOTAL: {0} second'.format(endTime - startTime))

