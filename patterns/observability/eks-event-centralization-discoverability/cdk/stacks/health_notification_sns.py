from aws_cdk import (
    Stack,
    RemovalPolicy,
    aws_events as events,
    aws_events_targets as targets,
    aws_iam as iam,
    aws_sns as sns
)
from constructs import Construct

class HealthNotificationSnsStack(Stack):

    def __init__(self,
                 scope: Construct, 
                 construct_id: str, 
                 event_bus: events.EventBus,
                 **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        topic_name = kwargs.get('topic_name_suffix',"EKSHealthEvents")
        event_rule_name = kwargs.get('event_rule_name_suffix', "EKSHealthEvents")

        # Create an SNS Topic in the tooling account
        topic = sns.Topic(
            self,
            id="CentralHealthEventsTopic",
            display_name="CentralHealthEventsTopic",
            topic_name=f"{self.stack_name}-{topic_name}-{self.region}",
            enforce_ssl=True,
        )
        topic.apply_removal_policy(RemovalPolicy.DESTROY)

        # Create EventBridge Rule 
        event_rule = events.Rule(
            self,
            id="EKSHealthEventRuleSns",
            event_bus=event_bus,
            rule_name=f"{self.stack_name}-{event_rule_name}-{self.region}",
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
        