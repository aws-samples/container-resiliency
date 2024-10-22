# Enhancing EKS Cluster Observability: End of Support Notifications and Discoverability

## Introduction

In the rapidly evolving world of containerized applications, maintaining resilience and observability across Kubernetes environments has become a critical challenge. As organizations increasingly adopt [Amazon Elastic Kubernetes Service](https://aws.amazon.com/eks/) (EKS) to manage their containerized workloads, the need for cluster version lifecycle management and discovery mechanisms becomes paramount. As Amazon EKS environments grow more complex and span multiple accounts and regions, customers often struggle to track cluster versions, support lifecycles, and overall deployment status.

Proactive monitoring of EKS cluster lifecycles and end of support is crucial to ensuring the security, stability, and compliance of Kubernetes deployments. Furthermore, gaining visibility into EKS cluster deployments across an entire AWS Organization is essential for effective resource management, strategic planning, and maintaining an accurate inventory.

To address these pain points, we share two robust solutions that provide observability of Amazon EKS clusters:

1. End of Support Notifications
2. Discovery and Reporting

The first solution leverages AWS Health, Amazon EventBridge, and Amazon SNS/SQS to monitor EKS-specific events, particularly for clusters approaching end of support (standard and extended). By delivering early notifications when an EKS cluster is nearing the end of its support window, this solution empowers you to proactively plan and update your clusters’ Kubernetes version.

Complementing this, the second solution is an automated discovery and reporting mechanism that identifies and aggregates detailed information about EKS clusters across all AWS accounts and regions within your AWS Organization. This comprehensive visibility into cluster versions, associated tags, and other key details facilitates compliance checks, accurate resource inventory management, and strategic upgrade planning. 

Together, these two solutions provide a robust framework for effective EKS cluster lifecycle management, enabling organizations to stay ahead of potential issues, optimize resource utilization, and make informed decisions that align with their long-term strategic goals.

## Prerequisites

You need the following to complete the walkthrough:

* An [AWS account](https://aws.amazon.com/console/) with [AWS Organizations](https://aws.amazon.com/organizations/) enabled
* Business, Enterprise On-Ramp, or Enterprise Support plan from [AWS Support](https://aws.amazon.com/premiumsupport/) to use the AWS Health API
* Basic knowledge of [Amazon EKS](https://aws.amazon.com/eks/), [AWS Health](https://aws.amazon.com/premiumsupport/technology/aws-health/), [Amazon EventBridge](https://aws.amazon.com/eventbridge/), [AWS Lambda](https://aws.amazon.com/lambda/), [AWS IAM](https://aws.amazon.com/iam/), [Amazon S3](https://aws.amazon.com/pm/serv-s3/), [Amazon SNS](https://aws.amazon.com/sns/), [Amazon SQS](https://aws.amazon.com/sqs/) and [AWS Cloud Development Kit (CDK)](https://aws.amazon.com/cdk/)
* Ability to delegate permissions from management to a tooling account that will be used to centralize notifications and perform EKS cluster discovery across the entire Organization
* Knowledge of Python

## Intial Setup

### Enable AWS Health Organizational View within the management account **

You must [enable Organizational View in AWS Health](https://docs.aws.amazon.com/health/latest/ug/enable-organizational-view-in-health-console.html?icmpid=docs_awshealth_console) to obtain a centralized, aggregated view of AWS Health events across your entire AWS organization.  You can verify that this is enabled through the console or by running the following command using the AWS CLI:  `aws health describe-health-service-status-for-organization` .  You should see `{ "healthServiceAccessStatusForOrganization": "ENABLED" }`.

A Business, Enterprise On-Ramp, or Enterprise Support plan from AWS Support is required to use the AWS Health API and to complete this step.

### Delegate administration from management account to a central tooling account

Setup an AWS account within the Organization to be the tooling account for this solution. This account will be used to centralize notifications and discovery.

From the management account delegate CloudFormation StackSets administration following the steps described in this blog: [CloudFormation StackSets delegated administration](https://aws.amazon.com/blogs/mt/cloudformation-stacksets-delegated-administration/)

The same result can also be achieved by running the following command from the management account. Replace `012345678901` with the AWS account ID of your tooling account.

```bash
aws organizations register-delegated-administrator \
  --service-principal=member.org.stacksets.cloudformation.amazonaws.com \
  --account-id="012345678901"
```

This is the only time we need to access the management account. The remaining steps descibed are completed from within the tooling account.

#### Bootstrap AWS Cloud Development Kit (CDK)

Select a primary AWS region where all the reporting and events will be consolidated within the central tooling account. Set the `AWS_DEFAULT_REGION` variable to this primary AWS region.

For the Discovery and Reporting solution, you must then bootstrap CDK in this primary region across the entire AWS Organization. Additionally, CDK must also bootstrapped in all regions where EKS clusters are deployed to received End of Support Notifications. To simplify this walkthrough we will be be demonstrating deployment of the resources to just the primary region you have selected.

Steps to bootstrap CDK across multiple accounts and regions are available in this blog: [Bootstrapping multiple AWS accounts for AWS CDK using CloudFormation StackSets](https://aws.amazon.com/blogs/mt/bootstrapping-multiple-aws-accounts-for-aws-cdk-using-cloudformation-stacksets/).

#### Download the CDK stacks

We provide CDK stacks for you to quickly deploy the solution in your environment. Simply download code from our GitHub repository: https://github.com/aws-samples/container-resiliency/tree/main/patterns/observability/eks-event-centralization-discoverability and setup the environment by running the following commands within the `cdk` directory.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Walkthrough

### Solution 1: EKS Cluster End of Support Notifications

Our first solution addresses the critical need for timely awareness of EKS cluster lifecycle events, particularly the approach of end-of-standard-support dates. By leveraging AWS Health, Amazon EventBridge and Amazon SNS and SQS (optional), we've created a centralized system that:

* Monitors AWS Health events across multiple regions and accounts
* Focuses on EKS-specific events, specifically the AWS_EKS_PLANNED_LIFECYCLE_EVENT
* Provides early notifications when an EKS cluster is 180 days away from reaching the end of standard and extended support

This centralized approach ensures that EKS customers receive sufficient time to plan and execute version upgrades, maintaining the security and stability of their Kubernetes environments.

#### Step 1: Deploy the eks-health-events CDK stack

Deploy the `eks-health-events` CDK stack to the central tooling account using the following command:

```bash
cdk deploy eks-health-events --require-approval never 
```

This deploys the CDK app in `tooling_account.py`, which provisions the following resources in the central tooling account:

* Event bus 
* SNS topic and SQS queue to monitor events
* EventBridge rule to forward planned lifecycle events for EKS to SNS
* EventBridge rule to forward monitor planned lifecycle events for EKS to SQS
* Resource policies for the event rules to publish to SNS and SQS

#### Step 2: Deploy the eks-health-events CDK stack

Deploy the `eks-health-events-stack-set` CDK stack.

```bash
 cdk deploy --app "python stack_sets.py" eks-health-events-stack-set --require-approval never
 ```

This uses CloudFormation StackSets to deploy the following resources to the chosen primary region across all the accounts in the AWS Organization besides the Management account:

* Local event bus
* EventBridge rule to forward planned lifecycle events for EKS to the central event bus that was provisioned in Step 2 above
* Resource policies for the event rules to publish to the central event bus

#### Step 3: Configure SNS notifications

Browse to the SNS service named `eks-health-events-EKSHealthEvents-<primary region>` and create a subscription to the newly created topic (e.g. a group email address).

#### Step 4: Validate the solution

You can inspect and validate the EventBridge rules, SQS queue and SNS topic were created by the CloudFormation stacks named `eks-health-events` and `eks-health-events-stack-set`. From this point on as your EKS clusters are 180 days away from reaching the end of support (standard and extended), the EventBridge rules will apply and SNS and/or SQS will be triggered.

### Solution 2: EKS Cluster Discovery and Reporting

Complementing the EKS Cluster End of Support Notifications solution, our second solution offers a comprehensive view of EKS clusters across an entire AWS Organization. This solution:

* Identifies EKS clusters in all AWS accounts and regions within an Organization
* Collects information about each cluster, including account details, region, cluster name, version, and associated tags
* Aggregates data on cluster versions, providing insights into version distribution
* Generates both detailed and summary reports, stored centrally for easy access

By providing this organization-wide visibility, the solution enables teams to maintain an accurate inventory of EKS resources, facilitate compliance checks, and support strategic upgrade planning.

#### Step 1: Deploy the eks-discovery CDK stack

Deploy the `eks-discovery-lambda` CDK stack to the central tooling account using the following command:

```bash
cdk deploy eks-discovery-lambda --require-approval never 
```

This deploys the CDK stack named `eks-discovery-lambda` in `tooling_account.py`, which provisions the following resources in the central tooling account:

* Lambda function to discover EKS clusters across all accounts and regions
* S3 bucket to store results
* SNS topic for notifications
* EventBridge scheduler for recurring execution
* Necessary IAM roles and policies

The Lambda function collects cluster details, generates reports, and sends notifications.

#### Step 2: Modify the EventBridge Scheduler as needed

If you would like to customize the EKS cluster discovery schedule, navigate to EventBridge and under schedules you will find the newly created `EKSDiscoveryWeeklySchedule`. Note that this is a cron-based scheduler.

In order to receive notifications from SNS you will want to create a subscription to the topic. To do this, navigate to the SNS service, locate the newly created Topic named `EKSDiscoverySNSTopic` and configure the protocol to meet your requirements (e.g. emailing to a group).

#### Step 3: Deploy cross-account role that Lamdda function can assume to perform discovery

The Lambda function you deployed in Step 1 relies on a cross-account role in each of the accounts within the AWS Organization to perform cluster discovery.

Deploy the `eks-discovery-stack-set` CDK stack that rolls out this cross account role.

```bash
 cdk deploy --app "python stack_sets.py" eks-discovery-stack-set --require-approval never
 ```

#### Step 4: Validate the solution

To validate the solution, navigate to the newly created Lambda function and test with a new event and an empty JSON object. Once the Lambda completes verify that the S3 bucket receives the zip file and confirm that you received an SNS notification.

#### Step 5: (Optional) Monitor the solution

You may optionally want to monitor the solution. This can be done by setting up CloudWatch Alarms to monitor the Lambda function's execution and any potential errors. Additionally, regularly review the generated reports in the S3 bucket and periodically review and update the IAM permissions if needed. And lastly, keep the Lambda function code updated with any new AWS SDK versions or feature additions.

### Troubleshooting

* Ensure that all IAM roles and policies are correctly set up and have the necessary permissions.
* Check CloudWatch Logs for any error messages in the Lambda functions or EventBridge rules.

### Security Considerations

* Review and adjust the IAM roles and policies to adhere to the principle of least privilege and your environment.
* Regularly audit the access to the centralized event management system.

### Cleanup

Run the following commands to clean up the resources provisioned: 

```bash
cdk destroy --app "python stack_sets.py" --all --force
cdk destroy --all --force
```

The first command deletes the CloudFormation StackSets that were deployed throughout the AWS Organization using the CDK App named `stack_sets.py`. The second command cleans up the resources provisioned within the central tooling account using the CDK App named `tooling_account.py`

## Conclusion

By following this guide you can set up a robust system leveraging AWS services to provide proactive end of standard support notifications. This enables timely planning for upgrades, mitigating risks from outdated clusters while maintaining security, stability, and compliance. Additionally, the EKS Cluster Discovery and Reporting solution marks a significant step forward in managing complex, multi-account Kubernetes environments on AWS. The solution enhances visibility, streamlines compliance efforts, facilitates strategic planning, and supports informed decision-making for cluster upgrades and resource allocation.

As organizations continue to scale their containerized applications, these solutions become invaluable assets. They enable teams to maintain a clear overview of their EKS landscape, optimize resource utilization, and ensure consistent management practices across diverse deployments. By implementing these solutions, you have taken a significant step forward in managing the observability, resilience, and governance of your Amazon EKS environments, ensuring the long-term success and scalability of your Kubernetes initiatives on AWS.

As a final call to action, we recommend trying both solutions and begin enhancing your EKS cluster observability today!
