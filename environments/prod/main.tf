terraform {
  required_version = ">= 1.3.8"
  backend "s3" {
    bucket  = "terraform-states-projects-prod"
    key     = "workshop/terraform.tfstate"
    region  = "us-east-1"
    profile = "si-terraform-prod"
    encrypt = true
  }

  required_providers {
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.4.1"
    }

    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
      configuration_aliases = [
        aws.infrastructure,
        aws.network,
        aws.security,
      ]
    }
  }
}

module "roles" {
  providers           = { aws.security = aws.security }
  source              = "../../modules/iam_roles"
  generic             = var.generic
  security = {
    "codebuild" = {
      path = "./src/codebuild/permissions/policy.json"
      placeholder_mapping = {
        account_id          = "435713982138"
        region              = "us-east-1"
        project             = var.generic.project_name
        hosting_bucket_name = "bucket"
        cloudfront          = "dasadad"
        # hosting_bucket_name = aws_s3_bucket.this.id
        # cloudfront          = aws_cloudfront_distribution.s3_distribution.id
      }
    }
  }
}

module "codebuild" {
  providers         = { aws.infrastructure = aws.infrastructure }
  source            = "../../modules/codebuild"
  generic           = var.generic
  codebuild         = var.codebuild
  name              = var.generic.project_name
  service_role      = module.roles.arn["codebuild"]
  buildspec_configs = { hosting_bucket_name = "bucket", distribution_id = "asaskajs" }
}

