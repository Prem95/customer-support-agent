# Real-Time Support Agent Assistant

The goal of this application to develop a simple chat interface to display the autonomous support "Co-pilot" system that can be used by the claims agent to understand the claim that they are processing - to make more informed business decisions, speed up SLA and ultimately to provide and more unique Customer Experience with AI

The stack is LangGraph for the orchestration, FastAPI for the backend, and React for the frontend. The two containers run on ECS. IaC that will be used is Terraform and basic CI/CD using Github Actions

The goal is not to overcomplicate the setup. Rather to show the most viable product for the Interview Assessment

## Operation

Each conversation is one LangGraph workflo. A customer message starts a workflow run. The run does the intent analysis, then the knowledge retrieval if it is necessary, then the recommendations, then the summary. 

The agent console shows the conversation and the sidebar. The button "Open customer chat" opens the customer view in a new tab. The two views use the same conversation and their own WebSocket connections.


## Repository

```
backend/    FastAPI and LangGraph service
frontend/   
terraform/  AWS infrastructure
docs/       design.md: architecture, workflow design, security, and operations
.github/    CI actions
```

## Local operation

You need an [OpenRouter](https://openrouter.ai) API key.

```bash
cp backend/.env.example backend/.env   # put your OPENROUTER_API_KEY in this file
make dev                               # open http://localhost:3000
```

Common commands:

| Command | Action |
|---|---|
| `make dev` | build and run both containers on :3000 |

## Infrastructure

Two ECS Fargate services in one VPC

```
terraform/bootstrap/   S3 state bucket, GitHub role, ECR repositories
terraform/             VPC, ECS, IAM, logs, secrets (applied by CI)
```

### First deployment

```bash
# 1. one-time bootstrap, with local state
cd terraform/bootstrap
terraform init && terraform apply -var github_repository=<owner>/<repo>

# 2. in GitHub, add the secrets AWS_DEPLOY_ROLE_ARN and TF_STATE_BUCKET,
#    the variable AWS_REGION, and a "production" environment

# 3. store the API key
aws secretsmanager put-secret-value \
  --secret-id agent-workflow/openrouter-api-key --secret-string '<OPENROUTER_API_KEY>'

# 4. push to main
```
