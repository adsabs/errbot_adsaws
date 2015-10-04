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
    def aws(self, msg):
        """
        Get info on the ec2 instances
        :param msg: string
        :return: the corresponding info
        """
        help = ''
        return help

    @botcmd
    def aws_ec2info(self, msg, args):
        """
        :param msg: msg sent
        :param args: arguments passed
        Return the ec2 info for running instances
        """
        return get_ec2_running()

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

if __name__ == '__main__':
    response = get_ec2_running()

    print response