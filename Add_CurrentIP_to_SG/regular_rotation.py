import boto3
import datetime
import os
from multiprocessing import Process
def lambda_handler(event, context):
	# 変数定義
	ec2 = boto3.client('ec2')
	regions = list()
	for i in ec2.describe_regions()['Regions']:
		regions.append(i['RegionName'])
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

	# 各リージョン毎のSubprocessを起動
	for region in regions:
		args = (region, sg_name, invalid)
		Process(target=each_region, args=args).start()
	return "OK"

def each_region(region, sg_name, invalid):
	ec2 = boto3.client('ec2', region_name=region)
	vpcs = list()
	for vpc in ec2.describe_vpcs()['Vpcs']:
		vpcs.append(vpc['VpcId'])
	for vpc in vpcs:
		args = (ec2, vpc, sg_name, invalid)
		Process(target=each_vpc, args=args).start()

def each_vpc(ec2, vpc, sg_name, invalid):
	vpc_sg_name = vpc + '-' + sg_name
	sgs = ec2.describe_security_groups(Filters=[{'Name': 'group-name', 'Values': [vpc_sg_name]}, {'Name': 'vpc-id', 'Values': [vpc]}])['SecurityGroups']
	if sgs:
		sg_id = sgs[0]['GroupId']
		sgs = sgs[0].get('IpPermissions')
		if sgs:
			sgs = sgs[0].get('IpRanges')
			for sg in sgs:
				if sg.get('Description') and datetime.datetime.strptime(sg.get('Description'), '%Y-%m-%d %H:%M:%S.%f') <= invalid:
					ec2.revoke_security_group_ingress(GroupId=sg_id, IpPermissions=[{'FromPort': -1, 'IpProtocol': '-1', 'ToPort': -1, 'IpRanges': [sg]}])
					print("Removed " + str(sg) + " from " + str(sg_id))
