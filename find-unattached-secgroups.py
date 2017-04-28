#!/usr/bin/env python

import subprocess

aws_region = 'ap-southeast-1'

aws_secgroups = {
    "default": {}
}

group_ids = []

for aws_profile in [ 'default' ]:

    print "Profile: %s" % aws_profile

    # Get all secgroups
    p = subprocess.Popen("aws ec2 describe-security-groups --profile %s --region %s --query 'SecurityGroups[*].GroupId'  --output text | tr '\t' '\n'" % (aws_profile, aws_region), stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell = True)
    out, err = p.communicate()
    for line in out.split('\n'):
        if line.strip()[:3]=='sg-':
            secgroup_name = line.strip()
            # Check if secgroup exists in collection, otherwise initialize it
            try:
                testcount = aws_secgroups[aws_profile][secgroup_name]["count"]
            except:
                aws_secgroups[aws_profile][secgroup_name] = {}
                aws_secgroups[aws_profile][secgroup_name]["count"] = 0

    # Get secgroup usage from EC2 instances
    p = subprocess.Popen("aws ec2 describe-instances --profile %s --region %s --query 'Reservations[*].Instances[*].SecurityGroups[*].GroupId' --output text | tr '\t' '\n' | sort" % (aws_profile, aws_region), stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell = True)
    out, err = p.communicate()
    for line in out.split('\n'):
        if line.strip()[:3]=='sg-':
            secgroup_name = line.strip()
            aws_secgroups[aws_profile][secgroup_name]["count"] += 1

    # Check which ones have zero count
    del group_ids[0:]
    for idx, aws_secgroup in enumerate(aws_secgroups[aws_profile]):
        if aws_secgroups[aws_profile][aws_secgroup]["count"]==0:
            group_ids.append(aws_secgroup)

    cmd = "aws ec2 describe-security-groups --profile %s --region %s --group-ids %s --query \"SecurityGroups[*].[GroupId, GroupName]\" --output text" % (aws_profile, aws_region, " ".join(group_ids))
    p = subprocess.Popen(cmd, stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell = True)
    out, err = p.communicate()
    print out
