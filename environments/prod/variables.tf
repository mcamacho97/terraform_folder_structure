variable "generic" {
  description = "general values for project"
  type = object({
    policy_prefix = string
    role_prefix   = string
    project_name  = string
  })
}

variable "codebuild" {
  description = "value of codebuild"
  type = object({
    buildspec_path = string
    description    = string
    build_timeout  = number
    artifacts = object({
      type = string
    })
    environment = object({
      compute_type                = string
      image                       = string
      type                        = string
      image_pull_credentials_type = string
    })
    logs_config = object({
      cloudwatch_logs = object({
        group_name = string
      })
    })
    source = object({
      type            = string
      location        = string
      git_clone_depth = number
    })
    source_version = string
  })
}