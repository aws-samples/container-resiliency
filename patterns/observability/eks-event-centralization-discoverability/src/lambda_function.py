import boto3
import json
import io
import zipfile
import csv
from collections import defaultdict
from datetime import datetime
import os
import logging

def lambda_handler(event, context):
    # Setup logging
    logger = logging.getLogger()
    logger.setLevel("INFO")

    # Initialize AWS clients
    sts_client = boto3.client('sts')
    organizations = boto3.client('organizations')
    s3_client = boto3.client('s3')
    sns_client = boto3.client('sns')
    ec2_client = boto3.client('ec2')

    # Get environment variables
    sns_topic_arn = os.environ['SNS_TOPIC_ARN']
    s3_bucket_name = os.environ['S3_BUCKET_NAME']
    cross_account_role_name = os.environ['CROSS_ACCOUNT_ROLE_NAME']

    cluster_info = []
    version_counts = defaultdict(int)

    # Get current account ID and list of all AWS regions
    current_account_id = sts_client.get_caller_identity()['Account']
    all_regions = [region['RegionName'] for region in ec2_client.describe_regions()['Regions']]

    # List all active accounts in the organization 
    accounts = []
    page_iterator = organizations.get_paginator('list_accounts').paginate()
    for page in page_iterator:
        accounts.extend(page['Accounts'])
    active_accounts = [account for account in accounts if account['Status'] == 'ACTIVE']

    # Iterate through all accounts
    account_count = 0
    skipped_count = 0
    for account in active_accounts:
        logger.info (f"Discovering EKS clusters in account {account['Id']}")
        account_count += 1        
        if account['Id'] == current_account_id:
            session = boto3.Session()
        else:
            # Assume role in other active accounts
            try:
                assumed_role_object = sts_client.assume_role(
                    RoleArn=f"arn:aws:iam::{account['Id']}:role/{cross_account_role_name}",
                    RoleSessionName="AssumeRoleSession1"
                )
                credentials = assumed_role_object['Credentials']
                session = boto3.Session(
                    aws_access_key_id=credentials['AccessKeyId'],
                    aws_secret_access_key=credentials['SecretAccessKey'],
                    aws_session_token=credentials['SessionToken']
                )
            except Exception as e:
                skipped_count += 1
                logger.warning(f"Error assuming role in account {account['Id']}")
                logger.warning({str(e)})
                logger.warning(f"This is the expected result if {account['Id']} is a management account and this Lambda function is run from a non-management account")
                continue

        cluster_count = 0
        # Iterate through all regions
        for region in all_regions:
            try:
                eks = session.client('eks', region_name=region)
                clusters = []
                page_iterator = eks.get_paginator('list_clusters').paginate()
                for page in page_iterator:
                    clusters.extend(page['clusters'])
               
                # Collect information for each EKS cluster
                for cluster_name in clusters:
                    cluster_details = eks.describe_cluster(name=cluster_name)['cluster']
                    cluster_version = cluster_details['version']
                    cluster_arn = cluster_details['arn']
                    tags = cluster_details['tags']                                     
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
                    cluster_count += 1
                
            except Exception as e:
                logger.error(f"Error processing region {region} in account {account['Id']}: {str(e)}")

        logger.info (f"EKS cluster(s) in account {account['Id']} = {cluster_count}")

    if not cluster_info:
        logger.info ("No EKS clusters found.")
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
        'body': json.dumps(f"EKS cluster discovery complete. Attempted scan of {account_count} account(s). Skipped {skipped_count} account(s). Found {len(cluster_info)} EKS cluster(s).")
    }

