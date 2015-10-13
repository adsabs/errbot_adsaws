# encoding: utf-8
import boto3
import unittest
from mock import patch
from moto import mock_ec2
from adsaws import get_ec2_running, get_ec2_value, get_ecs_info, get_ecs_details, get_ecs_containers
from adsaws import AdsAws
from boto3.session import Session

class TestAdsAws(unittest.TestCase):
    """
    Tests the plugins for the ADS AWS methods
    """

    @mock_ec2
    def test_can_get_aws_ec2_running_instance_information(self):
        """
        Test that the method can obtain the running EC2 instance information
        """

        # Add the EC2 instances for mocking
        ec2_connection = boto3.resource('ec2', region_name='us-east-1')
        rc1 = ec2_connection.create_instances(ImageId='ami-0022c769', MinCount=1, MaxCount=1)
        ec2_connection.create_tags(Resources=[rc1[0].id], Tags=[{'Key': 'Name', 'Value': 'test1'}])

        expected_ec2 = [
            {'status': 'running', 'tag': 'test1'},
        ]

        running_ec2 = get_ec2_running()

        for expected, running in zip(expected_ec2, running_ec2):
            self.assertDictEqual(
                expected,
                running,
                msg="Messages are not equal, {} != {}".format(
                    running,
                    expected
                )
            )

    @mock_ec2
    def test_can_get_ip_of_ec2_instance(self):
        """
        Test can get the ip of an ec2 instance
        """
        ec2_connection = boto3.resource('ec2', region_name='us-east-1')
        rc1 = ec2_connection.create_instances(ImageId='ami-0022c769', MinCount=1, MaxCount=1)
        ec2_connection.create_tags(
            Resources=[rc1[0].id],
            Tags=[{'Key': 'Name', 'Value': 'test1'}]
        )

        ip_ec2 = get_ec2_value('test1', 'ip')

        self.assertIsInstance(ip_ec2, list)
        for d in ip_ec2:
            self.assertTrue('PrivateIpAddress' in d or 'PublicIpAddress' in d)

    @patch('adsaws.get_boto3_session')
    def test_get_ecs_info(self, mock_session):
        mock_data = {'clusterArns': ['cluster/production','cluster/staging'],'ResponseMetadata': {}}
        mock_session.return_value.client.return_value.list_clusters.return_value = mock_data
        info = get_ecs_info()
        self.assertTrue('clusterArns' in info)

    @patch('adsaws.get_boto3_session')
    def test_aws_ecsclusters(self, mock_session):
        mock_data = {'clusterArns': ['cluster/production','cluster/staging'],'ResponseMetadata': {}}
        mock_session.return_value.client.return_value.list_clusters.return_value = mock_data
        foo = AdsAws()
        return_msg = foo.aws_ecsclusters()
        expected   = '**ADS AWS ECS Clusters**\n> production: cluster/production\n> staging: cluster/staging\n'
        self.assertEqual(return_msg, expected)

    @patch('adsaws.get_boto3_session')
    def test_get_ecs_details(self, mock_session):
        mock_data = {u'clusters': [{u'status': u'ACTIVE',
                                    u'clusterName': u'staging',
                                    u'registeredContainerInstancesCount': 3,
                                    u'pendingTasksCount': 0,
                                    u'runningTasksCount': 11,
                                    u'activeServicesCount': 11}], 
                                    'ResponseMetadata': {}}
        mock_session.return_value.client.return_value.describe_clusters.return_value = mock_data
        info = get_ecs_details('staging')
        self.assertTrue('clusters' in info)

    @patch('adsaws.get_boto3_session')
    def test_aws_ecsclusters(self, mock_session):
        mock_data = {u'clusters': [{u'status': u'ACTIVE',
                                    u'clusterName': u'staging',
                                    u'registeredContainerInstancesCount': 3,
                                    u'pendingTasksCount': 0,
                                    u'runningTasksCount': 11,
                                    u'activeServicesCount': 11}], 
                                    'ResponseMetadata': {}}
        mock_session.return_value.client.return_value.describe_clusters.return_value = mock_data
        foo = AdsAws()
        return_msg = foo.aws_ecsclusterinfo('ecsclusterinfo','staging')
        expected   = '**staging**\n>Status: ACTIVE\n># Registered Container Instances: 3\n># running Tasks: 11\n># pending Tasks: 0\n># active Servies: 11\n'
        self.assertEqual(return_msg, expected)

    @patch('adsaws.get_boto3_session')
    def test_get_ecs_containers(self, mock_session):
        mock_data = {u'failures': [], u'containerInstances': [{u'status': u'ACTIVE', 
                                                               u'registeredResources': [{u'integerValue': 1024, u'longValue': 0, u'type': u'INTEGER', u'name': u'CPU', u'doubleValue': 0.0}, 
                                                                                        {u'integerValue': 2004, u'longValue': 0, u'type': u'INTEGER', u'name': u'MEMORY', u'doubleValue': 0.0}, 
                                                                                        {u'name': u'PORTS', u'longValue': 0, u'doubleValue': 0.0, u'stringSetValue': [u'22', u'2376', u'2375', u'51678'], 
                                                                                        u'type': u'STRINGSET', u'integerValue': 0}, {u'name': u'PORTS_UDP', u'longValue': 0, u'doubleValue': 0.0, u'stringSetValue': [], 
                                                                                        u'type': u'STRINGSET', u'integerValue': 0}],
                                                               u'ec2InstanceId': u'i-3889f693', 
                                                               u'agentConnected': True, 
                                                               u'containerInstanceArn': u'ARN', 
                                                               u'pendingTasksCount': 0, 
                                                               u'remainingResources': [{u'integerValue': 1024, u'longValue': 0, u'type': u'INTEGER', u'name': u'CPU', u'doubleValue': 0.0},
                                                                                       {u'integerValue': 504, u'longValue': 0, u'type': u'INTEGER', u'name': u'MEMORY', u'doubleValue': 0.0},
                                                                                       {u'name': u'PORTS', u'longValue': 0, u'doubleValue': 0.0, u'stringSetValue': [u'22', u'2376', u'2375', u'51678'],
                                                                                       u'type': u'STRINGSET', u'integerValue': 0}, {u'name': u'PORTS_UDP', u'longValue': 0, u'doubleValue': 0.0, u'stringSetValue': [],
                                                                                       u'type': u'STRINGSET', u'integerValue': 0}],
                                                               u'runningTasksCount': 5, 
                                                               u'versionInfo': {u'agentVersion': u'1.3.0', u'agentHash': u'097e4af', u'dockerVersion': u'DockerVersion: 1.6.2'}}],
                                                                'ResponseMetadata': {}}
        mock_session.return_value.client.return_value.describe_container_instances.return_value = mock_data
        info = get_ecs_containers('staging')
        self.assertTrue('containerInstances' in info)

    @patch('adsaws.get_boto3_session')
    def test_aws_ecsclusterstatus(self, mock_session):
        mock_data = {u'failures': [], u'containerInstances': [{u'status': u'ACTIVE', 
                                                               u'registeredResources': [{u'integerValue': 1024, u'longValue': 0, u'type': u'INTEGER', u'name': u'CPU', u'doubleValue': 0.0}, 
                                                                                        {u'integerValue': 2004, u'longValue': 0, u'type': u'INTEGER', u'name': u'MEMORY', u'doubleValue': 0.0}, 
                                                                                        {u'name': u'PORTS', u'longValue': 0, u'doubleValue': 0.0, u'stringSetValue': [u'22', u'2376', u'2375', u'51678'], 
                                                                                        u'type': u'STRINGSET', u'integerValue': 0}, {u'name': u'PORTS_UDP', u'longValue': 0, u'doubleValue': 0.0, u'stringSetValue': [], 
                                                                                        u'type': u'STRINGSET', u'integerValue': 0}],
                                                               u'ec2InstanceId': u'i-3889f693', 
                                                               u'agentConnected': True, 
                                                               u'containerInstanceArn': u'ARN', 
                                                               u'pendingTasksCount': 0, 
                                                               u'remainingResources': [{u'integerValue': 1024, u'longValue': 0, u'type': u'INTEGER', u'name': u'CPU', u'doubleValue': 0.0},
                                                                                       {u'integerValue': 504, u'longValue': 0, u'type': u'INTEGER', u'name': u'MEMORY', u'doubleValue': 0.0},
                                                                                       {u'name': u'PORTS', u'longValue': 0, u'doubleValue': 0.0, u'stringSetValue': [u'22', u'2376', u'2375', u'51678'],
                                                                                       u'type': u'STRINGSET', u'integerValue': 0}, {u'name': u'PORTS_UDP', u'longValue': 0, u'doubleValue': 0.0, u'stringSetValue': [],
                                                                                       u'type': u'STRINGSET', u'integerValue': 0}],
                                                               u'runningTasksCount': 5, 
                                                               u'versionInfo': {u'agentVersion': u'1.3.0', u'agentHash': u'097e4af', u'dockerVersion': u'DockerVersion: 1.6.2'}}],
                                                                'ResponseMetadata': {}}
        mock_session.return_value.client.return_value.describe_container_instances.return_value = mock_data
        foo = AdsAws()
        return_msg = foo.aws_ecsclusterstatus('ecsclusterstatus', 'staging')
        expected = '**Cluster Container info for: staging**\n>Container: ARN\n>ec2InstanceId: i-3889f693\n>Container status: ACTIVE\n>Docker version: DockerVersion: 1.6.2\n>Agent version: 1.3.0\n>Agent connected: True\n>+++++++++++++++++++++++++++++++++++++++++++++\n'
        self.assertEqual(return_msg, expected)