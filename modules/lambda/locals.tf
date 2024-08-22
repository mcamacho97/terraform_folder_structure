/*----------
  | Locals |
  ----------*/
locals {
  lambda_names = {
    for key, value in var.lambdas :
    key => coalesce(
      value.function_name,
      "${key}${
        var.generic.use_env_suffix
        ? "-${terraform.workspace}"
        : ""
      }"
    )
  }

  lambda_managed_policies = [
    for value in split(",", var.generic.lambda_managed_policies) :
    "arn:aws:iam::aws:policy/service-role/${value}"
  ]

  lambda_policy_name = {
    for key, value in var.lambdas :
    key => "${var.generic.policy_prefix}${
      var.generic.use_env_suffix
      ? title(terraform.workspace)
      : ""
    }${title(key)}Lambda"
  }

  lambda_role_name = {
    for key, value in var.lambdas :
    key => "${var.generic.role_prefix}${
      var.generic.use_env_suffix
      ? title(terraform.workspace)
      : ""
    }${title(key)}Lambda"
  }



  lambda_role_path = {
    for key in keys(var.lambdas) :
    key =>
    "./src/lambda/${key}/permissions/" if fileexists("./src/lambda/${key}/permissions/policy.json")
  }

  lambda_role_trusted_policy = {
    for key, value in local.lambda_role_path :
    key => (
      fileexists("${value}trusted_entities.json")
      ? file("${value}trusted_entities.json")
      : jsonencode({
        "Statement" : [
          {
            "Sid" : "AsumeRoleForLambda"
            "Action" : "sts:AssumeRole",
            "Effect" : "Allow",
            "Principal" : { "Service" : "lambda.amazonaws.com" }
          }
        ],
        "Version" : "2012-10-17"
      })
    )
  }
}