import json, logging, os
from lib.ec2 import get_instances
from lib.ssm import start_execution
from lib.kubernetes import KubeAPI
from lib.s3 import list_bundles_latest

logger = logging.getLogger()
logger.setLevel("INFO")

CLUSTER_ID=os.environ['CLUSTER_ID']
CLUSTER_REGION=os.environ['CLUSTER_REGION']
BUNDLE_RECENCY_SECONDS=int(os.environ['BUNDLE_RECENCY_SECONDS'])
LOG_COLLECTION_NODES_MAX=int(os.environ['LOG_COLLECTION_NODES_MAX'])
LOG_COLLECTION_BUCKET=os.environ['LOG_COLLECTION_BUCKET']
SSM_AUTOMATION_EXECUTION_ROLE_ARN=os.environ['SSM_AUTOMATION_EXECUTION_ROLE_ARN']

def lambda_handler(event, context):
    try:
        for record in event['Records']:
            message = json.loads(record['Sns']['Message'])
            logger.info(message)
            alerts = message['alerts']
 
        for alert in alerts:
            if alert['labels']['alertname'] == 'KubeNNR':
                nnr_execution(alert['labels']['node'])
            elif alert['labels']['alertname'] == 'KubeNNRMax':
                logger.info(f"The EKS cluster {CLUSTER_ID} in region {CLUSTER_REGION} has more than 5 nodes in Not Ready state")
                kubeapi = KubeAPI(CLUSTER_ID, CLUSTER_REGION)
                not_ready_nodes = kubeapi.list_nodes_notready(LOG_COLLECTION_NODES_MAX)
                nnr_gt_execution(not_ready_nodes)
            else:
                logger.error("Invalid alert received, skipping.")
    except Exception as error:
        logger.error(error)

def nnr_execution(node):
    try:
        instances = get_instances([node])
        for instance in instances:
            exec_id = start_execution(instance, LOG_COLLECTION_BUCKET, SSM_AUTOMATION_EXECUTION_ROLE_ARN)
            logger.info(f"EKS Log Collector automation executed for {instance}: {exec_id}")
    except Exception as error:
        raise error
    
def nnr_gt_execution(nodes):
    try:
        not_ready_instances = get_instances(nodes)
        logger.info(f"Found {len(not_ready_instances)} instances in Not Ready state: {', '.join(not_ready_instances)}")
        bundles = list_bundles_latest(LOG_COLLECTION_BUCKET, BUNDLE_RECENCY_SECONDS)
        if len(bundles) > 0:
            logger.info(f"Log bundles already uploaded in last {BUNDLE_RECENCY_SECONDS} secs, skipping.")
        else:
            for instance in not_ready_instances:
                exec_id = start_execution(instance, LOG_COLLECTION_BUCKET, SSM_AUTOMATION_EXECUTION_ROLE_ARN)
                logger.info(f"EKS Log Collector automation executed for {instance}: {exec_id}")
    except Exception as error:
        raise error