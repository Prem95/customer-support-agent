variable "project" {
  description = "Project name used as a prefix for all resources"
  type        = string
  default     = "agent-workflow"
}

variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "ap-southeast-1"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "allowed_ingress_cidrs" {
  description = "CIDRs allowed to reach the frontend (office/VPN ranges for an internal tool)"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "frontend_image_tag" {
  description = "Frontend container image tag to deploy"
  type        = string
  default     = "latest"
}

variable "backend_image_tag" {
  description = "Backend container image tag to deploy"
  type        = string
  default     = "latest"
}

variable "llm_model" {
  description = "OpenRouter model identifier used by the backend"
  type        = string
  default     = "google/gemini-3.7-flash"
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 14
}
