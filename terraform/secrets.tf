# value is set out-of-band via put-secret-value so it never enters state or VCS
resource "aws_secretsmanager_secret" "openrouter_api_key" {
  name        = "${var.project}/openrouter-api-key"
  description = "OpenRouter API key used by the backend LLM client"
}
