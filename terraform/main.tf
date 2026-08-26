locals {
  frontend_image = "${data.aws_ecr_repository.frontend.repository_url}:${var.frontend_image_tag}"
  backend_image  = "${data.aws_ecr_repository.backend.repository_url}:${var.backend_image_tag}"
  backend_port   = 8000
  frontend_port  = 8080
}

module "network" {
  source   = "./modules/network"
  name     = var.project
  vpc_cidr = var.vpc_cidr
}

resource "aws_ecs_cluster" "this" {
  name = var.project

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

# frontend reaches the backend as backend.<project>.local, VPC-internal only
resource "aws_service_discovery_private_dns_namespace" "this" {
  name = "${var.project}.local"
  vpc  = module.network.vpc_id
}

resource "aws_service_discovery_service" "backend" {
  name = "backend"

  dns_config {
    namespace_id = aws_service_discovery_private_dns_namespace.this.id
    dns_records {
      type = "A"
      ttl  = 10
    }
  }

  health_check_custom_config {
    failure_threshold = 1
  }
}

module "backend_service" {
  source = "./modules/ecs-service"

  name               = "${var.project}-backend"
  cluster_id         = aws_ecs_cluster.this.id
  image              = local.backend_image
  container_port     = local.backend_port
  subnet_ids         = module.network.private_subnet_ids
  security_group_ids = [aws_security_group.backend.id]
  execution_role_arn = aws_iam_role.backend_execution.arn
  task_role_arn      = aws_iam_role.task.arn
  log_group_name     = aws_cloudwatch_log_group.backend.name
  aws_region         = var.aws_region

  service_registry_arn = aws_service_discovery_service.backend.arn

  environment = {
    ENVIRONMENT = "aws"
    LLM_MODEL   = var.llm_model
    LOG_LEVEL   = "INFO"
  }

  secrets = {
    OPENROUTER_API_KEY = data.aws_secretsmanager_secret.openrouter_api_key.arn
  }

  health_check_command = [
    "CMD-SHELL",
    "python -c \"import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health')\" || exit 1",
  ]
}

# The frontend runs in the public subnets with a public IP. There is no load
# balancer: the security group limits access to allowed_ingress_cidrs.
module "frontend_service" {
  source = "./modules/ecs-service"

  name               = "${var.project}-frontend"
  cluster_id         = aws_ecs_cluster.this.id
  image              = local.frontend_image
  container_port     = local.frontend_port
  subnet_ids         = module.network.public_subnet_ids
  security_group_ids = [aws_security_group.frontend.id]
  assign_public_ip   = true
  execution_role_arn = aws_iam_role.frontend_execution.arn
  task_role_arn      = aws_iam_role.task.arn
  log_group_name     = aws_cloudwatch_log_group.frontend.name
  aws_region         = var.aws_region

  environment = {
    BACKEND_HOST = "backend.${aws_service_discovery_private_dns_namespace.this.name}"
    BACKEND_PORT = tostring(local.backend_port)
  }
}
