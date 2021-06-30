# CodeArtifact Retention Policy

[AWS CodeArtifact](https://aws.amazon.com/codeartifact/) doesn't provide an option to configure retention policy for artifacts published in the repositories.
This solution offers a workaround, which relies on [AWS Lambda](https://aws.amazon.com/lambda/) and [Amazon EventBridge](https://aws.amazon.com/eventbridge/), to periodically (every 24h) scan the repositories and delete artifact versions older than the configured retention period.

The solution is implemented as a [Terraform](https://www.terraform.io/) module, which can be deployed to an AWS account.


## Usage

```terraform
module "codeartifact_retention" {
  source = "../codeartifact-retention-module"

  keep_latest = false

  repositories = [
    {
      repository_arn = "arn:aws:codeartifact:us-east-1:XXXXXXXXXXXX:repository/my-domain/my-repo-1"
      days_to_retain = 7
    },
    {
      repository_arn = "arn:aws:codeartifact:us-east-1:XXXXXXXXXXXX:repository/my-domain/my-repo-2"
      days_to_retain = 30
    }
  ]
}
```

An example showing how to use the module can be seen in the [`example`](./example) module, where retention policy is configured for two repositories.

If you deploy the example module, you can publish some artifacts to the created repositories. After specified number of days (check the values set for `days_to_retain` in example module), published artifact versions will be deleted.

By default, the latest published package version will not be deleted, despite the policy setting. If you want to delete the latest package version as well, set `keep_latest` module variable to `false`.


## Deploying Example Module

Prerequisites:

- `terraform` executable is available in the `PATH`.

- Region is set:
    ```bash
    export AWS_REGION="us-east-1"
    ```

- AWS credentials are set, which can be done in one of the following ways:

    - If the credentials are configured in the `~/.aws/credentials` file, export the `AWS_PROFILE` environment variable referencing the profile you want to use:
        ```bash
        export AWS_PROFILE="MyProfileName"
        ```

    - Otherwise, if you have access key and secret access key, you can export them directly:
        ```bash
        export AWS_ACCESS_KEY_ID=...
        export AWS_SECRET_ACCESS_KEY=...
        ```
Example module can be deployed by navigating to its directory and executing following commands:

```bash
terraform init
terraform apply
```

To remove the deployed resources, run:

```bash
terraform destroy
```
