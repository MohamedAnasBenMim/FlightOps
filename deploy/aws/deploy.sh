#!/usr/bin/env bash
set -euo pipefail

project_root=$(git rev-parse --show-toplevel)
cd "$project_root"

aws_region=${AWS_REGION:-$(aws configure get region)}
aws_region=${aws_region:-us-east-1}
project_name=${PROJECT_NAME:-flightops-prod}
bootstrap_stack="${project_name}-bootstrap"
application_stack="${project_name}-application"
image_tag=${IMAGE_TAG:-$(git rev-parse --short=12 HEAD)}

for command_name in aws docker jq openssl npm; do
  command -v "$command_name" >/dev/null || {
    echo "Required command is missing: $command_name" >&2
    exit 1
  }
done

if [[ "${CONFIRM_AWS_COSTS:-}" != "YES" ]]; then
  echo "Set CONFIRM_AWS_COSTS=YES after reviewing docs/DEPLOYMENT.md." >&2
  exit 1
fi

aws sts get-caller-identity --region "$aws_region" >/dev/null

if [[ -n "$(git status --porcelain)" ]]; then
  echo "Deployment requires a clean Git worktree for an immutable image tag." >&2
  exit 1
fi

echo "Deploying ECR bootstrap stack in $aws_region..."
aws cloudformation deploy   --region "$aws_region"   --stack-name "$bootstrap_stack"   --template-file deploy/aws/bootstrap.yml   --parameter-overrides ProjectName="$project_name"   --no-fail-on-empty-changeset

repository_uri=$(aws cloudformation describe-stacks   --region "$aws_region"   --stack-name "$bootstrap_stack"   --query "Stacks[0].Outputs[?OutputKey=='ApiRepositoryUri'].OutputValue"   --output text)
registry_host=${repository_uri%%/*}
image_uri="${repository_uri}:${image_tag}"

aws ecr get-login-password --region "$aws_region" |
  docker login --username AWS --password-stdin "$registry_host"

echo "Building and publishing $image_uri..."
docker build --platform linux/amd64 --tag "$image_uri" .
docker push "$image_uri"

origin_verify_header=$(openssl rand -hex 32)

echo "Deploying the application stack. RDS creation can take several minutes..."
aws cloudformation deploy   --region "$aws_region"   --stack-name "$application_stack"   --template-file deploy/aws/infrastructure.yml   --capabilities CAPABILITY_NAMED_IAM   --parameter-overrides     ProjectName="$project_name"     ApiImageUri="$image_uri"     OriginVerifyHeader="$origin_verify_header"   --no-fail-on-empty-changeset

echo "Running the one-off database migration..."
AWS_REGION="$aws_region" PROJECT_NAME="$project_name" deploy/aws/migrate.sh

frontend_bucket=$(aws cloudformation describe-stacks   --region "$aws_region"   --stack-name "$application_stack"   --query "Stacks[0].Outputs[?OutputKey=='FrontendBucketName'].OutputValue"   --output text)
distribution_id=$(aws cloudformation describe-stacks   --region "$aws_region"   --stack-name "$application_stack"   --query "Stacks[0].Outputs[?OutputKey=='DistributionId'].OutputValue"   --output text)
application_url=$(aws cloudformation describe-stacks   --region "$aws_region"   --stack-name "$application_stack"   --query "Stacks[0].Outputs[?OutputKey=='ApplicationUrl'].OutputValue"   --output text)

echo "Building and uploading the Vue application..."
npm ci --prefix frontend
npm run build --prefix frontend
aws s3 sync frontend/dist "s3://$frontend_bucket"   --region "$aws_region"   --delete   --exclude index.html   --cache-control "public,max-age=31536000,immutable"
aws s3 cp frontend/dist/index.html "s3://$frontend_bucket/index.html"   --region "$aws_region"   --cache-control "no-cache"   --content-type "text/html"
aws cloudfront create-invalidation   --distribution-id "$distribution_id"   --paths "/*" >/dev/null

echo "Waiting for the ECS service to stabilize..."
cluster_name=$(aws cloudformation describe-stacks   --region "$aws_region"   --stack-name "$application_stack"   --query "Stacks[0].Outputs[?OutputKey=='ClusterName'].OutputValue"   --output text)
service_name=$(aws cloudformation describe-stacks   --region "$aws_region"   --stack-name "$application_stack"   --query "Stacks[0].Outputs[?OutputKey=='ServiceName'].OutputValue"   --output text)
aws ecs wait services-stable   --region "$aws_region"   --cluster "$cluster_name"   --services "$service_name"

echo "Deployment complete: $application_url"
echo "Run BASE_URL=$application_url deploy/aws/smoke.sh after CloudFront finishes propagating."
