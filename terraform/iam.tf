data "aws_iam_policy_document" "ecs_tasks_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

# execution roles are split so only the backend can read the LLM secret

resource "aws_iam_role" "frontend_execution" {
  name               = "${var.project}-frontend-execution"
  assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume.json
}

resource "aws_iam_role" "backend_execution" {
  name               = "${var.project}-backend-execution"
  assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume.json
}

resource "aws_iam_role_policy_attachment" "frontend_execution" {
  role       = aws_iam_role.frontend_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role_policy_attachment" "backend_execution" {
  role       = aws_iam_role.backend_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

data "aws_iam_policy_document" "backend_secrets" {
  statement {
    actions   = ["secretsmanager:GetSecretValue"]
    resources = [aws_secretsmanager_secret.openrouter_api_key.arn]
  }
}

resource "aws_iam_role_policy" "backend_secrets" {
  name   = "read-openrouter-secret"
  role   = aws_iam_role.backend_execution.id
  policy = data.aws_iam_policy_document.backend_secrets.json
}

# the app itself calls no AWS APIs, so the task role stays empty
resource "aws_iam_role" "task" {
  name               = "${var.project}-task"
  assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume.json
}
