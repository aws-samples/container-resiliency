from aws_cdk import (
    Stack,
    aws_iam as iam
)
from constructs import Construct

# Stack to be deployed across the AWS Organization
class CrossAccountRoleStack(Stack):

    def __init__(self, 
                 scope: Construct, 
                 construct_id: str, 
                 lambda_execution_role_arn: str, 
                 cross_account_role_name: str,
                 **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        cross_account_role = iam.Role(
            self, "EKSDiscoveryCrossAccountRole",
            assumed_by=iam.ArnPrincipal(lambda_execution_role_arn),
            role_name=cross_account_role_name
        )

        cross_account_role.add_to_policy(iam.PolicyStatement(
            actions=["eks:ListClusters", 
                     "eks:DescribeCluster", 
                     "eks:ListTagsForResource"],
            resources=["*"]
        ))
