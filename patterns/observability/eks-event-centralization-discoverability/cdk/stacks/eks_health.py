from aws_cdk import (
    CfnOutput,
    Duration,    
    RemovalPolicy,
    Stack,    
    aws_events as events,
    aws_events_targets as targets,
    aws_iam as iam,
    aws_sqs as sqs,
    aws_sns as sns    
)
from constructs import Construct

class EKSHealth(Stack):

    def __init__(self,
                 scope: Construct, 
                 construct_id: str, 
                 event_bus_name: str,
                 topic_name: str,
                 **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        event_bus = events.EventBus(
            self, "bus",
            event_bus_name=event_bus_name,
            description="Event bus for EKS Health Events"
        )
        
        # Create an SNS Topic in the tooling account
        topic = sns.Topic(
            self,
            id="CentralHealthEventsTopic",
            display_name="CentralHealthEventsTopic",
            topic_name=f"{self.stack_name}-{topic_name}-{self.region}",
            enforce_ssl=True,
        )
        topic.apply_removal_policy(RemovalPolicy.DESTROY)

        # Create EventBridge Rule to forward to SNS
        event_rule = events.Rule(
            self,
            id="EKSHealthEventRuleSns",
            event_bus=event_bus,
            rule_name=f"{self.stack_name}-{self.region}-sns",
            description="Send EKS planned lifecycle health events to SNS",
            event_pattern=events.EventPattern(
                source=["aws.health"],
                detail_type=["AWS Health Event"],
                detail={
                    "service": ["EKS"],
                    "eventTypeCategory": ["scheduledChange"],
                    "eventTypeCode": ["AWS_EKS_PLANNED_LIFECYCLE_EVENT"],
                },
            ),
            targets=[targets.SnsTopic(topic)]
        )
        
        # Add necessary permissions to the SNS topic
        topic.add_to_resource_policy(iam.PolicyStatement(
            actions=["sns:Publish"],
            principals=[iam.ServicePrincipal("events.amazonaws.com")],
            resources=[topic.topic_arn],
            conditions={
                "ArnEquals": {
                    "aws:SourceArn": event_rule.rule_arn
                }
            }
        ))
        
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
            rule_name=f"{self.stack_name}-{self.region}-sqs",
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
                    
        CfnOutput(self, "CentralEventBusArn", value=event_bus.event_bus_arn)
