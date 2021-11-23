import boto3
from multiprocessing import Process, Pipe
from time import sleep
ec2 = boto3.client('ec2')

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

if __name__ == "__main__":
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
    print(data)