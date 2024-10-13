#!/usr/bin/env python3
import os
import boto3
import aws_cdk as cdk
from stacks.eks_discovery_stack import EKSDiscoveryStack

# Name of cross account role  that will be deployed across 
# AWS Organization and be assumed by the Lambda function
CROSS_ACCOUNT_ROLE_NAME = "eks-discovery-cross-account-role"
LAMBDA_EXECUTION_ROLE_NAME = "eks-discovery-lambda-execution-role"

app = cdk.App()

# Deploy EKS Discovery Lambda
lambda_stack = EKSDiscoveryStack(
    app,
    "EKSDiscoveryCdkStack",
    lambda_execution_role_name=LAMBDA_EXECUTION_ROLE_NAME,
    cross_account_role_name = CROSS_ACCOUNT_ROLE_NAME
)

app.synth()
