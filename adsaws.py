# encoding: utf-8
"""
ADS AWS functions that collect the relevant information requested by the user
"""

from core import get_boto3_session
from errbot import BotPlugin, botcmd, arg_botcmd

class AdsAws(BotPlugin):
    """
    ADS AWS commands
    """
    @botcmd
    def aws(self, msg, args):
        """
        Get info on the ec2 instances
        :param msg: string
        :return: the corresponding info
        """
        help = '**ADS AWS Commands**\n'
        help += '> !aws ec2info*: get the status of all the ADS AWS EC2 instances\n'
        help += '> !aws ec2get*: get the property of an ADS AWS EC2 instance\n'
        help += '> !aws ecsclusters*: get a list of ECS clusters with their ARN\n'
        help += '> !aws ecsclusterinfo*: get a list of properties for a given ECS cluster\n'
        help += '> !aws ecsclusterinfo*: get status info for a given ECS cluster\n'
        return help

    @botcmd
    def aws_ec2info(self, msg, args):
        """
        :param msg: msg sent
        :param args: arguments passed
        Return the ec2 info for running instances
        """
        info = get_ec2_running()

        return_msg = '**ADS AWS EC2 Instances**\n'
        for instance in info:
            return_msg += '> {} is *{}*\n'.format(instance['tag'], instance['status'])

        return return_msg

    @botcmd
    def aws_ec2get(self, msg, args):
        """
        :param msg: msg sent
        :param args: arguments passed
        """

        args = args.split(' ')
        if len(args) != 2:
            return 'Malformed request: !aws ec2get <instance> <property> {}'.format(args)

        values = get_ec2_value(*args)

        return_msg = '**{}**\n'.format(args[0])
        for value in values:
            return_msg += '> {}: {}\n'.format(list(value.keys())[0], list(value.values())[0])

        return return_msg

    @botcmd
    def aws_ecsclusters(self, msg, args):
        """
        Return the ARNs for the ECS clusters
        """
        cluster_info = get_ecs_info()
        return_msg = '**ADS AWS ECS Clusters**\n'
        for entry in cluster_info.get('clusterArns'):
            return_msg += '> {}: {}\n'.format(entry.split('/')[1], entry)
        return return_msg

    @botcmd
    def aws_ecsclusterinfo(self, msg, args):
        """
        :param msg: msg sent
        :param args: arguments passed
        Return properties for a given ECS cluster
        """
        args = args.split(' ')
        if len(args) != 1:
            return 'Malformed request: !aws ecsclusterinfo <cluster name> {}'.format(args)
        cluster_info = get_ecs_details(*args)
        return_msg = '**{}**\n'.format(args[0])
        for entry in cluster_info.get('clusters'):
            if entry['clusterName'] != args[0]:
                continue
            return_msg += '>Status: {}\n'.format(entry['status'])
            return_msg += '>Number Registered Container Instances: {}\n'.format(entry['registeredContainerInstancesCount'])
            return_msg += '>Number Running Tasks: {}\n'.format(entry['runningTasksCount'])
            return_msg += '>Number Pending Tasks: {}\n'.format(entry['pendingTasksCount'])
            return_msg += '>Number Active Servies: {}\n'.format(entry['activeServicesCount'])
            
        return return_msg

    @botcmd
    def aws_ecsclusterstatus(self, msg, args):
        """
        :param msg: msg sent
        :param args: arguments passed
        Return properties for a given ECS clusters
        """
        args = args.split(' ')
        if len(args) != 1:
            return 'Malformed request: !aws ecsclusterinfo <cluster name> {}'.format(args)
        container_info = get_ecs_containers(*args)
        return_msg = '**Cluster Container info for: {}**\n'.format(args[0])
        for entry in container_info.get('containerInstances'):
            return_msg += '>Container: {}\n'.format(entry['containerInstanceArn'])
            return_msg += '>ec2InstanceId: {}\n'.format(entry['ec2InstanceId'])
            return_msg += '>Container status: {}\n'.format(entry['status'])
            return_msg += '>Docker version: {}\n'.format(entry['versionInfo']['dockerVersion'])
            return_msg += '>Agent version: {}\n'.format(entry['versionInfo']['agentVersion'])
            return_msg += '>Agent connected: {}\n'.format(entry['agentConnected'])
            return_msg += '>+++++++++++++++++++++++++++++++++++++++++++++\n'
        return return_msg

def get_ec2_running():
    """
    Get the tag and status for all of the EC2 instances
    """

    ec2 = get_boto3_session().client('ec2')

    ec2_output = []
    for reservation in ec2.describe_instances()['Reservations']:
        for instance in reservation['Instances']:

            instance_out = {
                'tag': [i.get('Value') for i in instance['Tags'] if i['Key'] == 'Name'][0],
                'status': instance['State']['Name']
            }

            ec2_output.append(instance_out)

    return ec2_output

def get_ec2_value(ec2_tag, ec2_value):
    """
    Get the IP (and other info) of a specific EC2 instance
    :param ec2_tag:
    :type ec2_tag: basestring

    :param ec2_value: value wanted, eg., ip
    :type ec2_value: basestring
    """

    synonym_list = {
        'ip': ['PublicIpAddress', 'PrivateIpAddress'],
        'publicipaddress': ['PublicIpAddress'],
        'privateipaddress': ['PrivateIpAddress']
    }

    ec2 = get_boto3_session().client('ec2')
    reservation = ec2.describe_instances(Filters=[{'Name': 'tag:Name', 'Values': [ec2_tag]}])

    values = []

    if ec2_value.lower() in synonym_list:
        keys = synonym_list[ec2_value.lower()]
    else:
        keys = [ec2_value]

    for key in synonym_list[ec2_value.lower()]:

        out_dict = {key: []}

        for instances in reservation['Reservations']:
            for instance in instances['Instances']:
                try:
                    out_dict[key].append(instance[key])
                except:
                    out_dict[key].append('NA')

        values.append(out_dict)

    return values

def get_ecs_info():
    client = get_boto3_session().client('ecs')
    result = client.list_clusters()
    return result

def get_ecs_details(name):
    client = get_boto3_session().client('ecs')
    result = client.describe_clusters(clusters=[name])
    return result

def get_ecs_containers(name):
    client = get_boto3_session().client('ecs')
    result = client.list_container_instances(cluster=name)
    containers = result.get('containerInstanceArns',[])
    container_info = client.describe_container_instances(cluster=name, containerInstances=containers)
    return container_info

if __name__ == '__main__':
    response = get_ec2_value('NAT', 'ip')

    print(response)
