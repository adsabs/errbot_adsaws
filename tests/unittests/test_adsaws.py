# encoding: utf-8
import boto3
import unittest

from moto import mock_ec2
from adsaws import get_ec2_running

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
        rc2 = ec2_connection.create_instances(ImageId='ami-005db969', MinCount=1, MaxCount=1)
        ec2_connection.create_tags(Resources=[rc1[0].id], Tags=[{'Key': 'Name', 'Value': 'test1'}])
        ec2_connection.create_tags(Resources=[rc2[0].id], Tags=[{'Key': 'Name', 'Value': 'test2'}])

        expected_ec2 = [
            {'status': 'running', 'tag': 'test1'},
            {'status': 'running', 'tag': 'test2'}
        ]

        running_ec2 = get_ec2_running()

        self.assertItemsEqual(
            expected_ec2,
            running_ec2,
            msg="Messages are not equal, {} != {}".format(
                running_ec2,
                expected_ec2
            )
        )

