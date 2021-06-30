import os
import re
import datetime
import json
import boto3

lambda_client = boto3.client("lambda")

PAGE_SIZE = 1000
FUNCTION_NAME = os.environ["AWS_LAMBDA_FUNCTION_NAME"]
KEEP_LATEST = os.environ["KEEP_LATEST"] == "true"


def lambda_handler(event, context):
    print("INPUT: {}".format(event))

    region, domain, repository = parse_repository_arn(event["repository_arn"])
    days_to_retain = event["days_to_retain"]

    if days_to_retain <= 0:
        print("ERROR: 'days_to_retain' parameter must be set to a positive number")
        return

    ca_client = boto3.client("codeartifact", region_name=region)

    if "package" in event.keys():
        package = event["package"]
        invocation_time = datetime.datetime.fromisoformat(event["invocation_time"])
        process_package_versions(ca_client, domain, repository, package, days_to_retain, invocation_time, KEEP_LATEST)
    else:
        invocation_time = datetime.datetime.now(tz=datetime.timezone.utc)
        packages = get_packages(ca_client, domain, repository)
        for p in packages:
            invoke_for_package(event, p, invocation_time)


def parse_repository_arn(arn):
    region, account, domain, repo = re.match(r"arn:[^:]+:codeartifact:([^:]+):(\d+):repository/([^\/]+)/([^\/]+)", arn).groups()
    return (region, domain, repo)


def get_packages(ca_client, domain, repository):
    params = {
        "domain": domain,
        "repository": repository,
        "maxResults": PAGE_SIZE
    }

    all_packages = []
    keep_fetching = True

    while keep_fetching:
        print(f"Fetching packages...")
        response = ca_client.list_packages(**params)

        if "packages" in response.keys():
            all_packages += response["packages"]

        if "nextToken" in response.keys():
            params["nextToken"] = response["nextToken"]
        else:
            keep_fetching = False

    print(f"Fetched {len(all_packages)} packages")

    return all_packages


def invoke_for_package(event, package, invocation_time):
    print(f"Invoking lambda for package: {package}")

    event_for_package = event.copy()
    event_for_package["package"] = package
    event_for_package["invocation_time"] = invocation_time.isoformat()

    response = lambda_client.invoke(
        FunctionName=FUNCTION_NAME,
        InvocationType="Event",
        Payload=json.dumps(event_for_package)
    )

    print(f"RESPONSE: {response}")


def process_package_versions(ca_client, domain, repository, package, days_to_retain, invocation_time, keep_latest):
    versions, latest_version = get_package_versions(ca_client, domain, repository, package)
    versions_to_delete = []

    for v in versions:
        print(f"VERSION: {v}")
        version = v["version"]

        if version == latest_version and keep_latest:
            continue

        info = describe_package_version(ca_client, domain, repository, package, version)

        if should_delete_package_version(info, days_to_retain, invocation_time):
            versions_to_delete.append(version)

    if len(versions_to_delete) > 0:
        delete_package_versions(ca_client, domain, repository, package, versions_to_delete)


def get_package_versions(ca_client, domain, repository, package):
    params = {
        "domain": domain,
        "repository": repository,
        "format": package["format"],
        "package": package["package"],
        "sortBy": "PUBLISHED_TIME",
        "maxResults": PAGE_SIZE,
    }

    if "namespace" in package.keys() and package["namespace"]:
        params["namespace"] = package["namespace"]

    all_versions = []
    keep_fetching = True
    latest_version = None

    while keep_fetching:
        print(f"Fetching versions...")
        response = ca_client.list_package_versions(**params)

        if "defaultDisplayVersion" in response.keys():
            latest_version = response["defaultDisplayVersion"]

        if "versions" in response.keys():
            all_versions += response["versions"]

        if "nextToken" in response.keys():
            params["nextToken"] = response["nextToken"]
        else:
            keep_fetching = False

    print(f"Fetched {len(all_versions)} versions")

    return all_versions, latest_version


def describe_package_version(ca_client, domain, repository, package, version):
    params = {
        "domain": domain,
        "repository": repository,
        "format": package["format"],
        "package": package["package"],
        "packageVersion": version,
    }

    if "namespace" in package.keys() and package["namespace"]:
        params["namespace"] = package["namespace"]

    response = ca_client.describe_package_version(**params)

    return response["packageVersion"]


def should_delete_package_version(version_info, days_to_retain, invocation_time):
    published_time = version_info["publishedTime"]
    age = invocation_time - published_time
    print(f"Package version age: {age}")
    return age > datetime.timedelta(days=days_to_retain)


def delete_package_versions(ca_client, domain, repository, package, versions_to_delete):
    print(f"Deleting package versions: {versions_to_delete}")

    params = {
        "domain": domain,
        "repository": repository,
        "format": package["format"],
        "package": package["package"],
        "versions": versions_to_delete,
    }

    if "namespace" in package.keys() and package["namespace"]:
        params["namespace"] = package["namespace"]

    response = ca_client.delete_package_versions(**params)
    print(f"RESPONSE: {response}")
