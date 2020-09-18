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

# Start timer
startTime = time.time()


# Chekc if file folder exist
name="MICROSOFT-AZURE"
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
        ip_prefix_label = 'ipv4Prefix'
        ip_type = 4
    else:
        address_family = socket.AF_INET6
        prefixes_label = 'prefixes'
        ip_prefix_label = 'ipv6Prefix'
        ip_type = 6

    pfx_dict = {}
    for ip_item in ipranges['values']:
        for prefix in ip_item['properties']['addressPrefixes']:
            # Check what type of the Prefix it is (IPv4 vs. IPv6)
            ip_family = ipaddress.ip_network(prefix.split("/")[0]).version

            # Proceed only for specyfic type
            if ip_type == ip_family:
                ip_prefix = prefix
            else:
                continue

            # Split name on Service Name and Region Name
            if "." in ip_item['name']:
                svc_name,rgn_name =  ip_item['name'].split('.')
            else:
                svc_name = ip_item['name']
                rgn_name = None

            # Main assign loop
            if ip_prefix not in pfx_dict:
                pfx_dict[ip_prefix] = {}
                pfx_dict[ip_prefix]['net'] = ip_prefix
                pfx_dict[ip_prefix]['nf'] = ip_item['properties']['networkFeatures']
                pfx_dict[ip_prefix]['type'] = ip_type
  
                # Services (by names)
                if rgn_name == None:
                    pfx_dict[ip_prefix]['svc'] = [ svc_name ]
                else:
                    pfx_dict[ip_prefix]['svc'] = [ svc_name ]
                    pfx_dict[ip_prefix]['svc'].append(svc_name+"_"+rgn_name )
                
                # Services (by systemService)
                if ip_item['properties']['systemService'] != "":
                    if ip_item['properties']['systemService'] != svc_name:
                        pfx_dict[ip_prefix]['svc'].append(ip_item['properties']['systemService'])
                else:
                    pfx_dict[ip_prefix]['svc'].append("NoSystemService")

                # Regions
                if ip_item['properties']['regionId'] == 0:
                    pfx_dict[ip_prefix]['rgn'] = [ "00_NoRegionDefined" ]
                else: 
                    pfx_dict[ip_prefix]['rgn'] = [ str(ip_item['properties']['regionId']).zfill(2)+"_"+ip_item['properties']['region'] ] 
                    pfx_dict[ip_prefix]['rgn'].append("ALL")
            else:
                if rgn_name != None:
                    pfx_dict[ip_prefix]['svc'].append(svc_name+"_"+rgn_name )
                else:
                    pfx_dict[ip_prefix]['svc'].append(svc_name)


            if ip_family == 4 and ip_item['properties']['regionId'] != 0:
                pfx_dict[ip_prefix]['rgn'].append("ALL_ipv4")
            if ip_family == 6 and ip_item['properties']['regionId'] != 0:
                pfx_dict[ip_prefix]['rgn'].append("ALL_ipv6")


    pfx_vals = list(pfx_dict.values())
    pfx_vals = sorted(pfx_vals, key=lambda x: socket.inet_pton(address_family, x['net'].split('/')[0]))

    return pfx_vals


def make_tarfile(output_filename, source_dir):
    with tarfile.open(output_filename, "w:gz") as tar:
        tar.add(source_dir, arcname=os.path.basename(source_dir))


def create_info_file(path):
    f = open(path, "w")
    f.write("fileName: "+json_file_name+"\n"+
            "changeNumber: "+str(ipranges['changeNumber'])+"\n"+
            "generateDate: "+datetime.now().strftime("%Y-%m-%d-%H-%M-%S")+time.strftime("%z", time.gmtime())+"\n")
    f.close()

# Main Script
if __name__ == "__main__":
    h = Http()
    (resp_headers, content) = h.request('https://www.microsoft.com/en-us/download/details.aspx?id=56519', headers={'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:80.0) Gecko/20100101 Firefox/80.0'})
    search_file = re.findall(r'ServiceTags[^\/]+(?=\.)\.json',content)
    json_file_name = search_file[0]

    # Download File
    ip_ranges = "https://download.microsoft.com/download/7/1/D/71D86715-5596-4529-9B13-DA13A5DE5B63/"+json_file_name
    try:
        resp, content = Http().request(ip_ranges)
        if resp.status != 200:
            fatal("Unable to load %s - %d %s" % (ip_ranges, resp.status, resp.reason))
        content = content.decode('latin1')
        ipranges = json.loads(content)
    except Exception as e:
        fatal("Unable to load %s - %s" % (ip_ranges, e))
    downloadTime = time.time()

    # Create one big IP dict
    prefixes = list()
    prefixes.extend(list_prefixes(ipv4=True))
    prefixes.extend(list_prefixes(ipv4=False))

    # Check if downloaded json contains prefixes
    if len(prefixes) < 1:
        fatal("No prefixes found")

    # Generate output text files
    file_out = dict()
    file_out['ALL_ipv4'] = list()
    file_out['ALL_ipv6'] = list()
    file_out['ALL'] = list()
    for ip_item in prefixes:
        # Debug Objects
        #pprint(ip_item)
        
        # IPv4 and IPv6
        file_out['ALL'].append(str(ip_item['net']))

        if ip_item['type'] == 4:
            file_out['ALL_ipv4'].append(str(ip_item['net']))

        if ip_item['type'] == 6:
            file_out['ALL_ipv6'].append(str(ip_item['net']))

        # Regions
        for rgn in ip_item['rgn']:
            region = "rgn_"+rgn
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
        #res = [i for n, i in enumerate(file_item) if i not in file_item[:n]] 
        with open(file_name, 'w') as f:
            for item in file_item:
                f.write("%s\n" % str(item))

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