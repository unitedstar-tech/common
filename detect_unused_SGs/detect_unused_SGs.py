#!/bin/pypy3
import boto3
ec2 = boto3.client('ec2')
elb = boto3.client('elb')
elb2 = boto3.client('elbv2')
rds = boto3.client('rds')
elasticache = boto3.client('elasticache')
ecs = boto3.client('ecs')
def extractor(list_data, key):
    data = list()
    for i in list_data:
        data.append(i.get(key))
    return data

raw_data = ec2.describe_security_groups()
sgs = raw_data['SecurityGroups']
token = raw_data.get('NextToken')
while token:
    raw_data = ec2.describe_security_groups(NextToken=token)
    sgs.append(raw_data['SecurityGroups'])
    token = raw_data.get('NextToken')
sgs = extractor(sgs, 'GroupId')

raw_data = elb.describe_load_balancers()
tmp = raw_data['LoadBalancerDescriptions']
token = raw_data.get('NextMarker')
while token:
    raw_data = tmp.describe_load_balancers(Marker=token)
    tmp.append(raw_data['LoadBalancerDescriptions'])
    token = raw_data.get('NextMarker')
tmp = extractor(tmp, 'SecurityGroups')
elb = list()
for i in tmp:
    for j in i:
        elb.append(tmp)
elb = list(set(elb))

raw_data = elb2.describe_load_balancers()
tmp = raw_data['LoadBalancers']
token = raw_data.get('NextMarker')
while token:
    raw_data = elb2.describe_load_balancers(Marker=token)
    tmp.append(raw_data['LoadBalancers'])
    raw_data.get('NextMarker')
tmp = extractor(tmp, 'SecurityGroups')
elbv2 = list()
for i in tmp:
    if not i:
        continue
    for j in list(i):
        elbv2.append(j)
elbv2 = list(set(elbv2))

raw_data = rds.describe_db_clusters()
tmp = raw_data['DBClusters']
token = raw_data.get('Marker')
while token:
    raw_data = rds.describe_db_clusters(Marker=token)
    tmp.append(raw_data['DBClusters'])
    token = raw_data.get('Marker')
tmp = extractor(tmp, 'VpcSecurityGroups')
rds_cluster = list()
for i in tmp:
    rds_cluster = list(set(rds_cluster + extractor(i, 'VpcSecurityGroupId')))

raw_data = rds.describe_db_instances()
tmp = raw_data['DBInstances']
token = raw_data.get('Marker')
while token:
    raw_data = rds.describe_db_instances(Marker=token)
    tmp.append(raw_data['DBInstances'])
    token = raw_data.get('Marker')
tmp = extractor(tmp, 'VpcSecurityGroups')
rds_instance = list()
for i in tmp:
    rds_instance = list(set(rds_instance + extractor(i, 'VpcSecurityGroupId')))
print(rds_instance)

raw_data = elasticache.describe_cache_clusters()
tmp = raw_data['CacheClusters']
token = raw_data.get('Marker')
while token:
    raw_data = elasticache.describe_cache_clusters(Marker=token)
    tmp.append(raw_data['CacheClusters'])
    token = raw_data.get('Marker')
tmp = extractor(tmp, 'SecurityGroups')
print(tmp)
cache = list()
for i in tmp:
    cache = list(set(cache + extractor(i, 'SecurityGroupId')))
print(cache)

for sg in sgs:
    if ec2.describe_instances(Filters=[{'Name': 'instance.group-id', 'Values': [sg]}])['Reservations']:
        continue
    elif sg in elb:
        continue
    elif sg in elbv2:
        continue
    elif sg in rds_cluster:
        continue
    elif sg in elbv2:
        continue
    elif sg in cache:
        continue
    else:
        print(sg)
