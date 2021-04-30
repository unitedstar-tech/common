#!/bin/bash
export LANG=C
export AWS_DEFAULT_OUTPUT=text
export AWS_DEFAULT_REGION=ap-northeast-1
SG=(`aws ec2 describe-security-groups --group-ids | grep SECURITYGROUPS | awk -F"\t" '{print $3}' | sort -u`)
for CHECK in ${SG[*]}
do
	aws ec2 describe-instances | grep  $CHECK >/dev/null
	if [ $? -eq 0 ]
	then
		continue
	fi
	aws elb describe-load-balancers | grep  $CHECK >/dev/null
	if [ $? -eq 0 ]
	then
		continue
	fi
	aws elbv2 describe-load-balancers | grep  $CHECK >/dev/null
	if [ $? -eq 0 ]
	then
		continue
	fi
	aws rds describe-db-instances | grep  $CHECK >/dev/null
	if [ $? -eq 0 ]
	then
		continue
	fi
	aws rds describe-db-clusters | grep  $CHECK >/dev/null
	if [ $? -eq 0 ]
	then
		continue
	fi
	aws elasticache describe-cache-clusters | grep  $CHECK >/dev/null
	if [ $? -eq 0 ]
	then
		continue
	fi
	echo $CHECK
done
