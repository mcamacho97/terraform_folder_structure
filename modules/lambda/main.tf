/*-------------
  | Resources |
  -------------*/
resource "aws_iam_role" "lambda" {
  for_each = local.lambda_role_path

  name                 = local.lambda_role_name[each.key]
  assume_role_policy   = local.lambda_role_trusted_policy[each.key]
  managed_policy_arns  = local.lambda_managed_policies
  permissions_boundary = local.permissions_boundary

  inline_policy {
    name   = local.lambda_policy_name[each.key]
    policy = templatefile("${each.value}policy.json", { region = local.region, account_id = local.account_id, s3_bucket = aws_s3_bucket.izum.bucket })
  }

  provider = aws.security
}

data "archive_file" "lambda" {
  for_each = var.lambdas

  output_file_mode = "0666"
  output_path      = "./files/${each.key}_package.zip"
  source_dir       = "./src/lambda/${each.key}/src"
  type             = "zip"
}

resource "aws_lambda_function" "this" {
  #checkov:skip=CKV_AWS_50: X-Ray tracing is enabled for Lambda
  #checkov:skip=CKV_AWS_115: Ensure that AWS Lambda function is configured for function-level concurrent execution limit
  #checkov:skip=CKV_AWS_116: Ensure that AWS Lambda function is configured for a Dead Letter Queue(DLQ)
  #checkov:skip=CKV_AWS_173: Check encryption settings for Lambda environmental variable
  #checkov:skip=CKV_AWS_272: Ensure AWS Lambda function is configured to validate code-signing
  for_each = var.lambdas

  filename         = "./files/${each.key}_package.zip"
  function_name    = local.lambda_names[each.key]
  handler          = each.value.handler
  layers           = ["arn:aws:lambda:us-east-1:017000801446:layer:AWSLambdaPowertoolsPythonV2:69", "arn:aws:lambda:us-east-1:336392948345:layer:AWSSDKPandas-Python311:12", "arn:aws:lambda:us-east-1:770693421928:layer:Klayers-p312-Pillow:2"]
  memory_size      = each.value.memory_size
  role             = coalesce(each.value.role, aws_iam_role.lambda[each.key].arn)
  runtime          = each.value.runtime
  source_code_hash = data.archive_file.lambda[each.key].output_base64sha256
  timeout          = each.value.timeout

  environment {
    variables = { for k, v in each.value.variables : k => replace(v, "{default}", terraform.workspace) }
  }

  vpc_config {
    security_group_ids = each.value.security_group_ids
    subnet_ids         = each.value.subnet_ids
  }

  provider = aws.infrastructure
}

resource "aws_lambda_permission" "get_list_files" {
  statement_id  = "AllowIzumAPIListFilesGetInvoke"
  action        = "lambda:InvokeFunction"
  function_name = element(split(":", aws_lambda_function.this["izum-list-objects"].arn), 6)
  principal     = "apigateway.amazonaws.com"

  # The /* part allows invocation from any stage, method and resource path
  # within API Gateway.
  source_arn = "${aws_api_gateway_rest_api.this.execution_arn}/*/GET/list-files"
  provider   = aws.infrastructure
}

resource "aws_lambda_permission" "get_presigned_url" {
  statement_id  = "AllowIzumAPIPresignedUrlGetInvoke"
  action        = "lambda:InvokeFunction"
  function_name = element(split(":", aws_lambda_function.this["izum-presigned-url"].arn), 6)
  principal     = "apigateway.amazonaws.com"

  # The /* part allows invocation from any stage, method and resource path
  # within API Gateway.
  source_arn = "${aws_api_gateway_rest_api.this.execution_arn}/*/GET/presigned-url"
  provider   = aws.infrastructure
}

resource "aws_lambda_permission" "put_presigned_url" {
  statement_id  = "AllowIzumAPIPresignedUrlPutInvoke"
  action        = "lambda:InvokeFunction"
  function_name = element(split(":", aws_lambda_function.this["izum-presigned-url"].arn), 6)
  principal     = "apigateway.amazonaws.com"

  # The /* part allows invocation from any stage, method and resource path
  # within API Gateway.
  source_arn = "${aws_api_gateway_rest_api.this.execution_arn}/*/PUT/presigned-url"
  provider   = aws.infrastructure
}

resource "aws_lambda_permission" "post_list_files" {
  statement_id  = "AllowIzumAPIRunStepPostInvoke"
  action        = "lambda:InvokeFunction"
  function_name = element(split(":", aws_lambda_function.this["izum-run-step"].arn), 6)
  principal     = "apigateway.amazonaws.com"

  # The /* part allows invocation from any stage, method and resource path
  # within API Gateway.
  source_arn = "${aws_api_gateway_rest_api.this.execution_arn}/*/POST/list-files"
  provider   = aws.infrastructure
}

resource "aws_lambda_permission" "allow_bucket" {
  statement_id  = "AllowS3Invoke"
  action        = "lambda:InvokeFunction"
  function_name = element(split(":", aws_lambda_function.this["izum-compress-images"].arn), 6)
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.izum.arn
  provider      = aws.infrastructure
}

resource "aws_lambda_permission" "delete_files" {
  statement_id  = "AllowIzumAPIRunStepPostInvoke"
  action        = "lambda:InvokeFunction"
  function_name = element(split(":", aws_lambda_function.this["izum-delete-objects"].arn), 6)
  principal     = "apigateway.amazonaws.com"

  # The /* part allows invocation from any stage, method and resource path
  # within API Gateway.
  source_arn = "${aws_api_gateway_rest_api.this.execution_arn}/*/DELETE/files"
  provider   = aws.infrastructure
}


