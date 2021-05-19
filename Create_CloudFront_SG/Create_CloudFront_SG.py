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
	if not ec2.describe_security_groups(Filters=[{'Name': 'group-name', 'Values': ['CloudFront']}, {'Name': 'vpc-id', 'Values': [vpc]}])['SecurityGroups']:
		ec2.create_security_group(Description='CloudFront', GroupName='CloudFront', VpcId=vpc)
	sg_id = ec2.describe_security_groups(Filters=[{'Name': 'group-name', 'Values': ['CloudFront']}, {'Name': 'vpc-id', 'Values': [vpc]}])['SecurityGroups'][0]['GroupId']
	sg_ipranges = ec2.describe_security_groups(Filters=[{'Name': 'group-name', 'Values': ['CloudFront']}, {'Name': 'vpc-id', 'Values': [vpc]}])['SecurityGroups'][0]['IpPermissions'][0]['IpRanges']
	for ip_permission in ip_permissions:
		if not ip_permission['CidrIp'] in str(sg_ipranges):
			ec2.authorize_security_group_ingress(GroupId=sg_id, IpPermissions=[{'FromPort': -1, 'IpProtocol': '-1', 'ToPort': -1, 'IpRanges': [ip_permission]}])
			print(ip_permission)
	for sg_iprange in sg_ipranges:
		if not sg_iprange['CidrIp'] in ips:
			ec2.revoke_security_group_ingress(GroupId=sg_id, IpPermissions=[{'FromPort': -1, 'IpProtocol': '-1', 'ToPort': -1, 'IpRanges': [sg_iprange]}])
			print(sg_iprange)