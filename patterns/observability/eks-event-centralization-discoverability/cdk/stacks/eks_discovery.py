from aws_cdk import (
    Stack,
    CfnOutput,
    Duration,
    RemovalPolicy,
    aws_iam as iam,
    aws_lambda as lambda_,
    aws_s3 as s3,
    aws_sns as sns, 
    aws_scheduler as scheduler
)
from constructs import Construct

class EKSDiscovery(Stack):
    
    def __init__(self,
                 scope: Construct, 
                 construct_id: str, 
                 lambda_execution_role_name: str,
                 cross_account_role_name: str,
                 **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        lambda_execution_role = iam.Role(
            self, "LambdaExecutionRole",
            assumed_by = iam.ServicePrincipal("lambda.amazonaws.com"),
            role_name = lambda_execution_role_name,
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ]
        )        

        lambda_execution_role.add_to_policy(iam.PolicyStatement(
            actions=["organizations:ListAccounts"],
            resources=["*"]
        )) 
        
        lambda_execution_role.add_to_policy(iam.PolicyStatement(
            actions=["sts:AssumeRole"],
            resources=["*"]
        ))
        
        lambda_execution_role.add_to_policy(iam.PolicyStatement(
            actions=["s3:PutObject"],
            resources=["*"]
        ))
        
        lambda_execution_role.add_to_policy(iam.PolicyStatement(
            actions=["sns:Publish"],
            resources=["*"]
        ))        

        lambda_function = lambda_.Function(
            self, 
            "eks-discovery-lambda",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="index.lambda_handler",
            code=lambda_.Code.from_asset("../lambda"),
            role=lambda_execution_role,
            timeout=Duration.seconds(300),
        )
        
        bucket = s3.Bucket(self, 
                           id="EKSDiscoveryResultBucket",
                           block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
                           encryption=s3.BucketEncryption.S3_MANAGED,
                           enforce_ssl=True,
                           versioned=True,
                           bucket_name=f"eks-discovery-{self.account}-{self.region}",
                           removal_policy=RemovalPolicy.DESTROY, 
                           auto_delete_objects=True)  
        
        topic = sns.Topic(self,
                          id="EKSDiscoverySNSTopic",
                          display_name="EKSDiscoverySNSTopic",
                          topic_name="EKSDiscoverySNSTopic")
    
        schedulerRole = iam.Role(
            self,
            "SchedulerRole",
            assumed_by = iam.ServicePrincipal("scheduler.amazonaws.com")
        )        

        schedulerRole.add_to_policy(iam.PolicyStatement(
            actions=["lambda:InvokeFunction"],
            resources=[lambda_function.function_arn]
        ))
    
        scheduler.CfnSchedule(self,
                              id="EKSDiscoveryWeeklySchedule",
                              name="EKSDiscoveryWeeklySchedule",
                              flexible_time_window=scheduler.CfnSchedule.FlexibleTimeWindowProperty(
                                  mode="OFF"
                              ),
                              schedule_expression="cron(0 0 ? * SUN *)", # Runs every Sunday at midnight
                              target=scheduler.CfnSchedule.TargetProperty(
                                  arn=lambda_function.function_arn,
                                  role_arn=schedulerRole.role_arn
                              ))
        
        lambda_function.add_environment("S3_BUCKET_NAME", bucket.bucket_name)
        lambda_function.add_environment("SNS_TOPIC_ARN", topic.topic_arn)
        lambda_function.add_environment("CROSS_ACCOUNT_ROLE_NAME", cross_account_role_name)
                
        CfnOutput(self, "LambdaExecutionRoleArn", value=lambda_execution_role.role_arn)
        