#!/usr/bin/env python3
import os
import boto3
import aws_cdk as cdk
from stacks.stack_set_stack import StackSetStack

# Name of cross account role  that will be deployed across 
# AWS Organization and be assumed by the Lambda function
DISCOVERY_CROSS_ACCOUNT_ROLE_NAME = "eks-discovery-cross-account-role"
HEALTH_CROSS_ACCOUNT_ROLE_NAME = "health-cross-account-role"

# Get AWS Organization root IDs
client = boto3.client('organizations')
paginator = client.get_paginator('list_roots')
page_iterator = paginator.paginate()
organization_root_ids = []
for page in page_iterator:
    for root in page['Roots']:
        organization_root_ids.append(root['Id'])

app = cdk.App()

# Deploy StackSet to distribute cross account role 
stack_set = StackSetStack(
    app,
    "EKSDiscoveryCdkStackSetStack",
    organization_root_ids = organization_root_ids,
    discovery_cross_account_role_name = DISCOVERY_CROSS_ACCOUNT_ROLE_NAME,
    health_cross_account_role_name = HEALTH_CROSS_ACCOUNT_ROLE_NAME,
    lambda_execution_role_arn = app.node.try_get_context("LambdaExecutionRoleArn"),
    central_event_bus_arn = app.node.try_get_context("CentralEventBusArn")        
)

app.synth()
