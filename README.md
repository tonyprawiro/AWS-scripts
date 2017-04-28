# Collection of Amazon Web Services scripts

- `access-keys.py` to generate a report of available access keys in your AWS account. Useful for taking a quick glance to see which keys are there and remove unneeded ones

- `cloudflare-secgroup.py` is a Lambda function to update a VPC security group to reflect the list of IPv4 that Cloudflare has. This script is useful if you need to whitelist Cloudflare's reverse proxies automatically. Here's a sample IAM policy :

```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "ViewAndUpdateSecurityGroups",
            "Effect": "Allow",
            "Action": [
                "ec2:AuthorizeSecurityGroupIngress",
                "ec2:RevokeSecurityGroupIngress",
                "ec2:DescribeSecurityGroups"
            ],
            "Resource": [
                "*"
            ]
        }
    ]
}
```

- `ansible-tower-hosts.py` is a script to update Ansible tower's inventory file with association of SSH credentials to the EC2 machines

- `find-unattached-secgroups.py` is a script to find unattached security groups
