#!/usr/bin/env bash
set -euo pipefail

aws_region=${AWS_REGION:-$(aws configure get region)}
aws_region=${aws_region:-us-east-1}
project_name=${PROJECT_NAME:-flightops-prod}
application_stack="${project_name}-application"
bootstrap_stack="${project_name}-bootstrap"

if [[ "${CONFIRM_DESTROY:-}" != "DELETE-${project_name}" ]]; then
  echo "Set CONFIRM_DESTROY=DELETE-${project_name} to delete all FlightOps AWS resources." >&2
  exit 1
fi

aws sts get-caller-identity --region "$aws_region" >/dev/null

stack_output() {
  local stack_name=$1
  local output_key=$2
  aws cloudformation describe-stacks     --region "$aws_region"     --stack-name "$stack_name"     --query "Stacks[0].Outputs[?OutputKey=='$output_key'].OutputValue"     --output text
}

frontend_bucket=$(stack_output "$application_stack" FrontendBucketName)
repository_name=$(stack_output "$bootstrap_stack" ApiRepositoryName)

echo "Emptying the versioned frontend bucket..."
while true; do
  delete_payload=$(aws s3api list-object-versions     --region "$aws_region"     --bucket "$frontend_bucket"     --output json |
    jq '{Objects: ([.Versions[]?, .DeleteMarkers[]?] | map({Key, VersionId})), Quiet: true}')
  object_count=$(echo "$delete_payload" | jq '.Objects | length')
  [[ "$object_count" == "0" ]] && break
  aws s3api delete-objects     --region "$aws_region"     --bucket "$frontend_bucket"     --delete "$delete_payload" >/dev/null
done

echo "Deleting the application stack..."
aws cloudformation delete-stack   --region "$aws_region"   --stack-name "$application_stack"
aws cloudformation wait stack-delete-complete   --region "$aws_region"   --stack-name "$application_stack"

image_ids=$(aws ecr list-images   --region "$aws_region"   --repository-name "$repository_name"   --query "imageIds"   --output json)
if [[ "$(echo "$image_ids" | jq length)" -gt 0 ]]; then
  aws ecr batch-delete-image     --region "$aws_region"     --repository-name "$repository_name"     --image-ids "$image_ids" >/dev/null
fi

echo "Deleting the bootstrap stack..."
aws cloudformation delete-stack   --region "$aws_region"   --stack-name "$bootstrap_stack"
aws cloudformation wait stack-delete-complete   --region "$aws_region"   --stack-name "$bootstrap_stack"

echo "FlightOps AWS resources were deleted."
