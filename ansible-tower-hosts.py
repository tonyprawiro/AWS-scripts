# -*- coding: utf-8 -*-

"""
Update tower script
~~~~~~~~~~~~

This script updates the hosts in Ansible Tower and add "ansible_user", "ansible_ssh_private_key", and
"ansible_python_interpreter" into host's variables.

This script is needed because Ansible (and Tower) doesn't know by default how to SSH into a machine.
Usually, sysadmins would put SSH username and config into the inventory manually and into .ssh/config file,
but this script makes it easier to do that by looking at a specific tag in EC2. For instance, if an EC2 instance has
a tag of "LogInAs" with value "ec2-user/mykeyfile", this script will insert these variables into Ansible Tower's
host variables:

ansible_user: "ec2-user"
ansible_ssh_private_key: "/etc/tower/ssh_keys/mykeyfile.pem"

:copyright: (c) 2016 Infocomm Development Authority (IDA) of Singapore
:license: Restricted
"""

import subprocess
import json
import requests
import yaml

tower_hostname = "tower.domain.com"
tower_username = "admin"
tower_password = "secret"
tower_api_base = "https://tower.domain.com/api/v1"
aws_cli_path = "/usr/local/bin/aws"
tower_token = ""
aws_machines = []


def get_aws_machines(aws_cli_path, profile):
    """
    Gathers all EC2 instances in a specified AWS credential profile. specifically trying to get and
    process the value of LogInAs tag

    :param aws_cli_path: string, the full path to aws-cli executable
    :param profile: the credential profile (in $HOME/.aws/credentials file, you should have at least "default" profile)
    :return: always None
    :rtype: None
    """

    p = subprocess.Popen([aws_cli_path, "ec2", "describe-instances", "--region", "ap-southeast-1", "--profile", profile],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    out, err = p.communicate()
    obj = json.loads(out)
    for Reservation in obj["Reservations"]:
        for Instance in Reservation["Instances"]:
            item = {}
            for Tag in Instance["Tags"]:
                if Tag["Key"] == "LogInAs":
                    if "/" in Tag["Value"]:
                        username, pemfile = Tag["Value"].split("/")
                        item["instanceid"] = Instance["InstanceId"]
                        item["username"] = username.strip()
                        item["pemfile"] = pemfile.strip()
                    if Tag["Key"] == "ansible_python_interpreter" and Tag["Value"].strip() != "":
                        item["ansible_python_interpreter"] = Tag["Value"].strip()
            if bool(item):
                aws_machines.append(item)
    return None


def tower_authenticate(base_url, username, password):
    """Perform authentication to get authorization token

    :param base_url: string, the base url of the Tower API
    :param username: string, username
    :param password: string, password
    :return: authentication token, or blank if any failure
    :rtype: string
    """

    try:
        payload = {"username": username, "password": password}
        r = requests.post("%s/authtoken/" % base_url, json=payload, headers={"Content-type": "application/json"})
        if r.status_code == 200:
            return json.loads(r.text)["token"]
    except:
        pass

    return ""


def get_tower_hosts_page(base_url, token, page):
    """Get the list of hosts in Tower, on a specific page

    :param base_url: string, the base url of the Tower API
    :param token: string, authorization token
    :param page: integer, page to retrieve (starts with 1)
    :return: parsed host list
    :rtype: dict
    """

    r = requests.get("%s/hosts?page=%d" % (base_url, page), headers={"Authorization": "Token %s" % token})
    if r.status_code == 200:
        o = json.loads(r.text)
        return o
    else:
        return None


def get_tower_host(base_url, token, host_id):
    """Get the host details of a specific host ID

    :param base_url: string, the base url of the Tower API
    :param token: string, authorization token
    :param host_id: integer, host ID to retrieve
    :return: host details
    :rtype: dict
    """
    r = requests.get("%s/hosts/%d" % (base_url, host_id), headers={"Authorization": "Token %s" % token})
    if r.status_code == 200:
        o = json.loads(r.text)
        return o
    else:
        return None


def get_aws_machine_details(machines, ec2_id):
    """Match the EC2 instance ID between the ones returned by AWS CLI and the Tower API, to get the username & pemfile

    :param machines: list, AWS machines
    :param ec2_id: string, the EC2 instance ID from Tower
    :return: username and pemfile
    :rtype: tuple
    """
    for Machine in machines:
        if Machine["instanceid"] == ec2_id:
            return Machine
    return {}


def patch_tower_machine(base_url, token, host_id, newvar):
    """Sends PATCH request to Tower API, mainly to update the host variables

    :param base_url:  string, the base url of the Tower API
    :param token: string, authorization token
    :param host_id: integer, host ID to retrieve
    :param newvar: dict, the new variable
    :return: True if request yields 200, otherwise False
    :rtype: bool
    """
    r = requests.patch("%s/hosts/%d/" % (base_url, host_id),
        json={"variables": json.dumps(newvar)},
        headers={"Authorization": "Token %s" % token, "Content-type": "application/json"})
    return r.status_code == 200


def process_tower_hosts(base_url, token, machines):
    """Iterate all hosts in Tower, then update the host variables according to the tags found

    :param base_url:  string, the base url of the Tower API
    :param token: string, authorization token
    :param machines: list, AWS machines
    :return: None
    :type: None
    """
    pg = 1

    is_continue = True

    while is_continue:

        tower_hosts_obj = get_tower_hosts_page(base_url, token, pg)

        if tower_hosts_obj["next"] is not None:
            pg += 1
        else:
            is_continue = False

        for Host in tower_hosts_obj["results"]:
            host_detail = get_tower_host(base_url, token, Host["id"])
            host_variables = None
            # Try to parse variables as JSON
            try:
                host_variables = json.loads(host_detail["variables"])
            except:
                # Error ? try to parse as YAML
                try:
                    host_variables = yaml.load(host_detail["variables"])
                except:
                    # Still error ? bochup...
                    pass
            if host_variables is not None:
                awsmachine = get_aws_machine_details(machines, host_variables["ec2_id"])
                username = ""
                pemfile = ""
                python_interpreter = ""
                try:
                    username = awsmachine["username"]
                except:
                    pass
                try:
                    pemfile = awsmachine["pemfile"]
                except:
                    pass
                try:
                    python_interpreter = awsmachine["ansible_python_interpreter"]
                except:
                    pass
                if username != "" and pemfile != "":
                    host_variables["ansible_user"] = username
                    host_variables["ansible_ssh_private_key"] = "/etc/tower/ssh_keys/%s.pem" % pemfile
                    if python_interpreter != "":
                        host_variables["ansible_python_interpreter"] = python_interpreter
                    patch_status = patch_tower_machine(base_url, token, Host["id"], host_variables)
                    if patch_status:
                        print "Updated host vars for %s / %s" % (
                        host_variables["ec2_id"], host_variables["ec2_private_ip_address"])
                    else:
                        print "Failed to update Tower host variables for %s" % host_variables["ec2_id"]
                else:
                    print "Unable to find LogInAs detail for %s" % host_variables["ec2_id"]
            else:
                print "Unable to determine host variables for host #%s from Tower" % Host["id"]

    return None


if __name__ == "__main__":

    # Authenticate to get the token
    tower_token = tower_authenticate(tower_api_base, tower_username, tower_password)

    if tower_token != "":

        # Gather all AWS machines
        get_aws_machines(aws_cli_path, "default")

        # Process all hosts in the Tower
        process_tower_hosts(tower_api_base, tower_token, aws_machines)

    else:

        print "Authentication failed"
