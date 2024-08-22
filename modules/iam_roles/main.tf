resource "aws_iam_policy" "this" {
  provider = aws.security
  for_each = var.security
  name     = "${var.generic.policy_prefix}${title(each.key)}${local.project_name.pascal}"
  path     = "/"
  policy   = templatefile(each.value.path, each.value.placeholder_mapping)
}

resource "aws_iam_role" "this" {
  provider           = aws.security
  for_each           = var.security
  name               = "${var.generic.role_prefix}${title(each.key)}${local.project_name.pascal}"
  assume_role_policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "${each.key}.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
EOF

  permissions_boundary = local.permission_boundary
}

resource "aws_iam_role_policy_attachment" "this" {
  provider   = aws.security
  for_each   = var.security
  role       = aws_iam_role.this[each.key].name
  policy_arn = aws_iam_policy.this[each.key].arn
}
