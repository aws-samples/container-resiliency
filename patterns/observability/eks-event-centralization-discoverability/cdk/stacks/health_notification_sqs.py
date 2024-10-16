from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    aws_events as events,
    aws_events_targets as targets,
    aws_iam as iam,
    aws_sqs as sqs
)
from constructs import Construct

class HealthNotificationSqsStack(Stack):

    def __init__(self,
                 scope: Construct, 
                 construct_id: str,
                 event_bus: events.EventBus,
                 **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        topic_name = kwargs.get('topic_name_suffix',"EKSHealthEvents")
        event_rule_name = kwargs.get('event_rule_name_suffix', "EKSHealthEvents")
        
        # Create SQS queue in the tooling account
        queue = sqs.Queue(self,
                          id="CentralHealthEventsQueue",
                          queue_name=f"{self.stack_name}-{topic_name}-{self.region}",
                          visibility_timeout=Duration.seconds(30),
                          retention_period=Duration.days(14),
                          enforce_ssl=True)
        queue.apply_removal_policy(RemovalPolicy.DESTROY)
        
        # Create Eventbridge Rule 
        event_rule = events.Rule(
            self,
            id="EKSHealthEventRuleSqs",
            event_bus=event_bus,
            rule_name=f"{self.stack_name}-{event_rule_name}-{self.region}",
            description="Send EKS planned lifecycle health events to SQS",
            event_pattern=events.EventPattern(
                source=["aws.health"],
                detail_type=["AWS Health Event"],
                detail={
                    "service": ["EKS"],
                    "eventTypeCategory": ["scheduledChange"],                    
                    "eventTypeCode": ["AWS_EKS_PLANNED_LIFECYCLE_EVENT"],
                },
            ),
            targets=[targets.SqsQueue(queue)]
        ) 
        event_rule.apply_removal_policy(RemovalPolicy.DESTROY)     
         
        # Add permissions to SQS queue
        queue.add_to_resource_policy(iam.PolicyStatement(
            actions=["sns:Publish"],
            principals=[iam.ServicePrincipal("events.amazonaws.com")],
            resources=[queue.queue_arn],
            conditions={
                "ArnEquals": {
                    "aws:SourceArn": event_rule.rule_arn
                }
            }
        ))         
                      