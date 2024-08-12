<h1>EKS Event Centralization and Discoverability</h1>
<h2>Introduction</h2>

<p>In the rapidly evolving landscape of Kubernetes management, maintaining visibility and control over Amazon Elastic Kubernetes Service (EKS) clusters has become a challenge for some organizations. As Amazon EKS environments grow more complex and span multiple accounts and regions, customers often struggle to track cluster versions, support lifecycles, and overall deployment status.</p>

<p>To address these pain points, we share two robust solutions that work in tandem to provide comprehensive observability for Amazon EKS environments:</p>

<ul>
    <li>EKS Lifecycle Management</li>
    <li>EKS Cluster Discovery and Reporting</li>
</ul>

<p>These solutions aim to empower EKS customers with proactive notifications about upcoming end-of-support dates and deliver detailed insights into cluster deployments across their entire AWS organization.</p>

<h2>Prerequisites</h2>

<p>You need the following to complete the walkthrough:</p>

<ul>
    <li>An <a href="https://aws.amazon.com/console/">AWS account</a></li>
    <li>Knowledge of Python</li>
    <li>Basic knowledge of <a href="https://aws.amazon.com/eks/">Amazon EKS</a>, <a href="https://aws.amazon.com/premiumsupport/technology/aws-health/">AWS Health</a>, <a href="https://aws.amazon.com/eventbridge/">Amazon EventBridge</a>, <a href="https://aws.amazon.com/lambda/">AWS Lambda</a>, <a href="https://aws.amazon.com/iam/">AWS IAM</a>, <a href="https://aws.amazon.com/pm/serv-s3/">Amazon S3</a>, <a href="https://aws.amazon.com/sns/">Amazon SNS</a>, <a href="https://aws.amazon.com/sqs/">Amazon SQS</a> and <a href="https://aws.amazon.com/cloudformation/">AWS CloudFormation</a></li>
</ul>

<h2>Solution 1: EKS Lifecycle Management</h2>

<p>Our first solution addresses the critical need for timely awareness of EKS cluster lifecycle events, particularly the approach of end-of-standard-support dates. By leveraging AWS Health, Amazon EventBridge and Amazon SNS (or SQS), we've created a centralized system that:</p>

<ul>
    <li>Monitors AWS Health events across multiple regions and accounts</li>
    <li>Focuses on EKS-specific events, specifically the AWS_EKS_PLANNED_LIFECYCLE_EVENT</li>
    <li>Provides early notifications when an EKS cluster is 180 days away from reaching the end of its standard support and extended support periods</li>
</ul>

<p>This centralized approach ensures that EKS customers receive ample time to plan and execute version upgrades, maintaining the security and stability of their Kubernetes environments.</p>

<img src="./images/AWS EKS Lifecycle Monitoring.drawio.png" alt="Architecture">

<h2>Solution 2: EKS Cluster Discovery and Reporting</h2>

<p>Complementing EKS Lifecycle Management, our second solution offers a comprehensive view of EKS deployments across an entire AWS organization. This automated discovery and reporting tool:</p>

<ul>
    <li>Identifies EKS clusters in all AWS accounts and regions within an organization</li>
    <li>Collects detailed information about each cluster, including account details, region, cluster name, version, and associated tags</li>
    <li>Aggregates data on cluster versions, providing insights into version distribution</li>
    <li>Generates both detailed and summary reports, stored centrally for easy access</li>
</ul>

<p>By providing this organization-wide visibility, the solution enables teams to maintain an accurate inventory of EKS resources, facilitate compliance checks, and support strategic upgrade planning.</p>

<img src="./images/EKS Cluster Discovery and Reporting Solution .drawio.png" alt="Architecture">

<p>In the following sections we'll explore each architecture and deployment steps.</p>

<h2>Walkthrough</h2>

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
  <li>Sign in to the <b>AWS Management Console</b></li>
  <li>Navigate to the <b>CloudFormation service</b></li>
  <li>Click <b>Create stack with new resources</b></li>
  <li>Select <b>Upload a template file</b> and upload the <code>CentralEKSEventsSQS.yaml</code> file</li>
  <li>Click <b>Next</b></li>
  <li>Enter a stack name (e.g., "central-eks-events-sqs")</li>
  <li>Click <b>Next</b> on the following pages, reviewing the options</li>
  <li>Click <b>Submit</b></li>
</ol>

<h3>2. Deploy CentralEKSEventsSNS.yaml</h3>

