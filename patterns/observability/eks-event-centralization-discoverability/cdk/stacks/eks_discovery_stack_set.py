from aws_cdk import (
    App,
    Stack,
    DefaultStackSynthesizer,
    aws_cloudformation as cfn
)
from constructs import Construct
from stacks.eks_discovery_template import EksDiscoveryTemplate
import json

class EksDiscoveryStackSet(Stack):

    def __init__(self, 
                 scope: Construct, 
                 construct_id: str, 
                 organization_root_ids: list[str], 
                 discovery_cross_account_role_name: str,
                 lambda_execution_role_arn: str,                  
                 **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        cross_account_app = App()
        
        tempate_id = "eks-discovery-cross-account-template"
        EksDiscoveryTemplate(
            cross_account_app, 
            tempate_id,
            lambda_execution_role_arn = lambda_execution_role_arn, 
            discovery_cross_account_role_name = discovery_cross_account_role_name,
            synthesizer=DefaultStackSynthesizer(generate_bootstrap_version_rule=False))
        cross_account_app.synth()
        assembly = cross_account_app.synth().get_stack_by_name(tempate_id).template
        
        cfn.CfnStackSet(
            self,
            "EksDiscoveryStackSet",
            stack_set_name = "eks-discovery-stackset",
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
