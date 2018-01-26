from typing import List

import boto3
import io
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


def get_containers(event_json: dict) -> List[Container]:
    containers = []
    for container_json in event_json['detail']['containers']:
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


def update_zone(dns_name: str, resource_records: List[str]):
    changes = {
        'ResourceRecordSet': {
            'Name': dns_name
        }
    }

    if resource_records:
        # We have records
        changes['Action'] = 'UPSERT'
        changes['ResourceRecordSet']['Type'] = RECORD_TYPE
        changes['ResourceRecordSet']['TTL'] = TTL
        # changes['ResourceRecordSet']['MultiValueAnswer'] = \
        #     len(resource_records) > 1
        records = [{'Value': r} for r in resource_records]
        changes['ResourceRecordSet']['ResourceRecords'] = records
    else:
        changes['Action'] = 'DELETE'

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

    container_list = get_containers(event)
    host_ip = get_ecs_instance_ip(cluster_arn=cluster_arn,
                                  ecs_instance_arn=event['detail']['containerInstanceArn'])

    for container in container_list:
        # FQDN with trailing dot
        dns_name = container.name + '.' + DNS_ZONE + '.'
        current_hosts = get_resource_records(dns_name)

        if container.last_status == ContainerStatus.RUNNING:
            if host_ip in current_hosts:
                print(f'{dns_name} RUNNING and already in zone.')
            else:
                current_hosts.append(host_ip)
                print(f'{dns_name} RUNNING and not in zone yet, adding...')
                update_zone(dns_name, current_hosts)
        elif container.last_status == ContainerStatus.STOPPED:
            if host_ip in current_hosts:
                print(f'{dns_name} STOPPED and in zone, removing...')
                current_hosts.remove(host_ip)
                update_zone(dns_name, current_hosts)
            else:
                print(f'{dns_name} STOPPED and not in zone.')
        else:
            raise ValueError(f'Container status unknown: {container.last_status}')
