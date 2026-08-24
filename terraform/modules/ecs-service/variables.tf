variable "name" {
  description = "Service name (used for task family, log group, discovery)"
  type        = string
}

variable "cluster_id" {
  description = "ECS cluster ID"
  type        = string
}

variable "image" {
  description = "Full container image URI including tag"
  type        = string
}

variable "container_port" {
  description = "Port the container listens on"
  type        = number
}

variable "cpu" {
  description = "Fargate task CPU units"
  type        = number
  default     = 256
}

variable "memory" {
  description = "Fargate task memory (MiB)"
  type        = number
  default     = 512
}

variable "desired_count" {
  description = "Number of tasks to run"
  type        = number
  default     = 1
}

variable "subnet_ids" {
  description = "Private subnet IDs for the tasks"
  type        = list(string)
}

variable "security_group_ids" {
  description = "Security groups attached to the tasks"
  type        = list(string)
}

variable "environment" {
  description = "Plain environment variables for the container"
  type        = map(string)
  default     = {}
}

variable "secrets" {
  description = "Secret environment variables, name => Secrets Manager ARN"
  type        = map(string)
  default     = {}
}

variable "execution_role_arn" {
  description = "Task execution role ARN (image pull, logs, secrets injection)"
  type        = string
}

variable "task_role_arn" {
  description = "Task role ARN (runtime AWS permissions)"
  type        = string
}

variable "log_group_name" {
  description = "CloudWatch log group name"
  type        = string
}

variable "aws_region" {
  description = "Region for the awslogs driver"
  type        = string
}

variable "assign_public_ip" {
  description = "Give the tasks a public IP (required for tasks in public subnets)"
  type        = bool
  default     = false
}

variable "service_registry_arn" {
  description = "Cloud Map service ARN, if the service is discoverable internally"
  type        = string
  default     = null
}

variable "health_check_command" {
  description = "Container-level health check command, if any"
  type        = list(string)
  default     = null
}
