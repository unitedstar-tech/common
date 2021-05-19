#!/bin/python
import boto3
import requests
ips = requests.get('http://d7uri8nf7uskq.cloudfront.net/tools/list-cloudfront-ips').json()['CLOUDFRONT_GLOBAL_IP_LIST']
ec2 = boto3.client('ec2')
vpcs = list()
for vpc in ec2.describe_vpcs()['Vpcs']:
	vpcs.append(vpc['VpcId'])

ip_permissions = list()
for ip in ips:
	ip_permissions.append({'CidrIp': ip})

for vpc in vpcs:
	sg = ec2.describe_security_groups(Filters=[{'Name': 'group-name', 'Values': ['CloudFront']}, {'Name': 'vpc-id', 'Values': [vpc]}])['SecurityGroups'][0]['IpPermissions'][0]['IpRanges']
	for ip in ips:
		if not ip in str(sg):
			print('+ ' + ip)
	for ip in sg:
		if not ip['CidrIp'] in ips:
			print('- ' + ip['CidrIp'])
