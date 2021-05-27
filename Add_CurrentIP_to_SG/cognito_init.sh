#!/bin/bash
export LANG=C
ID=$1
Pass=$2
UserPoolId=ap-northeast-1_OzULknGCT
ClientId=23phd55fe9h61f21bgk7qlik7c
temp_pass=password
session=`aws cognito-idp admin-initiate-auth --user-pool-id $UserPoolId --client-id $ClientId --auth-flow ADMIN_NO_SRP_AUTH --auth-parameters USERNAME=$ID,PASSWORD=$temp_pass | head -1 | awk '{print $2}'`
aws cognito-idp admin-respond-to-auth-challenge --user-pool-id $UserPoolId --client-id $ClientId --challenge-name NEW_PASSWORD_REQUIRED --challenge-responses NEW_PASSWORD=$Pass,USERNAME=$ID --session "$session"
