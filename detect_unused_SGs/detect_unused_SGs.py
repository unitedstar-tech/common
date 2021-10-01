import boto3
import re
ec2 = boto3.client('ec2')
elb = boto3.client('elb')
elb2 = boto3.client('elbv2')
rds = boto3.client('rds')
elasticache = boto3.client('elasticache')
ecs = boto3.client('ecs')
lmbd = boto3.client('lambda')
efs = boto3.client('efs')
def extractor(list_data, key):
    data = list()
    for i in list_data:
        data.append(i.get(key))
    return data

raw_data = ec2.describe_security_groups()
tmp = raw_data['SecurityGroups']
token = raw_data.get('NextToken')
while token:
    raw_data = ec2.describe_security_groups(NextToken=token)
    tmp.append(raw_data['SecurityGroups'])
    token = raw_data.get('NextToken')
sgs = list()
for sg in tmp:
    if sg['GroupName'] == 'default':
        continue
    sgs.append(sg)
sgs = extractor(sgs, 'GroupId')

raw_data = elb.describe_load_balancers()
tmp = raw_data['LoadBalancerDescriptions']
token = raw_data.get('NextMarker')
while token:
    raw_data = tmp.describe_load_balancers(Marker=token)
    tmp.append(raw_data['LoadBalancerDescriptions'])
    token = raw_data.get('NextMarker')
tmp = extractor(tmp, 'SecurityGroups')
elb_sg = list()
for i in tmp:
    for j in i:
        elb_sg.append(tmp)
elb_sg = list(set(elb_sg))

raw_data = elb2.describe_load_balancers()
tmp = raw_data['LoadBalancers']
token = raw_data.get('NextMarker')
while token:
    raw_data = elb2.describe_load_balancers(Marker=token)
    tmp.append(raw_data['LoadBalancers'])
    raw_data.get('NextMarker')
tmp = extractor(tmp, 'SecurityGroups')
elbv2_sg = list()
for i in tmp:
    if not i:
        continue
    for j in list(i):
        elbv2_sg.append(j)
elbv2_sg = list(set(elbv2_sg))

raw_data = rds.describe_db_clusters()
tmp = raw_data['DBClusters']
token = raw_data.get('Marker')
while token:
    raw_data = rds.describe_db_clusters(Marker=token)
    tmp.append(raw_data['DBClusters'])
    token = raw_data.get('Marker')
tmp = extractor(tmp, 'VpcSecurityGroups')
rds_cluster_sg = list()
for i in tmp:
    rds_cluster_sg = list(set(rds_cluster_sg + extractor(i, 'VpcSecurityGroupId')))

raw_data = rds.describe_db_instances()
tmp = raw_data['DBInstances']
token = raw_data.get('Marker')
while token:
    raw_data = rds.describe_db_instances(Marker=token)
    tmp.append(raw_data['DBInstances'])
    token = raw_data.get('Marker')
tmp = extractor(tmp, 'VpcSecurityGroups')
rds_instance_sg = list()
for i in tmp:
    rds_instance_sg = list(set(rds_instance_sg + extractor(i, 'VpcSecurityGroupId')))

raw_data = elasticache.describe_cache_clusters()
tmp = raw_data['CacheClusters']
token = raw_data.get('Marker')
while token:
    raw_data = elasticache.describe_cache_clusters(Marker=token)
    tmp.append(raw_data['CacheClusters'])
    token = raw_data.get('Marker')
tmp = extractor(tmp, 'SecurityGroups')
elasticache_sg = list()
for i in tmp:
    elasticache_sg = list(set(elasticache_sg + extractor(i, 'SecurityGroupId')))

raw_data = ecs.list_clusters()
clusters = raw_data['clusterArns']
token = raw_data.get('nextToken')
while token:
    raw_data = ecs.list_clusters(nextToken=token)
    clusters.append(raw_data['clusterArns'])
    token = raw_data.get('nextToken')
def ecs_services(cluster):
    raw_data = ecs.list_services(cluster=cluster)
    services = raw_data['serviceArns']
    token = raw_data.get('nextToken')
    while token:
        raw_data = ecs.list_services(cluster=cluster, nextToken=token)
        services.append(raw_data['serviceArns'])
        token = raw_data.get('nextToken')
    items = len(services)
    num = 0
    raw_data = list()
    while num < items:
        max = num + 10
        if max >= items:
            max = items
        raw_data.append(ecs.describe_services(cluster=cluster, services=services[num:max])['services'])
        num += 10
    sgs = list()
    for service in raw_data:
        network = extractor(service, 'networkConfiguration')
        for i in network:
            if not i:
                continue
            sgs = list(set(sgs + i['awsvpcConfiguration'].get('securityGroups')))
    return sgs
ecs_sg = list()
for cluster in clusters:
    ecs_sg = list(set(ecs_sg + ecs_services(cluster)))

raw_data = lmbd.list_functions()
functions = raw_data['Functions']
token = raw_data.get('NextMarker')
while token:
    raw_data = lmbd.list_functions(Marker=token)
    functions.append(raw_data['Functions'])
    token = raw_data.get('NextMarker')
functions = extractor(functions, 'FunctionArn')
lambda_sg = list()
for function in functions:
    tmp = lmbd.get_function(FunctionName=function)['Configuration'].get('VpcConfig')
    if tmp:
        lambda_sg = list(set(lambda_sg + tmp.get('SecurityGroupIds')))

raw_data = efs.describe_file_systems()
fs = raw_data['FileSystems']
token = raw_data.get('Marker')
while token:
    raw_data = efs.describe_file_systems(Marker=token)
    fs.append(raw_data['FileSystems'])
    token = raw_data.get('Marker')
fs = extractor(fs, 'FileSystemId')
efs_sg = list()
for i in fs:
    fsmt = efs.describe_mount_targets(FileSystemId=i)['MountTargets']
    fsmt = extractor(fsmt, 'MountTargetId')
    for fsmt_id in fsmt:
        efs_sg = efs_sg + efs.describe_mount_target_security_groups(MountTargetId=fsmt_id)['SecurityGroups']

used_sg = list(set(elb_sg + elbv2_sg + rds_cluster_sg + rds_instance_sg + elasticache_sg + ecs_sg + lambda_sg + efs_sg))

for sg in sgs:
    if ec2.describe_instances(Filters=[{'Name': 'instance.group-id', 'Values': [sg]}])['Reservations']:
        continue
    elif sg in used_sg:
        continue
    else:
        print(sg)
