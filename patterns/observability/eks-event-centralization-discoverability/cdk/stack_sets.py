#!/usr/bin/env python3
import os
import boto3
import aws_cdk as cdk
import constants
from stacks.eks_discovery_stack_set import EksDiscoveryStackSet
from stacks.eks_health_stack_set import EksHealthStackSet

region = os.getenv("CDK_DEFAULT_REGION", "us-east-1")
central_account_id = boto3.client("sts").get_caller_identity().get("Account")

# Get AWS Organization root IDs
paginator = boto3.client("organizations").get_paginator("list_roots")
page_iterator = paginator.paginate()
organization_root_ids = []
for page in page_iterator:
    for root in page["Roots"]:
        organization_root_ids.append(root["Id"])

app = cdk.App()

# StackSet to distribute cross account role for EKS Discovery Lambda
lambda_execution_role_arn = (
    f"arn:aws:iam::{central_account_id}:role/{constants.LAMBDA_EXECUTION_ROLE_NAME}"
)
stack_set = EksDiscoveryStackSet(
    app,
    "eks-discovery-stack-set",
    organization_root_ids=organization_root_ids,
    discovery_cross_account_role_name=constants.DISCOVERY_CROSS_ACCOUNT_ROLE_NAME,
    lambda_execution_role_arn=lambda_execution_role_arn,
)

# StackSet to enable Health events from AWS Organization accounts to be forwarded
# to event bus in a central account 
central_event_bus_arn = f"arn:aws:events:{region}:{central_account_id}:event-bus/{constants.CENTRAL_EVENT_BUS_NAME}"
stack_set = EksHealthStackSet(
    app,
    "eks-health-events-stack-set",
    organization_root_ids=organization_root_ids,
    health_cross_account_role_name=constants.HEALTH_CROSS_ACCOUNT_ROLE_NAME,
    central_event_bus_arn=central_event_bus_arn,
)

app.synth()
