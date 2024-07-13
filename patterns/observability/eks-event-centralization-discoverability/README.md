<h1>EKS Event Centralization and Discoverability</h1>

<p>This repository contains four AWS CloudFormation templates that set up a centralized event management system for Amazon EKS clusters across multiple AWS accounts. The templates should be deployed in the following order:</p>

<ol>
  <li>CentralEKSEventsSQS.yaml</li>
  <li>CentralEKSEventsSNS.yaml</li>
  <li>ForwardEventsToCentral.yaml</li>
  <li>Discoverability.yaml</li>
</ol>

<h2>Prerequisites</h2>

<ul>
  <li>Access to the AWS Management Console with appropriate permissions</li>
  <li>Multiple AWS accounts set up (one central account and one or more member accounts)</li>
  <li>Amazon EKS clusters deployed in member accounts</li>
</ul>

<h2>Deployment Instructions</h2>

<h3>1. Deploy CentralEKSEventsSQS.yaml</h3>

<p>This template creates an SQS queue in the central account to receive EKS events from member accounts.</p>

<ol>
  <li>Sign in to the AWS Management Console in your central account</li>
  <li>Navigate to the CloudFormation service</li>
  <li>Click "Create stack" and choose "With new resources (standard)"</li>
  <li>Select "Upload a template file" and upload the <code>CentralEKSEventsSQS.yaml</code> file</li>
  <li>Click "Next"</li>
  <li>Enter a stack name (e.g., "central-eks-events-sqs")</li>
  <li>Click "Next" on the following pages, reviewing the options</li>
  <li>On the final page, acknowledge that CloudFormation might create IAM resources</li>
  <li>Click "Create stack"</li>
</ol>

<p>After deployment, go to the "Outputs" tab of the stack and note the SQS queue ARN.</p>

<h3>2. Deploy CentralEKSEventsSNS.yaml</h3>

<p>This template sets up an SNS topic in the central account to fan out EKS events to multiple subscribers.</p>

<ol>
  <li>In the central account, create a new CloudFormation stack</li>
  <li>Upload the <code>CentralEKSEventsSNS.yaml</code> file</li>
  <li>Enter a stack name (e.g., "central-eks-events-sns")</li>
  <li>In the "Parameters" section, paste the SQS queue ARN from step 1 into the "SQSQueueARN" field</li>
  <li>Complete the stack creation process, acknowledging IAM resource creation</li>
</ol>

<p>After deployment, note the SNS topic ARN from the stack outputs.</p>

<h3>3. Deploy ForwardEventsToCentral.yaml</h3>

<p>This template should be deployed in each member account to forward EKS events to the central account's SNS topic.</p>

<ol>
  <li>Sign in to the AWS Management Console in a member account</li>
  <li>Create a new CloudFormation stack and upload the <code>ForwardEventsToCentral.yaml</code> file</li>
  <li>Enter a stack name (e.g., "forward-eks-events-to-central")</li>
  <li>In the "Parameters" section:
    <ul>
      <li>Enter the central account ID in the "CentralAccountId" field</li>
      <li>Paste the SNS topic ARN from step 2 into the "CentralSNSTopicARN" field</li>
    </ul>
  </li>
  <li>Complete the stack creation process, acknowledging IAM resource creation</li>
</ol>

<p>Repeat this step for each member account.</p>

<h3>4. Deploy Discoverability.yaml</h3>

<p>This template enhances the discoverability of EKS clusters by creating SSM parameters with cluster information.</p>

<ol>
  <li>In each member account, create a new CloudFormation stack</li>
  <li>Upload the <code>Discoverability.yaml</code> file</li>
  <li>Enter a stack name (e.g., "eks-discoverability")</li>
  <li>Complete the stack creation process, acknowledging IAM resource creation</li>
</ol>

<h2>Template Details</h2>

<h3>CentralEKSEventsSQS.yaml</h3>

<ul>
  <li>Creates an SQS queue in the central account</li>
  <li>Sets up necessary IAM roles and policies</li>
</ul>

<h3>CentralEKSEventsSNS.yaml</h3>

<ul>
  <li>Creates an SNS topic in the central account</li>
  <li>Configures the SNS topic to forward messages to the SQS queue</li>
  <li>Sets up IAM roles for cross-account access</li>
</ul>

<h3>ForwardEventsToCentral.yaml</h3>

<ul>
  <li>Creates an EventBridge rule to capture EKS events</li>
  <li>Sets up IAM roles for forwarding events to the central SNS topic</li>
</ul>

<h3>Discoverability.yaml</h3>

<ul>
  <li>Creates SSM parameters with EKS cluster information</li>
  <li>Enhances cluster discoverability across the organization</li>
</ul>

<h2>Post-Deployment</h2>

<p>After deploying all templates:</p>

<ol>
  <li>Verify that EKS events are being forwarded from member accounts to the central account's SNS topic and SQS queue.</li>
  <li>Check the SSM parameters in the member accounts for EKS cluster information.</li>
  <li>Set up additional subscribers to the central SNS topic as needed (e.g., Lambda functions, email notifications).</li>
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
