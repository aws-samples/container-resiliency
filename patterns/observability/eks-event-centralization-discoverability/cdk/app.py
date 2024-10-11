#!/usr/bin/env python3
import os
import boto3
import aws_cdk as cdk
from eks_discovery_stack_set import EKSDiscoveryStackSet

# List of AWS Organization roots
client = boto3.client('organizations')
paginator = client.get_paginator('list_roots')
page_iterator = paginator.paginate()
organization_root_ids = []
for page in page_iterator:
    for root in page['Roots']:
        organization_root_ids.append(root['Id'])

app = cdk.App()

stack_set_creator_stack = EKSDiscoveryStackSet(
    app,
    "EKSDiscoveryStackSet",
    organization_root_ids=organization_root_ids,
    lambda_execution_role_arn="arn:aws:iam::241533131964:role/service-role/foofunc-role-1sqggmkn"
)

app.synth()
