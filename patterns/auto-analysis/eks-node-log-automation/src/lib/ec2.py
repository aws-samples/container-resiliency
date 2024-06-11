import boto3, botocore

ec2 = boto3.client("ec2")

def get_instances(node_list):
    try:
        response = ec2.describe_instances(
            Filters=[
                {
                    'Name': 'private-dns-name',
                    'Values': node_list
                }
            ]
        )
        instances = list()
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                instances.append(instance['InstanceId'])
    except botocore.exceptions.ClientError as error:
        raise error
    else:
        return instances