<p>This CloudFormation template creates an SNS topic and an EventBridge rule to monitor AWS EKS health events. It sets up the rule to capture planned lifecycle events for EKS and sends notifications to the SNS topic. The template also includes necessary permissions and outputs the SNS topic ARN.</p>

<ol>
  <li>Sign in to the <b>AWS Management Console</b></li>
  <li>Navigate to the <b>CloudFormation service</b></li>
  <li>Click <b>Create stack with new resources</b></li>
  <li>Select <b>Upload a template file</b> and upload the <code>CentralEKSEventsSNS.yaml</code> file</li>
  <li>Enter a stack name (e.g., "central-eks-events-sns")</li>
  <li>Click <b>Next</b> on the following pages, reviewing the options</li>
  <li>Click <b>Submit</b></li>
  <li>After creation, create a subscription to the topic (e.g., a group email address).</li>
</ol>

<h3>3. Deploy ForwardEventsToCentral.yaml</h3>

<p>This CloudFormation template creates an EventBridge rule to capture AWS EKS health events and forward them to another EventBridge bus. It sets up an IAM role for cross-account access, configures the rule to match specific EKS planned lifecycle events, and defines the target as the specified EventBridge bus. The template outputs the ARNs of the created rule and IAM role. <strong>Note: This template should be deployed in every AWS region where EKS event capture is desired.</strong></p>

<ol>
  <li>Sign in to the <b>AWS Management Console</b></li>
  <li>Navigate to the <b>CloudFormation service</b></li>
  <li>Click <b>Create stack with new resources</b></li>
  <li>Select <b>Upload a template file</b> and upload the <code>ForwardEventsToCentral.yaml</code> file</li>
  <li>Enter a stack name (e.g., "forward-eks-events-to-central")</li>
  <li>In the <b>Parameters</b> section:
    <ul>
      <li>Enter the TargetEventBusArn from the central region</li>
    </ul>
  </li>
  <li>Complete the stack creation process, acknowledging IAM resource creation</li>
</ol>

<p>Repeat this step in each region where EKS event capture is desired.</p>

<h3>4. Deploy Discoverability.yaml</h3>

<p>This CloudFormation template sets up an EKS cluster discovery solution for multi-account environments. It creates a Lambda function to discover EKS clusters across all accounts and regions, an S3 bucket to store results, an SNS topic for notifications, and an EventBridge scheduler for weekly execution. The Lambda function collects cluster details, generates reports, and sends notifications. IAM roles and policies are also defined to manage necessary permissions.</p>

<ol>
  <li>Sign in to the <b>AWS Management Console</b></li>
  <li>Navigate to the <b>CloudFormation service</b></li>
  <li>Click <b>Create stack with new resources</b></li>
  <li>Select <b>Upload a template file</b> and upload the <code>Discoverability.yaml</code> file</li>
  <li>Enter a stack name (e.g., "eks-discoverability")</li>
  <li>Click <b>Next</b> on the following pages, reviewing the options</li>
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
  <li>Review and adjust the IAM roles and policies to adhere to the principle of least privilege and your environment.</li>
  <li>Encrypt the SQS queue and SNS topic using AWS KMS for added security.</li>
  <li>Regularly audit the access to the centralized event management system.</li>
</ul>

<h2>Clean-up</h2>

<p>To clean up the resources created by these CloudFormation templates and revert to your original state, follow these steps:</p>

<p>Begin by deleting the CloudFormation stacks in the reverse order of their deployment. Start with the <i>Discoverability</i> stack, which will remove the Lambda function, S3 bucket, SNS topic, and associated IAM roles and policies. Next, delete the <i>ForwardEventsToCentral</i> stacks in each region where they were deployed. This will remove the EventBridge rules and IAM roles for cross-account access.</p>

<p>Then, proceed to delete the <i>central-eks-events-sns</i> stack, which will remove the SNS topic and EventBridge rule for monitoring EKS health events. Finally, delete the <i>central-eks-events-sqs</i> stack to remove the SQS queue and its associated EventBridge rule.</p>

<p>After deleting these stacks, review your AWS accounts to ensure all related resources have been properly removed. This may include checking the Lambda console, S3 console, SNS console, SQS console, and IAM console for any lingering resources. Additionally, if you made any modifications to the OrganizationAccountAccessRole in member accounts specifically for this project, consider reverting those changes if they're no longer needed for other purposes.</p>

<p>By following these cleanup steps, you'll effectively remove all resources created by the CloudFormation templates, returning your AWS environment to its previous state.</p>

<p>For any issues or questions, please open an issue in this repository.</p>
