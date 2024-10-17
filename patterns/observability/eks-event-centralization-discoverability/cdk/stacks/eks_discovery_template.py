from aws_cdk import (
    Stack,
    aws_iam as iam,
)
from constructs import Construct


# Cross account permissions for Lambda to perform discovery in accounts 
# across the AWS Organizations
class EksDiscoveryTemplate(Stack):

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        discovery_cross_account_role_name: str,
        lambda_execution_role_arn: str,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Cross account role that is assumed by EKS Discovery Lambda function
        discovery_cross_account_role = iam.Role(
            self,
            "EKSDiscoveryCrossAccountRole",
            assumed_by=iam.ArnPrincipal(lambda_execution_role_arn),
            role_name=discovery_cross_account_role_name,
        )

        discovery_cross_account_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "eks:ListClusters",
                    "eks:DescribeCluster",
                    "eks:ListTagsForResource",
                ],
                resources=["*"],
            )
        )
