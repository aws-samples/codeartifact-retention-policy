data "archive_file" "codeartifact_retention_lambda_zip" {
  type = "zip"
  source_dir = "${path.module}/lambda"
  output_path = "codeartifact-retention-lambda.zip"
}

resource "aws_lambda_function" "codeartifact_retention" {
  function_name = "codeartifact-retention"
  filename = data.archive_file.codeartifact_retention_lambda_zip.output_path
  source_code_hash = data.archive_file.codeartifact_retention_lambda_zip.output_base64sha256
  handler = "main.lambda_handler"
  runtime = "python3.8"
  timeout = 60
  role = aws_iam_role.codeartifact_retention.arn

  environment {
    variables = {
      KEEP_LATEST = var.keep_latest
    }
  }
}

resource "aws_iam_role" "codeartifact_retention" {
  name = "codeartifact-retention"
  assume_role_policy = data.aws_iam_policy_document.codeartifact_retention_assume_role.json
}

data "aws_iam_policy_document" "codeartifact_retention_assume_role" {
  statement {
    effect = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role_policy_attachment" "attach_basic_lambda_policies_to_codeartifact_retention" {
  role = aws_iam_role.codeartifact_retention.id
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "codeartifact_retention" {
  name = "codeartifact-retention"
  role = aws_iam_role.codeartifact_retention.id
  policy = data.aws_iam_policy_document.codeartifact_retention.json
}

data "aws_iam_policy_document" "codeartifact_retention" {
  statement {
    effect = "Allow"
    actions = [
      "lambda:InvokeFunction"
    ]
    resources = [
      aws_lambda_function.codeartifact_retention.arn
    ]
  }
  statement {
    effect = "Allow"
    actions = [
      "codeartifact:ListPackages"
    ]
    resources = var.repositories[*].repository_arn
  }
  statement {
    effect = "Allow"
    actions = [
      "codeartifact:ListPackageVersions",
      "codeartifact:DescribePackageVersion",
      "codeartifact:DeletePackageVersions"
    ]
    resources = [
      for r in var.repositories : "${replace(r.repository_arn, ":repository/", ":package/")}/*"
    ]
  }
}
