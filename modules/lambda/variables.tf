variable "lambdas" {
  description = "dict of variables that are used for lambda functions"
  type = map(object({
    function_name      = optional(string)
    handler            = optional(string, "lambda_function.lambda_handler")
    memory_size        = optional(number)
    role               = optional(string)
    runtime            = optional(string, "python3.11")
    security_group_ids = optional(list(string), [])
    subnet_ids         = optional(list(string), [])
    timeout            = optional(number, 28)
    variables          = optional(map(string))
  }))
}
