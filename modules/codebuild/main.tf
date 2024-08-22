resource "aws_codebuild_project" "this" {
  #checkov:skip=CKV_AWS_147
  provider      = aws.infrastructure
  name          = var.name
  description   = var.codebuild.description
  build_timeout = var.codebuild.build_timeout
  service_role  = var.service_role

  artifacts {
    type = var.codebuild.artifacts.type
  }

  environment {
    compute_type                = var.codebuild.environment.compute_type
    image                       = var.codebuild.environment.image
    type                        = var.codebuild.environment.type
    image_pull_credentials_type = var.codebuild.environment.image_pull_credentials_type
  }

  logs_config {
    cloudwatch_logs {
      group_name = replace(var.codebuild.logs_config.cloudwatch_logs.group_name, "{project}", var.name)
    }
  }
  source {
    type            = var.codebuild.source.type
    location        = var.codebuild.source.location
    git_clone_depth = var.codebuild.source.git_clone_depth
    buildspec       = templatefile(var.codebuild.buildspec_path, var.buildspec_configs)
  }

  source_version = var.codebuild.source_version
}
