#!/usr/bin/env bash
set -euo pipefail

aws_region=${AWS_REGION:-$(aws configure get region)}
aws_region=${aws_region:-us-east-1}
project_name=${PROJECT_NAME:-flightops-prod}
stack_name="${project_name}-application"

stack_output() {
  local output_key=$1
  aws cloudformation describe-stacks     --region "$aws_region"     --stack-name "$stack_name"     --query "Stacks[0].Outputs[?OutputKey=='$output_key'].OutputValue"     --output text
}

cluster_name=$(stack_output ClusterName)
task_definition=$(stack_output TaskDefinitionArn)
subnet_ids=$(stack_output PublicSubnetIds)
security_group=$(stack_output ApiSecurityGroupId)
network_configuration="awsvpcConfiguration={subnets=[$subnet_ids],securityGroups=[$security_group],assignPublicIp=ENABLED}"
overrides='{"containerOverrides":[{"name":"api","command":["alembic","upgrade","head"]}]}'

task_arn=$(aws ecs run-task   --region "$aws_region"   --cluster "$cluster_name"   --launch-type FARGATE   --platform-version LATEST   --task-definition "$task_definition"   --network-configuration "$network_configuration"   --overrides "$overrides"   --query "tasks[0].taskArn"   --output text)

if [[ -z "$task_arn" || "$task_arn" == "None" ]]; then
  echo "ECS did not start the migration task." >&2
  exit 1
fi

echo "Waiting for migration task $task_arn..."
aws ecs wait tasks-stopped   --region "$aws_region"   --cluster "$cluster_name"   --tasks "$task_arn"

exit_code=$(aws ecs describe-tasks   --region "$aws_region"   --cluster "$cluster_name"   --tasks "$task_arn"   --query "tasks[0].containers[?name=='api'].exitCode | [0]"   --output text)
stopped_reason=$(aws ecs describe-tasks   --region "$aws_region"   --cluster "$cluster_name"   --tasks "$task_arn"   --query "tasks[0].stoppedReason"   --output text)

if [[ "$exit_code" != "0" ]]; then
  echo "Migration failed with exit code $exit_code: $stopped_reason" >&2
  exit 1
fi

echo "Database migration completed successfully."
