import boto3
import datetime
import os
def lambda_handler(event, context):
	try:
		sip = event['rawQueryString'].split("=")[1] + "/32"
	except:
		sip = "1.2.3.4/32"
	ec2 = boto3.client('ec2')
	try:
		sg_name = os.environ['sg_name']
	except:
		sg_name = "Developers"
	now = datetime.datetime.now()
	invalid = now - datetime.timedelta(days=3)
	vpcs = list()
	for vpc in ec2.describe_vpcs()['Vpcs']:
		vpcs.append(vpc['VpcId'])
	for vpc in vpcs:
		vpc_sg_name = vpc + '-' + sg_name
		if not ec2.describe_security_groups(Filters=[{'Name': 'group-name', 'Values': [vpc_sg_name]}, {'Name': 'vpc-id', 'Values': [vpc]}])['SecurityGroups']:
			ec2.create_security_group(Description=vpc_sg_name, GroupName=vpc_sg_name, VpcId=vpc)
		sg_id = ec2.describe_security_groups(Filters=[{'Name': 'group-name', 'Values': [vpc_sg_name]}, {'Name': 'vpc-id', 'Values': [vpc]}])['SecurityGroups'][0]['GroupId']
		try:
			ec2.authorize_security_group_ingress(GroupId=sg_id, IpPermissions=[{'FromPort': -1, 'IpProtocol': '-1', 'ToPort': -1, 'IpRanges': [{'CidrIp': sip, 'Description': str(now)}]}])
		except:
			pass
		sgs = ec2.describe_security_groups(Filters=[{'Name': 'group-name', 'Values': [vpc_sg_name]}, {'Name': 'vpc-id', 'Values': [vpc]}])['SecurityGroups'][0]['IpPermissions'][0]['IpRanges']
		for sg in sgs:
			if sg.get('Description') and datetime.datetime.strptime(sg.get('Description'), '%Y-%m-%d %H:%M:%S.%f') <= invalid:
				ec2.revoke_security_group_ingress(GroupId=sg_id, IpPermissions=[{'FromPort': -1, 'IpProtocol': '-1', 'ToPort': -1, 'IpRanges': [sg]}])
				print(sg)
	return sip