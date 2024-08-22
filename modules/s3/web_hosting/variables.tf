variable "generic" {
  description = "general values for project"
  type = object({
    policy_prefix = string
    role_prefix   = string
    project_name  = string
  })
}