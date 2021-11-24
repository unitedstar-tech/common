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
	ec2_client = boto3.client('ec2', region_name=region)
	ec2_resource = boto3.resource('ec2', region_name=region)
	instances = [instance['Instances'][0]['InstanceId'] for instance in ec2_client.describe_instances()['Reservations']]
	plist = list()
	output = list()
	for instance in instances:
		pipe_out2, pipe_in2 = Pipe(False)
		process = Process(target=extract_instance_data, args=(ec2_resource, instance, pipe_in2))
		process.start()
		plist.append(process)
		output.append(pipe_out2)
	for proc in plist:
		proc.join()
	output = [i.recv() for i in output]
	pipe_in.send(output)

def extract_instance_data(ec2_resource, instance, pipe_in):
	instance_data = ec2_resource.Instance(instance)
	instance_tags = instance_data.tags
	if not instance_tags:
		instance_tags = ['']
	for tag in instance_tags:
		if "Name" in str(tag):
			instance_name = tag.get('Value')
			break
		else:
			instance_name = '(' + instance + ')'
	instance_type = instance_data.instance_type
	attached_ebs = list()
	for ebs in instance_data.block_device_mappings:
		volume = ec2_resource.Volume(ebs['Ebs']['VolumeId'])
		ebs_type = volume.volume_type
		ebs_size = volume.size
		attached_ebs.append({'ebs_type': ebs_type, 'ebs_size': ebs_size})
	instance_data = {'Instance_ID': instance, 'Instance_name': instance_name, 'Instance_type': instance_type, 'EBS': attached_ebs}
	pipe_in.send(instance_data)

def create_csv(data):
	data = deepcopy(data)
	csv = 'Region\tInstance Name\tInstance ID\tInstance Type\tEBS Type\tEBS Size'
	for region_data in data:
		region = region_data['region']
		for instance in region_data['data']:
			ebs = instance['EBS']
			if not ebs:
				ebs.append({'ebs_type': 'N/A', 'ebs_size': 0})
			for i in ebs:
				csv = csv + '\n' + str(region) + '\t' + str(instance['Instance_name']) + '\t' + str(instance['Instance_ID']) + '\t' + str(instance['Instance_type']) + '\t' + str(i['ebs_type']) + '\t' + str(i['ebs_size'])
				if not '(Attached EBS)' in instance['Instance_name']:
					instance['Instance_name'] = instance['Instance_name'] + '(Attached EBS)'
				instance['Instance_ID'] = ''
				instance['Instance_type'] = ''
	return csv

def compare(today, yesterday):
	changes = list()
	for yesterday_region_data in yesterday:
		region = yesterday_region_data['region']
		for today_region_data in today:
			if region == today_region_data['region']:
				yesterday_data = set([str(instance) for instance in yesterday_region_data['data']])
				today_data = set([str(instance) for instance in today_region_data['data']])
				data = [json.loads(re.sub("'", '"', terminated_instance)) for terminated_instance in list(yesterday_data - today_data)] + [json.loads(re.sub("'", '"', launched_instance)) for launched_instance in list(today_data - yesterday_data)]
				if data:
					changes.append({'region': region, 'data': data})
	return changes

def ct(changes):
	yesterday = datetime.date.today() - datetime.timedelta(days=1)
	events = list()
	for change in changes:
		region = change['region']
		trail = boto3.client('cloudtrail', region_name=region)
		for instance in [instance['Instance_ID'] for instance in change['data']]:
			for event in trail.lookup_events(LookupAttributes=[{'AttributeKey': 'ResourceName', 'AttributeValue': instance}], StartTime=datetime.datetime(yesterday.year, yesterday.month, yesterday.day))['Events']:
				events.append({'Event': event['EventName'], 'Time': event['EventTime'], 'User': event.get('Username'), 'Resource': instance})
	return events

def create_body(body, events, data):
	for event in events:
		flag = False
		for region in data:
			for instance in region['data']:
				if instance['Instance_ID'] == event['Resource']:
					body = body + '\n' + event['Event'] + '\t' + str(event['Time']) + '\t' + event['User'] + '\t' + event['Resource'] + '\t' + instance['Instance_type'] + '\t' + str(instance['EBS'])
					flag = True
					break
			if flag:
				break
	return body

def lambda_handler(event, context):
	regions = [region['RegionName'] for region in ec2.describe_regions()['Regions']]
	plist = list()
	output = list()
	for region in regions:
		pipe_out, pipe_in = Pipe(False)
		process = Process(target=each_region, args=(region, pipe_in))
		process.start()
		plist.append(process)
		output.append({'region': region, 'data':pipe_out})
	for proc in plist:
		proc.join()
	data = list()
	for i in output:
		j = i['data'].recv()
		if j:
			data.append({'region': i['region'], 'data': j})
	csv = create_csv(data)
	s3.Object(bucket, output_path + 'ec2_instances.json').put(Body=str(data))
	s3.Object(bucket, output_path + 'ec2_instances.csv').put(Body=csv)
	try:
		last_data = json.loads(re.sub("'", '"', s3.Object(bucket, yesterday + 'ec2_instances.json').get()['Body'].read().decode('utf-8')))
	except:
		return 1
	events = ct(compare(data, last_data))
	if events:
		body = 'Event\tTime\tUser\tInstance\tInstance type\tEBS'
		body = create_body(body, events, data)
		s3.Object(bucket, output_path + 'ec2_transactions.csv').put(Body=body)
		boto3.client('sns').publish(TopicArn=topic_arn, Message=body, Subject='Instance transaction notifier ' + datetime.datetime.strftime(datetime.date.today(), '%Y/%m/%d'))
		return body
	return 0

lambda_handler(None, None)