# Real-Time Support Agent Assistant

The goal of this application to develop a simple chat interface to display the autonomous support "Co-pilot" system that can be used by the claims agent to understand the claim that they are processing - to make more informed business decisions, speed up SLA and ultimately to provide and more unique Customer Experience with AI

The stack is LangGraph for the orchestration, FastAPI for the backend, and React for the frontend. The two containers run on ECS. IaC that will be used is Terraform and basic CI/CD using Github Actions

The goal is not to overcomplicate the setup. Rather to show the most viable product for the Interview Assessment

## Operation

Each conversation is one LangGraph workflo. A customer message starts a workflow run. The run does the intent analysis, then the knowledge retrieval if it is necessary, then the recommendations, then the summary. 

The agent console shows the conversation and the sidebar. The button "Open customer chat" opens the customer view in a new tab. The two views use the same conversation and their own WebSocket connections.


## Repository

```
backend/    FastAPI and LangGraph service: API, WebSocket, workflow, knowledge documents
frontend/   React application. nginx supplies it and sends the API requests to the backend
terraform/  AWS infrastructure: VPC, ECS, ECR, IAM, logs, secrets, and a bootstrap stack
docs/       Design documents and the related compromises
.github/    The CI workflow and the deploy workflow
```

## Local operation

You need an [OpenRouter](https://openrouter.ai) API key.

```bash
cp backend/.env.example backend/.env   # put your OPENROUTER_API_KEY in this file
docker compose up --build
# open http://localhost:3000
```

Without Docker, use two terminals:

```bash
cd backend && uv sync && uv run uvicorn app.main:app --reload   # port 8000
cd frontend && npm install && npm run dev                        # port 5173
```

Tests and lint checks:

```bash
cd backend && uv run pytest && uv run ruff check .
cd frontend && npm run lint && npm run build
```
