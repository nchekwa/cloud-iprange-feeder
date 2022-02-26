# cloud-iprange-feeder
IP address ranges from Cloud Providers

## How to run:
1) need to have python + pip (debian: apt-get install python-pip | centos: yum install -y pip)<br>
 Scripts was innitialy writen in pyton2 (but were tune to work with v3 also).
2) install needed exttra lib -> pip install -r requirements.txt
3) clone repo ie. to: /opt/cloud-iprange-feeder/
4) run feeder inside folder: python feeder_AMAZON_AWS.py

Example console output:
```bash
root@debian:/opt/cloud-iprange-feeder# python feeder_AMAZON-AWS.py
-----------------------------------------------------------------
Process: feeder_AMAZON-AWS.py at 2021-01-22 14:11:57.906558
Result:
 - download in 0.206455945969 second
 - processing in 0.590703964233 second
   TOTAL: 0.797159910202 second
```

## What feeder will do?
Feeder going to download IP Prefix list, parse it and generate in 'files' folder parsed files:
- text files split by region/service/ALL (files contains IP ranges)
- tgz which will contain all those text file in one compress file (for juniper SRX feed-server)
- create info file - with time generation (when feeder was run)

```
ie:
files/AMAZON-AWS
├── ALL
├── ALL_ipv4
├── ALL_ipv6
├── rgn_af-south-1
├── rgn_ap-east-1
├── rgn_ap-northeast-1
...
├── svc_AMAZON
├── svc_S3
└── svc_WORKSPACES_GATEWAYS
files/AMAZON-AWS.tgz
files/AMAZON-AWS.txt
```

## How to use TGZ file
SRX#
```
[edit security dynamic-address]
set security dynamic-address feed-server MyAmazonFeed url http://<server>/cloud-iprange-feeder/files/AMAZON-AWS.tgz
set security dynamic-address feed-server MyAmazonFeed update-interval 30
set security dynamic-address feed-server MyAmazonFeed hold-interval 3600
set security dynamic-address feed-server MyAmazonFeed feed-name AWS_ALL path AMAZON-AWS/ALL
set security dynamic-address address-name AWS_ALL_IPs profile feed-name AWS_ALL
```

# SRX
```
> show configuration security dynamic-address 
feed-server MyAmazonFeed {
    url http://<server>/cloud-iprange-feeder/files/AMAZON-AWS.tgz;
    update-interval 30;
    hold-interval 3600;
    feed-name AWS_ALL {
        path AMAZON-AWS/ALL;
    }
}
address-name AWS_ALL_IPs {
    profile {
        feed-name AWS_ALL;
    }
}
```
```
root@vSRX> show security dynamic-address summary address-name AWS_ALL_IPs
```
Juniper SRX output command example in doc\ folder

## List of feeds:
- AMAZON-AWS - https://ip-ranges.amazonaws.com/ip-ranges.json
- GITHUB - https://api.github.com/meta
- GOOGLE-GCS - https://www.gstatic.com/ipranges/cloud.json
- MICROSOFT-AZURE - https://www.microsoft.com/en-us/download/details.aspx?id=56519
- Microsoft O365 - https://endpoints.office.com/endpoints/worldwide?clientrequestid=b10c5ed1-bad1-445f-b386-b919946339a7
- ORACLE-OCI - https://docs.cloud.oracle.com/en-us/iaas/tools/public_ip_ranges.json
- MAXMIND_GeoIP - https://www.maxmind.com/

ToDo:
- "Alibaba Cloud" - list not available
- Cloudflare - https://www.cloudflare.com/ips-v4 | https://www.cloudflare.com/ips-v6

## If you looking for Threat Protection - please check:
http://iplists.firehol.org/<br>
https://github.com/firehol/blocklist-ipsets


## Othere Geo-IP Feeds:
https://github.com/sapics/ip-location-db#readme
https://ipinfo.io/
ASN-https://bgp.potaroo.net/cidr/autnums.html