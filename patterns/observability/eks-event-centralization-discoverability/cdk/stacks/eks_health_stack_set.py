from aws_cdk import (
    App,
    Stack,
    DefaultStackSynthesizer,
    aws_cloudformation as cfn
)
from constructs import Construct
from stacks.eks_health_template import EksHealthTemplate
import json

class EksHealthStackSet(Stack):

    def __init__(self, 
                 scope: Construct, 
                 construct_id: str, 
                 organization_root_ids: list[str], 
                 health_cross_account_role_name: str,
                 central_event_bus_arn: str,
                 **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        cross_account_app = App()
        
        tempate_id = "eks-health-cross-account-template"        
        EksHealthTemplate(
            cross_account_app, 
            tempate_id,
            health_cross_account_role_name = health_cross_account_role_name,
            central_event_bus_arn = central_event_bus_arn,
            synthesizer=DefaultStackSynthesizer(generate_bootstrap_version_rule=False))
        cross_account_app.synth()
        assembly = cross_account_app.synth().get_stack_by_name(tempate_id).template
        
        cfn.CfnStackSet(
            self,
            "EksHealthStackSet",
            stack_set_name = "eks-health-stackset",
            permission_model = "SERVICE_MANAGED",
            call_as = "DELEGATED_ADMIN",
            capabilities = ["CAPABILITY_NAMED_IAM"],
            auto_deployment = cfn.CfnStackSet.AutoDeploymentProperty(
                enabled  = True, 
                retain_stacks_on_account_removal = False
            ),
            template_body=json.dumps(assembly),
            stack_instances_group = [
                cfn.CfnStackSet.StackInstancesProperty(
                    deployment_targets=cfn.CfnStackSet.DeploymentTargetsProperty(organizational_unit_ids=organization_root_ids),
                    regions = [self.region]
                )
            ]
        )
