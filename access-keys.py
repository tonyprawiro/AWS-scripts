#!/usr/bin/python

import subprocess, os, json, csv

cmd = ["aws", "iam", "list-users"]

with open(os.devnull, 'w') as fnull:
	p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=fnull)
	out, err = p.communicate()

users = json.loads(out)['Users']
total_users = len(users)
for i in range(0, total_users):
	line = []
	line.append(users[i]['UserName'])
	line.append(users[i]['CreateDate'])
	line.append('')
	# get access keys
	cmd = ["aws", "iam", "list-access-keys", "--user-name", users[i]["UserName"]]
	out = ""
	with open(os.devnull, 'w') as fnull:
		p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=fnull)
		out, err = p.communicate()
	access_keys = json.loads(out)['AccessKeyMetadata']
	total_access_keys = len(access_keys)
	for j in range(0, total_access_keys):
		line.append(access_keys[j]['AccessKeyId'])
		line.append(access_keys[j]['CreateDate'])
		# get last used info
		cmd = ["aws", "iam", "get-access-key-last-used", "--access-key-id", access_keys[j]["AccessKeyId"]]
		out = ""
		with open(os.devnull, 'w') as fnull:
			p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=fnull)
			out, err = p.communicate()
		access_key_last_used = json.loads(out)['AccessKeyLastUsed']
		last_used_date = ""
		try:
			last_used_date = access_key_last_used['LastUsedDate'] # potentially not defined
		except:
			pass
		line.append(last_used_date)
		line.append(access_key_last_used['Region'])
		line.append(access_key_last_used['ServiceName'])
		line.append('')
	print '"' + '","'.join(line) + '"
