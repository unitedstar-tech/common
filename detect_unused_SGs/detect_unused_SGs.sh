#!/bin/bash
export LANG=C
export AWS_DEFAULT_OUTPUT=text
export AWS_DEFAULT_REGION=ap-northeast-1

EFSs=(`aws efs describe-file-systems | grep "FILESYSTEMS" | awk '{print $6}'`)
num1=0
num2=0
while [ $num1 -lt ${#EFSs[*]} ]
do
	EFS_mountpoint=(`aws efs describe-mount-targets --file-system-id ${EFSs[$num1]} | awk '{print $7}'`)
	while [ $num2 -lt ${#EFS_mountpoint[*]} ]
	do
		SG=`aws efs describe-mount-target-security-groups --mount-target-id ${EFS_mountpoint[$num2]} | awk '{print $2}'`
		num2=`expr $num2 + 1`
		echo ${EFS_SGs[*]} | grep $SG >/dev/null 2>&1 && continue
		EFS_SGs=($SG ${EFS_SGs[*]})
	done
	num1=`expr $num1 + 1`
done

num1=0
clusters=(`aws ecs list-clusters | awk '{print $2}'`)
while [ $num1 -lt ${#clusters[*]} ]
do
	services=(`aws ecs list-services --cluster ${clusters[$num1]} | awk '{print $2}'` ${services[*]})
	num2=0
	while [ $num2 -lt ${#services[*]} ]
	do
		ECS_SGs=(`aws ecs describe-services --cluster ${clusters[$num1]} --services ${services[$num2]} | grep "SECURITYGROUPS" | sort -u | awk '{print $2}'` ${ECS_SGs[*]})
		num2=`expr $num2 + 1`
	done
	num1=`expr $num1 + 1`
done

Default_SGs=(`aws ec2 describe-security-groups | grep "^\s*SECURITYGROUPS" | grep "default group\|default VPC security group" | sed -e "s/\s\{2,\}/\t/g" | awk -F "\t" '{print $3}' | sort -u`)

SG=(`aws ec2 describe-security-groups --group-ids | grep SECURITYGROUPS | awk -F"\t" '{print $3}' | sort -u`)
for CHECK in ${SG[*]}
do
	echo ${Default_SGs[*]} | grep $CHECK >/dev/null
	if [ $? -eq 0 ]
	then
		continue
	fi
	aws ec2 describe-instances | grep $CHECK >/dev/null
	if [ $? -eq 0 ]
	then
		continue
	fi
	aws elb describe-load-balancers | grep $CHECK >/dev/null
	if [ $? -eq 0 ]
	then
		continue
	fi
	aws elbv2 describe-load-balancers | grep $CHECK >/dev/null
	if [ $? -eq 0 ]
	then
		continue
	fi
	aws rds describe-db-instances | grep $CHECK >/dev/null
	if [ $? -eq 0 ]
	then
		continue
	fi
	aws rds describe-db-clusters | grep $CHECK >/dev/null
	if [ $? -eq 0 ]
	then
		continue
	fi
	aws elasticache describe-cache-clusters | grep $CHECK >/dev/null
	if [ $? -eq 0 ]
	then
		continue
	fi
	aws lambda list-functions | grep $CHECK >/dev/null
	if [ $? -eq 0 ]
	then
		continue
	fi
	echo ${EFS_SGs[*]} | grep $CHECK >/dev/null
	if [ $? -eq 0 ]
	then
		continue
	fi
	echo ${ECS_SGs[*]} | grep $CHECK >/dev/null
	if [ $? -eq 0 ]
	then
		continue
	fi
	echo $CHECK
done
