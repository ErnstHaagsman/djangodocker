from functools import lru_cache
from typing import List, Set

import boto3
import json

# Configuration
CLUSTER_NAME = 'djangotodo'
DNS_ZONE = 'todo.ernsthaagsman.com'
HOSTED_ZONE_ID = '/hostedzone/Z2BI37M7SUW4E4'
EVENT_NAME = 'ECS Task State Change'
RECORD_TYPE = 'A'
TTL = 30


class Container:
    def __init__(self, containerArn, lastStatus, name, taskArn):
        self.container_arn = containerArn
        self.last_status = lastStatus
        self.name = name
        self.task_arn = taskArn


class ContainerStatus:
    STOPPED = 'STOPPED'
    RUNNING = 'RUNNING'
    PENDING = 'PENDING'


def get_task_ids(family: str) -> List[str]:
    client = boto3.client('ecs')
    tasks = client.list_tasks(
        cluster=CLUSTER_NAME,
        family=family
    )

    # Insurance in case someone uses this script for very large clusters
    if 'nextToken' in tasks:
        raise Exception(f"{family} has more than 100 tasks, please change "
                        "the script to be able to handle nextToken.")

    return tasks['taskArns']


def get_task_descriptions(task_ids: List[str]):
    if not task_ids:
        return []

    client = boto3.client('ecs')
    tasks = client.describe_tasks(
        cluster=CLUSTER_NAME,
        tasks=task_ids
    )

    if tasks['failures']:
        print('Failures encountered while getting task descriptions:')
        print(json.dumps(tasks['failures'], indent=4))
        print('***************')

    return tasks['tasks']


def get_containers(task: dict) -> List[Container]:
    containers = []
    for container_json in task['containers']:
        containers.append(Container(
            container_json['containerArn'],
            container_json['lastStatus'],
            container_json['name'],
            container_json['taskArn']
        ))
    return containers


def get_ec2_id(cluster_arn: str, ecs_instance_arn: str) -> str:
    ecs_client = boto3.client('ecs')
    description = ecs_client.describe_container_instances(
        cluster=cluster_arn,
        containerInstances=[ecs_instance_arn]
    )

    # Zeroth index because we only requested a single instance's information
    # but the API call supports requesting more
    ecs_instance = description['containerInstances'][0]
    return ecs_instance['ec2InstanceId']


def get_ec2_instance_ip(ec2_instance_id: str) -> str:
    ec2 = boto3.resource('ec2')
    instance = ec2.Instance(ec2_instance_id)
    return instance.private_ip_address


@lru_cache(maxsize=128)
def get_ecs_instance_ip(cluster_arn: str, ecs_instance_arn: str) -> str:
    return get_ec2_instance_ip(get_ec2_id(cluster_arn, ecs_instance_arn))


def get_resource_records(dns_name: str) -> List[str]:
    r53_client = boto3.client('route53')
    zone = r53_client.list_resource_record_sets(
        HostedZoneId=HOSTED_ZONE_ID,
        StartRecordType=RECORD_TYPE,
        StartRecordName=dns_name,
        MaxItems='1'
    )

    if not zone['ResourceRecordSets']:
        return []

    # Taking the 0th ResourceRecordSet, as the API supports returning more,
    # but we're only requesting one.
    resource_records = zone['ResourceRecordSets'][0]['ResourceRecords']
    return [record['Value'] for record in resource_records]


def update_zone(dns_name: str, resource_records: Set[str]):
    changes = {
        'ResourceRecordSet': {
            'Name': dns_name,
            'Type': RECORD_TYPE
        }
    }

    if resource_records:
        # We have records
        changes['Action'] = 'UPSERT'
        changes['ResourceRecordSet']['TTL'] = TTL
    else:
        changes['Action'] = 'DELETE'

        # Amazon wants us to specify what the records used to be in this case
        resource_records = get_resource_records(dns_name)

    records = [{'Value': r} for r in resource_records]
    changes['ResourceRecordSet']['ResourceRecords'] = records

    r53_client = boto3.client('route53')
    r53_client.change_resource_record_sets(
        HostedZoneId=HOSTED_ZONE_ID,
        ChangeBatch={
            'Comment': 'Automated change through Lambda',
            'Changes': [changes]
        }
    )


def lambda_handler(event, context):
    # First, print event for troubleshooting
    print('*****EVENT*****')
    print(json.dumps(event, indent=4, sort_keys=True))
    print('***************\n\n')

    # Verify event
    detail_type = event['detail-type']
    if detail_type != EVENT_NAME:
        raise ValueError(f"Unsupported event type: {detail_type}")

    cluster_arn = event['detail']['clusterArn']
    cluster_name = cluster_arn.split('/')[1]
    if cluster_name != CLUSTER_NAME:
        raise ValueError(f"Cluster not configured: {cluster_name}")

    # Refresh the DNS record for the task that was just changed
    # First, get all tasks for the family of the changed task
    task_def_arn = event['detail']['taskDefinitionArn']

    # The ARN is formatted as:
    # arn:aws:ecs:region:account:taskdefinition/family:revision
    task_revision = task_def_arn.split('/')[1]
    task_family = task_revision.split(':')[0]

    # Get the task objects for all active tasks for this definition
    task_ids = get_task_ids(family=task_family)
    tasks = get_task_descriptions(task_ids)

    container_ips = {}

    # First get the names of any containers listed in the event, in case
    # they were stopped, and we didn't find active tasks. They should still
    # be removed from DNS
    for container in get_containers(event['detail']):
        dns_name = container.name + '.' + DNS_ZONE + '.'
        if dns_name not in container_ips:
            container_ips[dns_name] = set()

    # Now iterate through the found tasks, and build a mapping of name to IP
    # addresses
    for task in tasks:
        if task['clusterArn'] != cluster_arn:
            continue

        container_list = get_containers(task)
        host_ip = get_ecs_instance_ip(cluster_arn=cluster_arn,
                                      ecs_instance_arn=task['containerInstanceArn'])

        for container in container_list:
            dns_name = container.name + '.' + DNS_ZONE + '.'

            if dns_name not in container_ips:
                container_ips[dns_name] = set()

            # Only check for RUNNING after adding the DNS name to the dict,
            # to make sure that any service with no active containers will
            # get its DNS records removed
            if container.last_status == ContainerStatus.RUNNING:
                container_ips[dns_name].add(host_ip)

    # Update DNS records for all containers
    for dns_name in container_ips:
        print(f'Updating {dns_name}, new IPs: {container_ips[dns_name]}')
        update_zone(dns_name, container_ips[dns_name])
