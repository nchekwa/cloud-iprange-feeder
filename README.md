# juniper-srx-feeder

## How to run:
1) need to have pythone + pip (debian: apt-get install python-pip | centos: yum install -y pip)
2) install needed exttra lib -> pip install -r requirements.txt
3) clone repo ie. to: /opt/feeder/
4) run feeder inside folder: python feeder_AMAZON_AWS.py

Example console output:
```bash
root@debian:/opt/feeder# python feeder_AMAZON_AWS.py
Time:
 - download in 0.467345952988 second
 - processing in 0.148323059082 second
   TOTAL: 0.61566901207 second
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
set security dynamic-address feed-server MyAmazonFeed url http://<server>/feeder/files/AMAZON-AWS.tgz
set security dynamic-address feed-server MyAmazonFeed update-interval 30
set security dynamic-address feed-server MyAmazonFeed hold-interval 3600
set security dynamic-address feed-server MyAmazonFeed feed-name AWS_ALL path AMAZON-AWS/ALL
set security dynamic-address address-name AWS_ALL_IPs profile feed-name AWS_ALL
```

# SRX
```
> show configuration security dynamic-address 
feed-server MyAmazonFeed {
    url http://<server>/feeder/files/AMAZON-AWS.tgz;
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
- SPAMHAUS-DROP - https://www.spamhaus.org/drop/[drop.txt,edrop.txt,dropv6.txt]
