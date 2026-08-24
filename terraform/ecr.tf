
data "aws_ecr_repository" "frontend" {
  name = "${var.project}/frontend"
}

data "aws_ecr_repository" "backend" {
  name = "${var.project}/backend"
}
