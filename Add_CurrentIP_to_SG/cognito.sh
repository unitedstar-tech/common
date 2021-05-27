#!/bin/bash
export LANG=C
ID=$1
Pass=$2
UserPoolId=ap-northeast-1_OzULknGCT
ClientId=23phd55fe9h61f21bgk7qlik7c
API_Gateway=https://1li6epuzq0.execute-api.ap-northeast-1.amazonaws.com/test
token=`aws cognito-idp admin-initiate-auth --user-pool-id $UserPoolId --client-id $ClientId --auth-flow ADMIN_NO_SRP_AUTH --auth-parameters USERNAME=$ID,PASSWORD=$Pass --query "AuthenticationResult.IdToken"`
curl -H "Authorization:$token" $API_Gateway
