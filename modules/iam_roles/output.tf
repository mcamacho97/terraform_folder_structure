output "arn" {
  value = { for key, role in aws_iam_role.this : key => role.arn }
}