import boto3, botocore

ssm = boto3.client("ssm")

def start_execution(instance_id, bucket, role_arn):
    try:
        response = ssm.start_automation_execution(
            DocumentName='AWSSupport-CollectEKSInstanceLogs',
            Parameters={
                'EKSInstanceId': [instance_id],
                'LogDestination': [bucket],
                'AutomationAssumeRole': [role_arn]
            }
        )
    except botocore.exceptions.ClientError as error:
        raise error
    else:
        return response.get('AutomationExecutionId')
