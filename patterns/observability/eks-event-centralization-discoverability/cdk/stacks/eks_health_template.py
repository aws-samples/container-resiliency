from aws_cdk import (
    Stack,
    aws_events as events,
    aws_events_targets as targets,    
    aws_iam as iam
)
from constructs import Construct

# Stack to be deployed across the AWS Organization
class EksHealthTemplate(Stack):

    def __init__(self, 
                 scope: Construct, 
                 construct_id: str, 
                 health_cross_account_role_name: str,                               
                 central_event_bus_arn: str,
                 **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Cross account role to forward AWS Health events to EventBridge
        health_notification_cross_account_role = iam.Role(
            self, "HealthNotificationCrossAccountRole",
            assumed_by=iam.ServicePrincipal("events.amazonaws.com"),
            role_name=health_cross_account_role_name,
        )   

        health_notification_cross_account_role.add_to_policy(iam.PolicyStatement(
            actions=["events:PutEvents"],
            resources=[central_event_bus_arn]
        ))

        # Create EKS Health Event Bus in the org accounts
        local_event_bus = events.EventBus(
            self, "bus",
            event_bus_name="local-eks-health-events-bus",
            description="Local event bus for EKS Health Events"
        )        

        # EventBridge rule to capture EKS Health events from local account's event bus 
        event_rule = events.Rule(
            self,
            id="EKSHealthEventsRule",
            event_bus=local_event_bus, # Local event bus
            rule_name=f"{self.stack_name}-{self.region}-forward-to-central",
            description="Capture EKS health events and forward to central event bus",
            event_pattern=events.EventPattern(
                source=["aws.health"],
                detail_type=["AWS Health Event"],
                detail={
                    "service": ["EKS"],
                    "eventTypeCategory": ["scheduledChange"],
                    "eventTypeCode": ["AWS_EKS_PLANNED_LIFECYCLE_EVENT"],
                },
            ),
            targets=[targets.EventBus(events.EventBus.from_event_bus_arn(self, "CentralEventBus", central_event_bus_arn))] 
        )        
