data "aws_secretsmanager_secret" "openrouter_api_key" {
  name = "${var.project}/openrouter-api-key"
}
