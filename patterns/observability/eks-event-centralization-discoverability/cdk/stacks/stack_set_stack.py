from aws_cdk import (
    App,
    Stack,
    CfnParameter,
    DefaultStackSynthesizer,
    aws_cloudformation as cfn
)
from constructs import Construct
from stacks.cross_account_role_stack import CrossAccountRoleStack
import json

class StackSetStack(Stack):

    def __init__(self, 
                 scope: Construct, 
                 construct_id: str, 
                 organization_root_ids: list[str], 
                 lambda_execution_role_arn: str, 
                 cross_account_role_name: str,
                 **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        cross_account_app = App()
        CrossAccountRoleStack(
            cross_account_app, 
            "CrossAccountRoleStack",
            lambda_execution_role_arn = lambda_execution_role_arn, 
            cross_account_role_name = cross_account_role_name,
            synthesizer=DefaultStackSynthesizer(generate_bootstrap_version_rule=False))
        cross_account_app.synth()
        assembly = cross_account_app.synth().get_stack_by_name("CrossAccountRoleStack").template
        
        cfn.CfnStackSet(
            self,
            "EKSDiscoveryStackSet",
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
