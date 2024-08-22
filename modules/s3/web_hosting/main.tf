resource "aws_s3_bucket" "this" {
  #checkov:skip=CKV2_AWS_62
  #checkov:skip=CKV2_AWS_6
  #checkov:skip=CKV_AWS_18
  #checkov:skip=CKV_AWS_144
  #checkov:skip=CKV_AWS_21
  #checkov:skip=CKV_AWS_145
  #checkov:skip=CKV_AWS_20
  #checkov:skip=CKV2_AWS_61
  provider = aws.infra
  bucket   = "${var.generic.project_name}-web-hosting-${local.environment}"
}
resource "aws_s3_bucket_ownership_controls" "this" {
  #checkov:skip=CKV2_AWS_65
  provider = aws.infra
  bucket   = aws_s3_bucket.this.id
  rule {
    object_ownership = "BucketOwnerPreferred"
  }
}

resource "aws_s3_bucket_acl" "this" {
  provider = aws.infra
  bucket   = aws_s3_bucket.this.id
  acl      = "private"
}

resource "aws_cloudfront_origin_access_control" "this" {
  provider                          = aws.infra
  name                              = "${var.generic.policy_prefix}${local.project_name.pascal}-OAC"
  description                       = "DocuCredit Frontend OAC policy"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

resource "aws_cloudfront_distribution" "s3_distribution" {
  provider = aws.infra

  comment = "DocuCredit Frontend hosting distribution"

  dynamic "custom_error_response" {
    for_each = var.cloudfront.custom_error_responses
    content {
      error_code            = custom_error_response.value.error_code
      response_code         = custom_error_response.value.response_code
      response_page_path    = custom_error_response.value.response_page_path
      error_caching_min_ttl = custom_error_response.value.error_caching_min_ttl
    }
  }


  default_root_object = var.cloudfront.default_root_object
  # aliases = var.cloudfront.aliases
  enabled = true
  origin {
    domain_name              = aws_s3_bucket.this.bucket_regional_domain_name
    origin_access_control_id = aws_cloudfront_origin_access_control.this.id
    origin_id                = aws_s3_bucket.this.id
  }

  default_cache_behavior {
    cache_policy_id        = var.cloudfront.default_cache_behavior.cache_policy_id.CachingOptimized
    target_origin_id       = aws_s3_bucket.this.id
    viewer_protocol_policy = var.cloudfront.default_cache_behavior.viewer_protocol_policy
    allowed_methods        = var.cloudfront.default_cache_behavior.allowed_methods
    cached_methods         = var.cloudfront.default_cache_behavior.cached_methods
  }


  price_class = var.cloudfront.price_class
  restrictions {
    geo_restriction {
      restriction_type = var.cloudfront.restrictions.geo_restriction.restriction_type
      locations        = var.cloudfront.restrictions.geo_restriction.locations
    }
  }
  viewer_certificate {
    cloudfront_default_certificate = var.cloudfront.viewer_certificate.cloudfront_default_certificate
  }
}

resource "aws_s3_bucket_policy" "this" {
  bucket = aws_s3_bucket.this.id
  policy = templatefile(local.cloudfront.path, local.cloudfront.placeholder_mapping)
}

