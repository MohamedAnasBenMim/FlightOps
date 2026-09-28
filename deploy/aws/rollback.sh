#!/usr/bin/env bash
set -euo pipefail

aws_region=${AWS_REGION:-$(aws configure get region)}
aws_region=${aws_region:-us-east-1}
project_name=${PROJECT_NAME:-flightops-prod}
bootstrap_stack="${project_name}-bootstrap"
application_stack="${project_name}-application"
image_tag=${IMAGE_TAG:?Set IMAGE_TAG to a previously published commit SHA}

if [[ "${CONFIRM_ROLLBACK:-}" != "YES" ]]; then
  echo "Set CONFIRM_ROLLBACK=YES after checking migration compatibility." >&2
  exit 1
fi

repository_uri=$(aws cloudformation describe-stacks   --region "$aws_region"   --stack-name "$bootstrap_stack"   --query "Stacks[0].Outputs[?OutputKey=='ApiRepositoryUri'].OutputValue"   --output text)
image_uri="${repository_uri}:${image_tag}"
origin_verify_header=$(openssl rand -hex 32)

aws ecr describe-images   --region "$aws_region"   --repository-name "${repository_uri#*/}"   --image-ids imageTag="$image_tag" >/dev/null

aws cloudformation deploy   --region "$aws_region"   --stack-name "$application_stack"   --template-file deploy/aws/infrastructure.yml   --capabilities CAPABILITY_NAMED_IAM   --parameter-overrides     ProjectName="$project_name"     ApiImageUri="$image_uri"     OriginVerifyHeader="$origin_verify_header"   --no-fail-on-empty-changeset

cluster_name=$(aws cloudformation describe-stacks   --region "$aws_region"   --stack-name "$application_stack"   --query "Stacks[0].Outputs[?OutputKey=='ClusterName'].OutputValue"   --output text)
service_name=$(aws cloudformation describe-stacks   --region "$aws_region"   --stack-name "$application_stack"   --query "Stacks[0].Outputs[?OutputKey=='ServiceName'].OutputValue"   --output text)

aws ecs wait services-stable   --region "$aws_region"   --cluster "$cluster_name"   --services "$service_name"

echo "Rolled back the API to $image_uri"
