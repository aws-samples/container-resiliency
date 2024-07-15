<h1>EKS Event Centralization and Discoverability</h1>

<p>This repository contains four AWS CloudFormation templates that set up a centralized event management system for Amazon EKS clusters across multiple AWS accounts. The templates should be deployed in the following order:</p>

<ol>
  <li>CentralEKSEventsSQS.yaml</li>
  <li>CentralEKSEventsSNS.yaml</li>
  <li>ForwardEventsToCentral.yaml</li>
  <li>Discoverability.yaml</li>
</ol>

<h2>Deployment Instructions</h2>

<h3>1. Deploy CentralEKSEventsSQS.yaml</h3>

<p>This CloudFormation template creates an SQS queue and an EventBridge rule to monitor AWS EKS health events. It configures the rule to capture planned lifecycle events for EKS and sends messages to the SQS queue. The template also sets up necessary permissions and outputs the SQS queue URL and ARN.</p>

<ol>
  <li>Sign in to the AWS Management Console</li>
  <li>Navigate to the CloudFormation service</li>
  <li>Click "Create stack"</li>
  <li>Select "Upload a template file" and upload the <code>CentralEKSEventsSQS.yaml</code> file</li>
  <li>Click "Next"</li>
  <li>Enter a stack name (e.g., "central-eks-events-sqs")</li>
  <li>Click "Next" on the following pages, reviewing the options</li>
  <li>Click "Submit"</li>
</ol>

<h3>2. Deploy CentralEKSEventsSNS.yaml</h3>

<p>This CloudFormation template creates an SNS topic and an EventBridge rule to monitor AWS EKS health events. It sets up the rule to capture planned lifecycle events for EKS and sends notifications to the SNS topic. The template also includes necessary permissions and outputs the SNS topic ARN.</p>

<ol>
  <li>Sign in to the AWS Management Console</li>
  <li>Navigate to the CloudFormation service</li>
  <li>Click "Create stack"</li>
  <li>Select "Upload a template file" and upload the <code>CentralEKSEventsSNS.yaml</code> file</li>
  <li>Enter a stack name (e.g., "central-eks-events-sns")</li>
  <li>Click "Next" on the following pages, reviewing the options</li>
  <li>Click "Submit"</li>
</ol>

<h3>3. Deploy ForwardEventsToCentral.yaml</h3>

<p>This CloudFormation template creates an EventBridge rule to capture AWS EKS health events and forward them to another EventBridge bus. It sets up an IAM role for cross-account access, configures the rule to match specific EKS planned lifecycle events, and defines the target as the specified EventBridge bus. The template outputs the ARNs of the created rule and IAM role. <strong>Note: This template should be deployed in every AWS region where EKS event capture is desired.</strong></p>

<ol>
  <li>Sign in to the AWS Management Console</li>
  <li>Navigate to the CloudFormation service</li>
  <li>Click "Create stack"</li>
  <li>Select "Upload a template file" and upload the <code>ForwardEventsToCentral.yaml</code> file</li>
  <li>Enter a stack name (e.g., "forward-eks-events-to-central")</li>
  <li>In the "Parameters" section:
    <ul>
      <li>Enter the TargetEventBusArn from the central account</li>
    </ul>
  </li>
  <li>Complete the stack creation process, acknowledging IAM resource creation</li>
</ol>

<p>Repeat this step in each region where EKS event capture is desired.</p>

<h3>4. Deploy Discoverability.yaml</h3>

<p>This CloudFormation template sets up an EKS cluster discovery solution for multi-account environments. It creates a Lambda function to discover EKS clusters across all accounts and regions, an S3 bucket to store results, an SNS topic for notifications, and an EventBridge scheduler for weekly execution. The Lambda function collects cluster details, generates reports, and sends notifications. IAM roles and policies are also defined to manage necessary permissions.</p>

<ol>
  <li>Sign in to the AWS Management Console</li>
  <li>Navigate to the CloudFormation service</li>
  <li>Click "Create stack"</li>
  <li>Select "Upload a template file" and upload the <code>Discoverability.yaml</code> file</li>
  <li>Enter a stack name (e.g., "eks-discoverability")</li>
  <li>Click "Next" on the following pages, reviewing the options</li>
  <li>Complete the stack creation process, acknowledging IAM resource creation</li>
</ol>

<h2>Troubleshooting</h2>

<ul>
  <li>Ensure that all IAM roles and policies are correctly set up and have the necessary permissions.</li>
  <li>Check CloudWatch Logs for any error messages in the Lambda functions or EventBridge rules.</li>
  <li>Verify that the account IDs and ARNs used in the templates are correct.</li>
</ul>

<h2>Security Considerations</h2>

<ul>
  <li>Review and adjust the IAM roles and policies to adhere to the principle of least privilege.</li>
  <li>Encrypt the SQS queue and SNS topic using AWS KMS for added security.</li>
  <li>Regularly audit the access to the centralized event management system.</li>
</ul>

<p>For any issues or questions, please open an issue in this repository.</p>
