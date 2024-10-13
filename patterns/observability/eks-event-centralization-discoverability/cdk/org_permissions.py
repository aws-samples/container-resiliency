#!/usr/bin/env python3
import os
import boto3
import aws_cdk as cdk
from stacks.stack_set import StackSet
from stacks.eks_discovery import EKSDiscovery

# Name of cross account role  that will be deployed across 
# AWS Organization and be assumed by the Lambda function
CROSS_ACCOUNT_ROLE_NAME = "eks-discovery-cross-account-role"
LAMBDA_EXECUTION_ROLE_NAME = "eks-discovery-lambda-execution-role"

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
stack_set = StackSet(
    app,
    "EKSDiscoveryStackSet",
    organization_root_ids = organization_root_ids,
    lambda_execution_role_arn = app.node.try_get_context("LambdaExecutionRoleArn"),
    cross_account_role_name = CROSS_ACCOUNT_ROLE_NAME
)

app.synth()
