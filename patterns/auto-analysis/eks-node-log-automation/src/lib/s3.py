import boto3, botocore
from datetime import datetime, timedelta
import pytz

s3 = boto3.resource("s3")

def list_bundles_latest(bucket, time_delta):
    start_from = datetime.now(pytz.utc) - timedelta(seconds=time_delta)
    try:
        bucket = s3.Bucket(bucket)
        bundles = bucket.objects.filter()
        bundles = [obj.key for obj in sorted(bundles, key=lambda x: x.last_modified, reverse=True) if obj.last_modified >= start_from]
    except botocore.exceptions.ClientError as error:
        raise error
    else:
        return bundles

