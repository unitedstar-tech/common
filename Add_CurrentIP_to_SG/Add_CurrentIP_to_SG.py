import boto3
import datetime
import os
def lambda_handler(event, context):
	try:
		sip = event['sip'] + "/32"
		print(sip)
	except:
		sip = "1.2.3.4/32"
	ec2 = boto3.client('ec2')
	try:
		sg_name = os.environ['sg_name']
	except:
		sg_name = "Developers"
	try:
		duration = int(os.environ['duration'])
	except:
		duration = 3
	now = datetime.datetime.now()
	invalid = now - datetime.timedelta(days=duration)
	vpcs = list()
	for vpc in ec2.describe_vpcs()['Vpcs']:
		vpcs.append(vpc['VpcId'])
	for vpc in vpcs:
		vpc_sg_name = vpc + '-' + sg_name
		sgs = ec2.describe_security_groups(Filters=[{'Name': 'group-name', 'Values': [vpc_sg_name]}, {'Name': 'vpc-id', 'Values': [vpc]}])['SecurityGroups']
		if sgs:
			sg_id = sgs[0]['GroupId']
			sgs = sgs[0].get('IpPermissions')
			if sgs:
				sgs = sgs[0].get('IpRanges')
				for sg in sgs:
					if sg.get('Description') and (datetime.datetime.strptime(sg.get('Description'), '%Y-%m-%d %H:%M:%S.%f') <= invalid or sip in sg['CidrIp']):
						ec2.revoke_security_group_ingress(GroupId=sg_id, IpPermissions=[{'FromPort': -1, 'IpProtocol': '-1', 'ToPort': -1, 'IpRanges': [sg]}])
						print("Removed " + str(sg) + " from " + str(sg_id))
		else:
			sg_id = ec2.create_security_group(Description=vpc_sg_name, GroupName=vpc_sg_name, VpcId=vpc)['GroupId']
			print("Created " + str(sg_id))
		try:
			ec2.authorize_security_group_ingress(GroupId=sg_id, IpPermissions=[{'FromPort': -1, 'IpProtocol': '-1', 'ToPort': -1, 'IpRanges': [{'CidrIp': sip, 'Description': str(now)}]}])
			print("Add " + sip + " to " + str(sg_id) + " at " + str(now))
		except:
			pass
	return sip