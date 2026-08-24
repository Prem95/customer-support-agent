# allowed CIDRs -> frontend:8080 -> backend:8000, each hop keyed to the previous SG

resource "aws_security_group" "frontend" {
  name_prefix = "${var.project}-frontend-"
  description = "Frontend tasks: reachable from the allowed ingress ranges only"
  vpc_id      = module.network.vpc_id

  ingress {
    description = "HTTP from allowed ranges"
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = var.allowed_ingress_cidrs
  }

  egress {
    description = "Backend calls and image/log egress"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_security_group" "backend" {
  name_prefix = "${var.project}-backend-"
  description = "Backend tasks: only reachable from frontend tasks"
  vpc_id      = module.network.vpc_id

  ingress {
    description     = "From frontend"
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.frontend.id]
  }

  egress {
    description = "OpenRouter API and image/log egress via NAT"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  lifecycle {
    create_before_destroy = true
  }
}
