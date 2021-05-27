#!/bin/bash
export LANG=C
export AWS_DEFAULT_OUTPUT=text
ID=$1
Pass=$2
UserPoolId=
ClientId=
API_Gateway=
token=`aws cognito-idp admin-initiate-auth --user-pool-id $UserPoolId --client-id $ClientId --auth-flow ADMIN_NO_SRP_AUTH --auth-parameters USERNAME=$ID,PASSWORD=$Pass --query "AuthenticationResult.IdToken"`
curl -H "Authorization:$token" $API_Gateway
