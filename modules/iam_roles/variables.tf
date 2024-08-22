variable "generic" {
  description = "general values for project"
  type = object({
    policy_prefix = string
    role_prefix   = string
    project_name  = string
  })
}

variable "security" {
  description = "Configuration for security policies, where keys can be any name, and the value is an object with path and placeholder mapping."
  type = map(object({
    path                = string
    placeholder_mapping = map(string)
  }))
}