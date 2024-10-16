#!/usr/bin/env python3
import aws_cdk as cdk
import os
from stacks.health_notification_sns import HealthNotificationSnsStack
from stacks.health_notification_sqs import HealthNotificationSqsStack
from stacks.event_bus import EventBusStack



app = cdk.App()

event_bus_stack = EventBusStack(app, "EventBridgeCdkStack")

HealthNotificationSnsStack(
    app, "HealthNotificationSNSCdkStack", event_bus=event_bus_stack.bus
)

health_notifications_sqs_stack = HealthNotificationSqsStack(
    app, "HealthNotificationSQSCdkStack", event_bus=event_bus_stack.bus
)


app.synth()
