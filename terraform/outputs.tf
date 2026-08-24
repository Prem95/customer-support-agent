# The frontend task gets a new public IP each time ECS replaces it, so the URL
# cannot be a static output. This command gives the current address.
output "application_url_command" {
  description = "Command that prints the current URL of the support console"
  value       = <<-EOT
    aws ecs list-tasks --cluster ${aws_ecs_cluster.this.name} --service-name ${module.frontend_service.service_name} --query 'taskArns[0]' --output text \
      | xargs -I {} aws ecs describe-tasks --cluster ${aws_ecs_cluster.this.name} --tasks {} --query 'tasks[0].attachments[0].details[?name==`networkInterfaceId`].value' --output text \
      | xargs -I {} aws ec2 describe-network-interfaces --network-interface-ids {} --query 'NetworkInterfaces[0].Association.PublicIp' --output text \
      | xargs -I {} echo "http://{}:8080"
  EOT
}

output "ecr_frontend_repository_url" {
  description = "ECR repository for frontend images"
  value       = data.aws_ecr_repository.frontend.repository_url
}

output "ecr_backend_repository_url" {
  description = "ECR repository for backend images"
  value       = data.aws_ecr_repository.backend.repository_url
}

output "ecs_cluster_name" {
  description = "ECS cluster name (used by CI/CD for deployments)"
  value       = aws_ecs_cluster.this.name
}

output "openrouter_secret_arn" {
  description = "Secrets Manager ARN to populate with the OpenRouter API key"
  value       = aws_secretsmanager_secret.openrouter_api_key.arn
}
