# AWS deployment runbook

## Current state

The infrastructure and deployment automation are complete and validated
offline. Live provisioning has not run because the AWS CLI profile available
during implementation returned InvalidClientTokenId on 2026-09-28.

Do not mark the provisioning roadmap items complete until the deployment,
migration, HTTPS smoke test, restart test, persistence check, and log review have
all succeeded in the intended AWS account.

## Architecture

~~~mermaid
flowchart LR
    U[Browser] -->|HTTPS| CF[CloudFront]
    CF -->|Static assets| S3[Private S3 bucket]
    CF -->|API requests + origin header| ALB[Application Load Balancer]
    ALB --> ECS[ECS Fargate API]
    ECS --> RDS[(Private encrypted RDS PostgreSQL)]
    ECS --> OM[Open-Meteo]
    ECS --> CW[CloudWatch Logs]
    ECR[ECR immutable image] --> ECS
~~~

The API task runs in a public subnet with a public IP solely to pull its image,
read its secret, and call Open-Meteo without a NAT gateway. Its security group
accepts port 8000 only from the ALB security group; no direct internet ingress is
allowed. RDS uses two private subnets and accepts PostgreSQL only from the API
security group.

AWS recommends private subnets for reducing ECS exposure. A production system
with a larger budget should move the task into private subnets and add either
NAT gateways or the required VPC endpoints. The portfolio deployment documents
this explicit cost/security tradeoff. See the AWS guidance on
[Fargate task networking](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/fargate-task-networking.html)
and [ECS exposure remediation](https://docs.aws.amazon.com/securityhub/latest/userguide/exposure-ecs-service.html).

CloudFront supplies the public HTTPS endpoint and sends an unguessable origin
header. The ALB otherwise returns 403. API cache behavior uses AWS's managed
CachingDisabled policy, so assessment and mission responses are never served
from an edge cache.

## Estimated monthly cost

Estimate for us-east-1, 730 hours, one lightly used portfolio environment:

| Component | Assumption | Approximate monthly cost |
| --- | --- | ---: |
| ECS Fargate | 0.25 vCPU, 0.5 GB, one task | $9 |
| RDS PostgreSQL | Single-AZ db.t4g.micro | $12–15 |
| RDS storage | 20 GB gp3 | $2–3 |
| Application Load Balancer | Hourly charge plus low LCU use | $17–22 |
| Public IPv4 | ALB addresses plus one task address | $7–11 |
| Secrets Manager | One secret | $0.40 |
| ECR, S3, CloudFront, CloudWatch | Small image/site, low traffic/log volume | $0–5 |
| **Expected total** | Before tax and unusual traffic | **$48–65/month** |

This is an estimate, not a quote. Review the AWS Pricing Calculator before every
deployment. AWS bills Fargate by requested CPU and memory duration
([Fargate pricing](https://aws.amazon.com/fargate/pricing/)); RDS instances are
billed while running
([RDS PostgreSQL pricing](https://aws.amazon.com/rds/postgresql/pricing/)); and
ALB billing includes running hours plus LCUs
([Elastic Load Balancing pricing](https://aws.amazon.com/elasticloadbalancing/pricing/)).
CloudWatch includes a 5 GB logs free allowance, then region-specific ingestion
and storage charges
([CloudWatch pricing](https://aws.amazon.com/cloudwatch/pricing/)).

Set an AWS Budget alert before deploying. The stack deliberately uses one task,
Single-AZ RDS, seven-day log retention, PriceClass_100, and no NAT gateway to
control portfolio costs. It is not a high-availability production design.

## Prerequisites

- Valid AWS CLI credentials with a deliberately selected account and region.
- Docker, Node.js 20, npm, jq, curl, OpenSSL, and Git.
- Permission to manage CloudFormation, ECR, ECS, IAM, EC2 networking, ELB, RDS,
  Secrets Manager, CloudWatch, S3, and CloudFront.
- A clean Git worktree.
- Billing alerts and explicit acceptance of the estimate above.

Verify identity before any mutation:

~~~bash
aws sts get-caller-identity
aws configure get region
~~~

## Deploy

The script refuses to run without explicit cost confirmation and tags the image
with the current commit SHA.

~~~bash
export AWS_REGION=us-east-1
export PROJECT_NAME=flightops-prod
export CONFIRM_AWS_COSTS=YES
deploy/aws/deploy.sh
~~~

It performs these operations:

1. Creates an ECR repository with immutable tags and scan-on-push.
2. Builds the x86-64 API image and pushes the commit-SHA tag.
3. Creates or updates networking, RDS, ECS, ALB, CloudFront, S3, logging, and
   alarms through CloudFormation.
4. Runs Alembic as a one-off Fargate task and verifies its exit code.
5. Builds Vue, uploads fingerprinted assets and non-cacheable index.html, and
   invalidates CloudFront.
6. Waits for the ECS service to become stable.
7. Prints the HTTPS application URL.

CloudFront can take several minutes to reach every edge after its first creation.

## Verify

~~~bash
export BASE_URL=https://the-distribution-name.cloudfront.net
deploy/aws/smoke.sh
~~~

Then verify:

- the dashboard loads over HTTPS;
- /health/live and /health/ready return 200;
- the smoke script creates and retrieves a persisted assessment;
- stopping the current ECS task causes ECS to replace it;
- the assessment remains retrievable after replacement;
- CloudWatch contains structured request logs with request IDs;
- the ALB DNS name returns 403 without the private origin header;
- all three CloudWatch alarms show OK or insufficient-data, not ALARM;
- ECR reports the pushed image scan result.

## Migrations

deploy/aws/migrate.sh starts the API task definition with its command overridden
to alembic upgrade head. The task uses the same network, secret, image, and
database endpoint as the service. It waits for completion and fails if the
container exit code is nonzero.

Migration policy:

- review generated SQL before deployment;
- prefer backward-compatible additive changes;
- run migration before relying on new columns;
- never let every service replica run migrations on startup;
- make a manual RDS snapshot before a destructive schema change.

## Rollback

For an application-only rollback, choose a known commit-SHA image still present
in ECR:

~~~bash
export IMAGE_TAG=previous_commit_sha
export CONFIRM_ROLLBACK=YES
deploy/aws/rollback.sh
~~~

Only use this if deployed migrations remain backward compatible. Database
rollbacks require a tested forward-fix or restoration from a manual snapshot;
restoring a snapshot creates a new database and requires a controlled stack
update. Never improvise a destructive downgrade on the only database.

CloudFormation's ECS deployment circuit breaker automatically rolls back a task
revision that cannot become healthy.

## Teardown

Teardown permanently deletes the database, stored assessment data, frontend
objects and versions, container images, networking, and logs created by these
stacks. It requires a project-specific confirmation value:

~~~bash
export CONFIRM_DESTROY=DELETE-flightops-prod
deploy/aws/teardown.sh
~~~

The template intentionally deletes the portfolio database instead of retaining a
billable final snapshot. Export anything important before teardown, then confirm
in AWS Billing that no related chargeable resources remain.
