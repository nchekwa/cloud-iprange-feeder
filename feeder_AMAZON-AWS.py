#!/usr/bin/env python

import json
import os
import sys
import socket
import ipaddress
import tarfile
import shutil
import time
from httplib2 import Http
from pprint import pprint 
from datetime import datetime

# Start timer
startTime = time.time()


# Chekc if file folder exist
name="AMAZON-AWS"
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


# Functions
def list_prefixes(ipv4=True):
    if ipv4:
        address_family = socket.AF_INET
        prefixes_label = 'prefixes'
        ip_prefix_label = 'ip_prefix'
        ip_type = 4
    else:
        address_family = socket.AF_INET6
        prefixes_label = 'ipv6_prefixes'
        ip_prefix_label = 'ipv6_prefix'
        ip_type = 6

    pfx_dict = {}
    for prefix in ipranges[prefixes_label]:
        ip_prefix = prefix[ip_prefix_label]
        if ip_prefix not in pfx_dict:
            pfx_dict[ip_prefix] = {}
            pfx_dict[ip_prefix]['net'] = ip_prefix
            pfx_dict[ip_prefix]['rgn'] = prefix['region']
            pfx_dict[ip_prefix]['svc'] = [ prefix['service'] ]
            pfx_dict[ip_prefix]['type'] = ip_type
        else:
            pfx_dict[ip_prefix]['svc'].append(prefix['service'])

    pfx_vals = list(pfx_dict.values())
    pfx_vals = sorted(pfx_vals, key=lambda x: socket.inet_pton(address_family, x['net'].split('/')[0]))

    return pfx_vals

def make_tarfile(output_filename, source_dir):
    with tarfile.open(output_filename, "w:gz") as tar:
        tar.add(source_dir, arcname=os.path.basename(source_dir))


def create_info_file(path):
    f = open(path, "w")
    f.write("syncToken: "+ipranges['syncToken']+"\n"+ 
            "createDate: "+ipranges['createDate']+"\n"+
            "generateDate: "+datetime.now().strftime("%Y-%m-%d-%H-%M-%S")+time.strftime("%z", time.gmtime())+"\n")
    f.close()

# Main Script
if __name__ == "__main__":
    # Main Process
    print ('-----------------------------------------------------------------')
    print ("Process: "+(__file__)+" at "+str( datetime.now()) )

    # Download File
    ip_ranges = "https://ip-ranges.amazonaws.com/ip-ranges.json"
    try:
        #resp, content = Http(disable_ssl_certificate_validation=True).request(ip_ranges)
        resp, content = Http().request(ip_ranges)
        if resp.status != 200:
            print("Unable to load %s - %d %s" % (ip_ranges, resp.status, resp.reason))
            exit(1)
        content = content.decode('latin1')
        ipranges = json.loads(content)
    except Exception as e:
        print("Unable to load %s - %s" % (ip_ranges, e))
        exit(1)
    downloadTime = time.time()

    # Create one big IP dict
    prefixes = list()
    prefixes.extend(list_prefixes(ipv4=True))
    prefixes.extend(list_prefixes(ipv4=False))

    # Check if downloaded json contains prefixes
    if len(ipranges['prefixes']) + len(ipranges['ipv6_prefixes']) < 1:
        print("No prefixes found")
        exit(1)

    # Generate output text files
    file_out = dict()
    file_out['ALL_ipv4'] = list()
    file_out['ALL_ipv6'] = list()
    file_out['ALL'] = list()
    for ip_item in prefixes:
        # IPv4 and IPv6
        file_out['ALL'].append(str(ip_item['net']))

        if ip_item['type'] == 4:
            file_out['ALL_ipv4'].append(str(ip_item['net']))

        if ip_item['type'] == 6:
            file_out['ALL_ipv6'].append(str(ip_item['net']))

        # Regions
        region = "rgn_"+ip_item['rgn']
        try:
            file_out[region]
        except:
            file_out[region] = list()
        file_out[region].append(str(ip_item['net'])) 

        # Services
        for svc in ip_item['svc']:
            service = "svc_"+svc
            try:
                file_out[service]
            except:
                file_out[service] = list()
            file_out[service].append(str(ip_item['net'])) 

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