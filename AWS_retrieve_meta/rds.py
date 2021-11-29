import boto3
from multiprocessing import Process, Pipe
import re
import datetime
import json
import os
import sys
from copy import deepcopy

ec2 = boto3.client('ec2')
s3 = boto3.resource('s3')
output_path = datetime.datetime.strftime(datetime.date.today(), '%Y/%m/%d/')
yesterday = datetime.datetime.strftime(datetime.date.today() - datetime.timedelta(days=1), '%Y/%m/%d/')

try:
	if os.environ['prefix']:
		output_path = os.environ['prefix'] + '/' + output_path
		yesterday = os.environ['prefix'] + '/' + yesterday
except:
	pass
try:
	topic_arn = os.environ['topic_arn']
except:
	print('Specify SNS Topic ARN')
	sys.exit(1)
try:
	bucket = os.environ['bucket']
except:
	print('Specify bucket')
	sys.exit(2)

def each_region(region, pipe_in):
	rds_client = boto3.client('rds', region_name=region)
	rds = rds_client.describe_db_instances()
	instances = list()
	for instance in rds['DBInstances']:
		if "docdb" == instance['Engine']:
			continue
		instances.append({'region': region,'instance_name': instance['DBInstanceIdentifier'], 'instance_type': instance['DBInstanceClass'], 'multi_az': str(instance['MultiAZ']), 'engine': instance['Engine'], 'storage_size': instance['AllocatedStorage'], 'storage_type': instance['StorageType']})
	pipe_in.send(instances)

def create_csv(data):
	data = deepcopy(data)
	csv = 'Region\tInstance Name\tInstance Type\tMulti-AZ\tEngine\tEBS Type\tEBS Size'
	for region_data in data:
		region = region_data['region']
		csv = csv + '\n' + str(region) + '\t' + str(region_data['instance_name']) + '\t' + str(region_data['instance_type']) + '\t' + str(region_data['multi_az']) + '\t' + str(region_data['engine']) + '\t' + str(region_data['storage_type']) + '\t' + str(region_data['storage_size'])
	return csv

def compare(today, yesterday):
	changes = list()
	yesterday_data = set([str(i) for i in yesterday])
	today_data = set([str(i) for i in today])
	changes = [json.loads(re.sub("'", '"', terminated_instance)) for terminated_instance in list(yesterday_data - today_data)] + [json.loads(re.sub("'", '"', launched_instance)) for launched_instance in list(today_data - yesterday_data)]
	return changes

def ct(changes):
	yesterday = datetime.date.today() - datetime.timedelta(days=1)
	output = list()
	for change in changes:
		instance = change['instance_name']
		region = change['region']
		for event in boto3.client('cloudtrail', region_name=region).lookup_events(LookupAttributes=[{'AttributeKey': 'ResourceName', 'AttributeValue': instance}], StartTime=datetime.datetime(yesterday.year, yesterday.month, yesterday.day))['Events']:
			for i in event['Resources']:
				instance_name = None
				if i['ResourceType'] == 'AWS::RDS::DBInstance':
					instance_name = i['ResourceName']
					break
			output.append({'Event': event['EventName'], 'Time': event['EventTime'], 'User': event.get('Username'), 'Resource': instance_name, 'instance_type': change['instance_type'], "multi_az": change['multi_az'], 'engine': change['engine'], 'storage_size': change['storage_size'], 'storage_type': change['storage_type'], 'Region': region})
	return output

def create_body(body, events):
	for event in events:
		body = body + '\n' + event['Event'] + '\t' + str(event['Time']) + '\t' + event['User'] + '\t' + event['Resource'] + '\t' + event['instance_type'] + '\t' + event['multi_az'] + '\t' + event['engine'] + '\t' + str(event['storage_size']) + '\t' + event['storage_type'] + '\t' + event['Region']
	return body

def lambda_handler(event, context):
	output = list()
	plist = list()
	output = list()
	for region in [region['RegionName'] for region in ec2.describe_regions()['Regions']]:
		pipe_out, pipe_in = Pipe(False)
		process = Process(target=each_region, args=(region, pipe_in))
		process.start()
		plist.append(process)
		output.append({'region': region, 'data':pipe_out})
	for proc in plist:
		proc.join()
	output = [data['data'].recv() for data in output]
	data = list()
	for i in output:
		data = data + i
	csv = create_csv(data)
	s3.Object(bucket, output_path + 'rds_instances.json').put(Body=str(data))
	s3.Object(bucket, output_path + 'rds_instances.csv').put(Body=csv)
	
	try:
		last_data = json.loads(re.sub("'", '"', s3.Object(bucket, yesterday + 'rds_instances.json').get()['Body'].read().decode('utf-8')))
	except:
		return 1
	events = ct(compare(data, last_data))
	if events:
		body = 'Event\tTime\tUser\tInstance_name\tInstance type\tMulti AZ\tEngine\tStorage size\tStorage type\tRegion'
		body = create_body(body, events)
		s3.Object(bucket, output_path + 'rds_transactions.csv').put(Body=body)
		boto3.client('sns').publish(TopicArn=topic_arn, Message=body, Subject='RDS Instance transaction notifier ' + datetime.datetime.strftime(datetime.date.today(), '%Y/%m/%d'))
	return 0