import boto3
import json
import io
import zipfile
import csv
from collections import defaultdict
from datetime import datetime
import os

def lambda_handler(event, context):
    # Initialize AWS clients
    sts_client = boto3.client('sts')
    organizations = boto3.client('organizations')
    s3_client = boto3.client('s3')
    sns_client = boto3.client('sns')
    ec2_client = boto3.client('ec2')

    # Get environment variables
    sns_topic_arn = os.environ['SNS_TOPIC_ARN']
    s3_bucket_name = os.environ['S3_BUCKET_NAME']

    cluster_info = []
    version_counts = defaultdict(int)

    # Get current account ID and list of all AWS regions
    current_account_id = sts_client.get_caller_identity()['Account']
    all_regions = [region['RegionName'] for region in ec2_client.describe_regions()['Regions']]

    # List all accounts in the organization
    accounts = organizations.list_accounts()

    # Iterate through all accounts
    for account in accounts['Accounts']:
        if account['Id'] == current_account_id:
            session = boto3.Session()
        else:
            # Assume role in other accounts
            try:
                assumed_role_object = sts_client.assume_role(
                    RoleArn=f"arn:aws:iam::{account['Id']}:role/OrganizationAccountAccessRole",
                    RoleSessionName="AssumeRoleSession1"
                )
                credentials = assumed_role_object['Credentials']
                session = boto3.Session(
                    aws_access_key_id=credentials['AccessKeyId'],
                    aws_secret_access_key=credentials['SecretAccessKey'],
                    aws_session_token=credentials['SessionToken']
                )
            except Exception as e:
                print(f"Error assuming role in account {account['Id']}: {str(e)}")
                continue

        # Iterate through all regions
        for region in all_regions:
            try:
                eks = session.client('eks', region_name=region)
                clusters = eks.list_clusters()
                # Collect information for each EKS cluster
                for cluster_name in clusters['clusters']:
                    cluster_details = eks.describe_cluster(name=cluster_name)['cluster']
                    cluster_version = cluster_details['version']
                    cluster_arn = cluster_details['arn']
                    tags = eks.list_tags_for_resource(resourceArn=cluster_arn).get('tags', {})
                    cluster_info.append({
                        'accountId': account['Id'],
                        'accountName': account['Name'],
                        'region': region,
                        'clusterName': cluster_name,
                        'clusterArn': cluster_arn,
                        'clusterVersion': cluster_version,
                        'tags': json.dumps(tags)
                    })
                    version_counts[cluster_version] += 1
            except Exception as e:
                print(f"Error processing region {region} in account {account['Id']}: {str(e)}")

    if not cluster_info:
        message = "No EKS clusters found."
    else:
        # Prepare CSV data for cluster details and version counts
        cluster_details_csv = io.StringIO()
        cluster_details_writer = csv.DictWriter(cluster_details_csv, fieldnames=cluster_info[0].keys())
        cluster_details_writer.writeheader()
        cluster_details_writer.writerows(cluster_info)

        version_counts_csv = io.StringIO()
        version_counts_writer = csv.writer(version_counts_csv)
        version_counts_writer.writerow(['clusterVersion', 'count'])
        for version, count in version_counts.items():
            version_counts_writer.writerow([version, count])

        # Create a zip file with both CSVs
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, mode='w') as zip_file:
            zip_file.writestr('cluster_details.csv', cluster_details_csv.getvalue())
            zip_file.writestr('version_counts.csv', version_counts_csv.getvalue())
        zip_buffer.seek(0)

        # Upload zip file to S3
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        s3_key = f'cluster_info_all_accounts_{timestamp}.zip'
        s3_client.put_object(
            Bucket=s3_bucket_name,
            Key=s3_key,
            Body=zip_buffer.getvalue()
        )

        # Send SNS notification
        s3_object_url = f"https://{s3_bucket_name}.s3.amazonaws.com/{s3_key}"
        sns_client.publish(
            TopicArn=sns_topic_arn,
            Subject='Amazon EKS Cluster Information Notification - All Accounts',
            Message=f'Please find the cluster information for all accounts at: {s3_object_url}'
        )

    return {
        'statusCode': 200,
        'body': json.dumps('EKS cluster discovery completed successfully for all accounts!')
    }

