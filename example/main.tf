resource "aws_kms_key" "code_artifact_encryption_key" {
  description = "Encryption key used for CodeArtifact"
}

resource "aws_codeartifact_domain" "my_domain" {
  domain = "my-domain"
  encryption_key = aws_kms_key.code_artifact_encryption_key.arn
}

resource "aws_codeartifact_repository" "my_repo_1" {
  repository = "my-repo-1"
  domain = aws_codeartifact_domain.my_domain.domain
}

resource "aws_codeartifact_repository" "my_repo_2" {
  repository = "my-repo-2"
  domain = aws_codeartifact_domain.my_domain.domain
}

module "codeartifact_retention" {
  source = "../codeartifact-retention-module"

  keep_latest = false

  repositories = [
    {
      repository_arn = aws_codeartifact_repository.my_repo_1.arn
      days_to_retain = 1
    },
    {
      repository_arn = aws_codeartifact_repository.my_repo_2.arn
      days_to_retain = 3
    }
  ]
}
