from aws_cdk import (
    Stack,
    CfnOutput,
    aws_events as events,
)
from constructs import Construct

class EventBusStack(Stack):

    bus: events.EventBus 

    def __init__(self,
                 scope: Construct, 
                 construct_id: str, 
                 **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.bus = events.EventBus(
            self, "bus",
            event_bus_name="EKSHealthEventsBus",
            description="Event bus for EKS Health Events"
        )
        
        CfnOutput(self, "EventBusTarget", value=self.bus.event_bus_arn)
