#!/usr/bin/env python

import json
import os
import sys
import socket
import ipaddress
import tarfile
import shutil
import time
import re
from httplib2 import Http
from pprint import pprint 
from datetime import datetime


info = dict()
files = dict()

# Start timer
startTime = time.time()

# List of files
# https://www.spamhaus.org/drop/

# Spamhaus Don't Route Or Peer List (DROP)
# The DROP list will not include any IP address space under the control of any legitimate network 
# even if being used by "the spammers from hell". DROP will only include netblocks allocated 
# directly by an established Regional Internet Registry (RIR) or National Internet Registry (NIR) such as 
# ARIN, RIPE, AFRINIC, APNIC, LACNIC or KRNIC or direct RIR allocations. 
files['DROP'] = 'https://www.spamhaus.org/drop/drop.txt'

# Spamhaus Extended DROP List (EDROP)
# EDROP is an extension of the DROP list that includes suballocated netblocks controlled by spammers or cyber criminals. 
# EDROP is meant to be used in addition to the direct allocations on the DROP list. 
files['EDROP'] = 'https://www.spamhaus.org/drop/edrop.txt'

# Spamhaus IPv6 DROP List (DROPv6)
# The DROPv6 list includes IPv6 ranges allocated to spammers or cyber criminals. DROPv6 will only include IPv6 netblocks 
# allocated directly by an established Regional Internet Registry (RIR) or National Internet Registry (NIR) such as 
# ARIN, RIPE, AFRINIC, APNIC, LACNIC or KRNIC or direct RIR allocations. 
files['DROPv6'] = 'https://www.spamhaus.org/drop/dropv6.txt'

# Chekc if file folder exist
name="SPAMHAUS-DROP"
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
        ip_type = 4
    else:
        address_family = socket.AF_INET6
        ip_type = 6

    pfx_dict = {}
    for line in content:
        #print(line)
        if re.match(r'; Last-Modified', line):
            info[drop_type+"-lastModified: "] = line.replace("; Last-Modified: ",drop_type+"-lastModified: ")
            continue
        if re.match(r'; Expires: ', line):
            info[drop_type+"-expires: "] = line.replace("; Expires: ",drop_type+"-expires: ")
            continue

        if re.match(r'^(\d|abcdef)', line.lower()):
            s_line = line.split(" ")
            prefix = unicode(s_line[0], "utf-8")
            ip_family = ipaddress.ip_network(prefix.split("/")[0]).version

            # Proceed only for specyfic type
            if ip_type == ip_family:
                ip_prefix = prefix
            else:
                continue
            
            pfx_dict[ip_prefix] = {}
            pfx_dict[ip_prefix]['net'] = ip_prefix
            pfx_dict[ip_prefix]['dl'] = [ drop_type ]  # DropList
            pfx_dict[ip_prefix]['type'] = ip_family

    pfx_vals = list(pfx_dict.values())
    pfx_vals = sorted(pfx_vals, key=lambda x: socket.inet_pton(address_family, x['net'].split('/')[0]))
    return pfx_vals

def make_tarfile(output_filename, source_dir):
    with tarfile.open(output_filename, "w:gz") as tar:
        tar.add(source_dir, arcname=os.path.basename(source_dir))


def create_info_file(path):
    
    f = open(path, "w")
    f.write("generateDate: "+datetime.now().strftime("%Y-%m-%d-%H-%M-%S")+time.strftime("%z", time.gmtime())+"\n")
    for key,line in sorted(info.items()):
        f.write(line+"\n")
    f.close()

# Main Script
if __name__ == "__main__":
    # Download File
    prefixes = list()
    for drop_type, file_src in files.items():
        try:
            resp, content = Http().request(file_src)
            if resp.status != 200:
                fatal("Unable to load %s - %d %s" % (file_src, resp.status, resp.reason))
            content = content.split("\n")
        except Exception as e:
            print("Unable to load %s - %s" % (file_src, e))
            exit(1)
        
        # Create one big IP dict
        prefixes.extend(list_prefixes(ipv4=True))
        prefixes.extend(list_prefixes(ipv4=False))

    downloadTime = time.time()
 

    # Generate output text files
    file_out = dict()
    file_out['ALL_ipv4'] = list()
    file_out['ALL_ipv6'] = list()
    file_out['ALL'] = list()
    for ip_item in prefixes:
        # Debug
        #pprint(ip_item)

        # IPv4 and IPv6
        file_out['ALL'].append(str(ip_item['net']))

        if ip_item['type'] == 4:
            file_out['ALL_ipv4'].append(str(ip_item['net']))

        if ip_item['type'] == 6:
            file_out['ALL_ipv6'].append(str(ip_item['net']))

        # Services
        for dl in ip_item['dl']:
            try:
                file_out[dl]
            except:
                file_out[dl] = list()
            file_out[dl].append(str(ip_item['net'])) 

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

    #print 'script was running %.2f seconds' % (datetime.now() - startTime)
    endTime = time.time()
    print ('Time:')
    print (' - download in {0} second'.format(downloadTime - startTime))
    print (' - processing in {0} second'.format(endTime - downloadTime))
    print ('   TOTAL: {0} second'.format(endTime - startTime))