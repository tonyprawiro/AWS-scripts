from __future__ import print_function

import json
import httplib
import boto3

secgroup_id = 'sg-abcd1234'

print('Loading function')

def lambda_handler(event, context):

    # Get the current rules
    ec2 = boto3.client('ec2', region_name = 'ap-southeast-1')
    secgroups = ec2.describe_security_groups(GroupIds=[secgroup_id])

    # Revoke all rules and addresses under this secgroup
    for ippermission in secgroups["SecurityGroups"][0]["IpPermissions"]:
        for cidrip in ippermission["IpRanges"]:
            ec2.revoke_security_group_ingress(GroupId=secgroup_id,
                IpProtocol=ippermission["IpProtocol"],
                FromPort=ippermission["FromPort"],
                ToPort=ippermission["ToPort"],
                CidrIp=cidrip["CidrIp"])

    # Get the latest Cloudflare IPv4 set
    conn = httplib.HTTPSConnection('www.cloudflare.com:443')
    conn.request("GET", "/ips-v4")
    res = conn.getresponse()
    data = res.read()
    for line in data.split("\n"):
        ipv4 = line.strip()
        if len(ipv4) > 0:

            # HTTP rule
            ec2.authorize_security_group_ingress(GroupId=secgroup_id,
                IpProtocol="tcp",
                FromPort=80,
                ToPort=80,
                CidrIp=ipv4)

            # HTTPS rule
            ec2.authorize_security_group_ingress(GroupId=secgroup_id,
                IpProtocol="tcp",
                FromPort=443,
                ToPort=443,
                CidrIp=ipv4)

    return True
