locals {
  account_id                  = data.aws_caller_identity.current.account_id
  region                      = "us-east-1"
  permission_boundary         = "arn:aws:iam::${local.account_id}:policy/SIPBIacSecurityDeploy"
  capitalized_repository_name = replace(title(replace(var.generic.project_name, "-", " ")), " ", "")

  project_name = {
    pascal = replace(title(var.generic.project_name), "-", "")
    snake  = replace(var.generic.project_name, "-", "_")
    spaced = replace(title(var.generic.project_name), "-", " ")
  }

}
data "aws_caller_identity" "current" {}
