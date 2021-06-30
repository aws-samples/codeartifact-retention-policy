module "codeartifact_retention_schedule" {
  source = "./schedule"

  count = length(var.repositories)

  repository_arn = var.repositories[count.index].repository_arn
  days_to_retain = var.repositories[count.index].days_to_retain
  lambda_arn = aws_lambda_function.codeartifact_retention.arn
}
