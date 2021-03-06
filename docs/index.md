# Cloudsplaining

[Cloudsplaining](https://github.com/salesforce/cloudsplaining) identifies violations of least privilege in AWS IAM and generates a risk-prioritized HTML report with a triage worksheet.

![](_images/cloudsplaining-report.gif)

## Commands

* `cloudsplaining download` - Download IAM authorization details for an entire AWS account.
* `cloudsplaining create-exclusions-file` - Create an exclusions file to filter out false positives specific to your context.
* `cloudsplaining scan` - Scan the IAM authorization details file; generate an HTML report and a triage worksheet.
* `cloudsplaining scan-policy-file` - Scan a single IAM policy file
* `cloudsplaining --help` - Print help messages and exit.



### Scanning an entire AWS Account

#### Downloading Account Authorization Details

We can scan an entire AWS account and generate reports. To do this, we leverage the AWS IAM [get-account-authorization-details](https://docs.aws.amazon.com/cli/latest/reference/iam/get-account-authorization-details.html) API call, which downloads a large JSON file (around 100KB per account) that contains all of the IAM details for the account. This includes data on users, groups, roles, customer-managed policies, and AWS-managed policies.

* You must have AWS credentials configured that can be used by the CLI.

* You must have the privileges to run [iam:GetAccountAuthorizationDetails](https://docs.aws.amazon.com/IAM/latest/APIReference/API_GetAccountAuthorizationDetails.html). The `arn:aws:iam::aws:policy/SecurityAudit` policy includes this, as do many others that allow Read access to the IAM Service.

* To download the account authorization details, ensure you are authenticated to AWS, then run `cloudsplaining`'s `download` command:

```bash
cloudsplaining download
```

* If you prefer to use your `~/.aws/credentials` file instead of environment variables, you can specify the profile name:

```bash
cloudsplaining download --profile myprofile
```

It will download a JSON file in your current directory that contains your account authorization detail information.

#### Create Exclusions file

Cloudsplaining tool does not attempt to understand the context behind everything in your AWS account. It's possible to understand the context behind some of these things programmatically - whether the policy is applied to an instance profile, whether the policy is attached, whether inline IAM policies are in use, and whether or not AWS Managed Policies are in use. **Only you know the context behind the design of your AWS infrastructure and the IAM strategy**.

As such, it's important to eliminate False Positives that are context-dependent. You can do this with an exclusions file. We've included a command that will generate an exclusions file for you so you don't have to remember the required format.

You can create an exclusions template via the following command:

```bash
cloudsplaining create-exclusions-file
```

This will generate a file in your current directory titled `exclusions.yml`.

Now when you run the `scan` command, you can use the exclusions file like this:

```bash
cloudsplaining scan --exclusions-file exclusions.yml --input-file examples/files/example.json --output examples/files/
```

For more information on the structure of the exclusions file, see [Filtering False Positives](#filtering-false-positives)

#### Scanning the Authorization Details file

Now that we've downloaded the account authorization file, we can scan *all* of the AWS IAM policies with `cloudsplaining`.

Run the following command:

```bash
cloudsplaining scan --exclusions-file exclusions.yml --input-file examples/files/example.json --output examples/files/
```

It will create an HTML report like [this](https://opensource.salesforce.com/cloudsplaining/):

> ![](docs/_images/cloudsplaining-report.gif)


It will also create a raw JSON data file:

* `default-iam-results.json`: This contains the raw JSON output of the report. You can use this data file for operating on the scan results for various purposes. For example, you could write a Python script that parses this data and opens up automated JIRA issues or Salesforce Work Items. An example entry is shown below. The full example can be viewed at [examples/output/example-authz-details-results.json](examples/files/iam-results-example.json)

```json
{
    "example-authz-details": [
        {
            "AccountID": "012345678901",
            "ManagedBy": "Customer",
            "PolicyName": "InsecureUserPolicy",
            "Arn": "arn:aws:iam::012345678901:user/userwithlotsofpermissions",
            "ActionsCount": 2,
            "ServicesCount": 1,
            "Actions": [
                "s3:PutObject",
                "s3:PutObjectAcl"
            ],
            "Services": [
                "s3"
            ]
        }
    ]
}
```


See the [examples/files](examples/files) folder for sample output.

#### Filtering False Positives

Resource constraints are best practice - especially for system roles/instance profiles - but sometimes, these are by design. For example, consider a situation where a custom IAM policy is used on an instance profile for an EC2 instance that provisions Terraform. *In this case, broad permissions are design requirements* - so we don't want to include these in the results.

You can create an exclusions template via the following command:

```bash
cloudsplaining create-exclusions-file
```

This will generate a file in your current directory titled `exclusions.yml`.

The default exclusions file looks like this:

```yaml
# Policy names to exclude from evaluation
# Suggestion: Add policies here that are known to be overly permissive by design, after you run the initial report.
policies:
  - "AWSServiceRoleFor*"
  - "*ServiceRolePolicy"
  - "*ServiceLinkedRolePolicy"
  - "AdministratorAccess" # Otherwise, this will take a long time
  - "service-role*"
  - "aws-service-role*"
# Don't evaluate these roles, users, or groups as part of the evaluation
roles:
  - "service-role*"
  - "aws-service-role*"
users:
  - ""
groups:
  - ""
# Read-only actions to include in the results, such as s3:GetObject
# By default, it includes Actions that could lead to Data Leaks
include-actions:
  - "s3:GetObject"
  - "ssm:GetParameter"
  - "ssm:GetParameters"
  - "ssm:GetParametersByPath"
  - "secretsmanager:GetSecretValue"
# Write actions to include from the results, such as kms:Decrypt
exclude-actions:
  - ""
```

* Make any additions or modifications that you want.
  * Under `policies`, list the path of policy names that you want to exclude.
  * If you want to exclude a role titled `MyRole`, list `MyRole` or `MyR*` in the `roles` list.
  * You can follow the same approach for `users` and `groups` list.

Now when you run the `scan` command, you can use the exclusions file like this:

```bash
cloudsplaining scan --exclusions-file exclusions.yml --input-file examples/files/example.json --output examples/files/
```
