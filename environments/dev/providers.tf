/*--------------------
  | Default Provider |
  --------------------*/
provider "aws" {
  region              = "us-east-1"
  profile             = "si-terraform-dev"
  allowed_account_ids = ["435713982138"]
}

/*----------------------------
  | Infraestructure Provider |
  ----------------------------*/
provider "aws" {
  region  = "us-east-1"
  alias   = "infrastructure"
  profile = "si-terraform-dev"

  assume_role {
    role_arn     = "arn:aws:iam::435713982138:role/SIRoleForInfraIacDeploy"
    session_name = "tf-infrastructure"
    external_id  = "tf-infrastructure"
  }

  default_tags {
    tags = {
      CreatedBy   = "terraform"
      handler     = "terraform"
      Project     = var.generic.project_name
      provider    = "infrastructure"
      environment = terraform.workspace
    }
  }
}


/*-----------------------
  | Networking Provider |
  -----------------------*/
provider "aws" {
  region  = "us-east-1"
  alias   = "network"
  profile = "si-terraform-dev"

  assume_role {
    role_arn    = "arn:aws:iam:435713982138:role/SIRoleForNetworkIacDeploy"
    external_id = "tf-network"
  }

  default_tags {
    tags = {
      CreatedBy   = "terraform"
      handler     = "terraform"
      Project     = var.generic.project_name
      provider    = "network"
      environment = terraform.workspace
    }
  }
}


/*---------------------
  | Security Provider |
  ---------------------*/
provider "aws" {
  region  = "us-east-1"
  alias   = "security"
  profile = "si-terraform-dev"

  assume_role {
    role_arn     = "arn:aws:iam::435713982138:role/SIRoleForSecurityIacDeploy"
    session_name = "tf-security"
    external_id  = "tf-security"
  }

  default_tags {
    tags = {
      CreatedBy   = "terraform"
      handler     = "terraform"
      Project     = var.generic.project_name
      provider    = "security"
      environment = terraform.workspace
    }
  }
}
