/*--------------------
  | Default Provider |
  --------------------*/
provider "aws" {
  region              = "us-east-1"
  profile             = "si-terraform-prod"
  allowed_account_ids = ["762630516372"]
}

/*----------------------------
  | Infraestructure Provider |
  ----------------------------*/
provider "aws" {
  region  = "us-east-1"
  alias   = "infrastructure"
  profile = "si-terraform-prod"

  assume_role {
    role_arn     = "arn:aws:iam::762630516372:role/SIRoleForInfraIacDeploy"
    session_name = "tf-infrastructure"
    external_id  = "tf-infrastructure"
  }

  default_tags {
    tags = {
      CreatedBy   = "terraform"
      handler     = "terraform"
      Project     = var.generic.project_name
      provider    = "infrastructure"
    }
  }
}


/*-----------------------
  | Networking Provider |
  -----------------------*/
provider "aws" {
  region  = "us-east-1"
  alias   = "network"
  profile = "si-terraform-prod"

  assume_role {
    role_arn    = "arn:aws:iam:762630516372:role/SIRoleForNetworkIacDeploy"
    external_id = "tf-network"
  }

  default_tags {
    tags = {
      CreatedBy   = "terraform"
      handler     = "terraform"
      Project     = var.generic.project_name
      provider    = "network"
    }
  }
}


/*---------------------
  | Security Provider |
  ---------------------*/
provider "aws" {
  region  = "us-east-1"
  alias   = "security"
  profile = "si-terraform-prod"

  assume_role {
    role_arn     = "arn:aws:iam::762630516372:role/SIRoleForSecurityIacDeploy"
    session_name = "tf-security"
    external_id  = "tf-security"
  }

  default_tags {
    tags = {
      CreatedBy   = "terraform"
      handler     = "terraform"
      Project     = var.generic.project_name
      provider    = "security"
    }
  }
}
