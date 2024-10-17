#!/usr/bin/env python3
import aws_cdk as cdk
import constants
from stacks.eks_discovery import EKSDiscovery
from stacks.eks_health import EKSHealth

app = cdk.App()

# Deploy EKS Discovery Lambda to central tooling account
# Function performs discovery of EKS cluster across entire AWS Organization
EKSDiscovery(
    app,
    "eks-discovery-lambda",
    lambda_execution_role_name=constants.LAMBDA_EXECUTION_ROLE_NAME,
    cross_account_role_name=constants.DISCOVERY_CROSS_ACCOUNT_ROLE_NAME,
)

# Forward AWS Health events for EKS to SQS and SNS via an Event Bus
EKSHealth(
    app,
    "eks-health-events",
    event_bus_name=constants.CENTRAL_EVENT_BUS_NAME,
    topic_name=constants.SNS_TOPIC_NAME,
)

app.synth()
