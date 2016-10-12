# encoding: utf-8
"""
ADS AWS functions that collect the relevant information requested by the user
"""
import inspect
import itertools
import requests
import datetime
from collections import defaultdict
import adsaws_config
from core import get_boto3_session
from errbot import BotPlugin, botcmd, arg_botcmd
import os
import time

os.environ['TZ'] = 'America/New_York'
time.tzset()

# Bumblebee API info
API_URL = {
    'staging':'http://ecs-staging-elb-2044121877.us-east-1.elb.amazonaws.com',
    'production':'https://api.adsabs.harvard.edu'
}
queryURL = "%s/v1/search/query" % API_URL['production']
headers = {'Content-type': 'application/json', 'Accept': 'text/plain', 'Authorization':'Bearer %s' % adsaws_config.API_KEY}
# ADS Classic info
try:
    bibgrpdirs = [d for d in os.listdir(adsaws_config.DATA_DIR) if d.find('bibgroup') > -1]
except:
    bibgrpdirs = []
bibgrp2dir = {}
for b in bibgrpdirs:
    bibname = "%s/%s/NAME"%(adsaws_config.DATA_DIR,b)
    if not os.path.exists(bibname):
        continue
    bibgrp = open(bibname).read().strip()
    bibgrp2dir[bibgrp] = bibname.replace('/NAME','')
refcodes = '%s/refereed/all.links' % adsaws_config.DATA_DIR
# Microservices info
SERVICES = ['metrics', 'graphics', 'recommender', 'orcid', 'biblib']

class AdsAws(BotPlugin):
    """
    ADS AWS commands
    """
    @botcmd(template="help")
    def aws(self, msg, args):
        """
        Get list of available bot commands
        :param msg: string
        :return: the corresponding info
        """

        commands = list(methodsWithDecorator(AdsAws, 'botcmd'))

        return {'commands':commands}

    @botcmd(template="ec2info")
    def aws_ec2info(self, msg, args):
        """
        Get the status of all the ADS AWS EC2 instances
        :param msg: msg sent
        :param args: arguments passed
        """
        info = get_ec2_running()

        return {'ec2info':info}

    @botcmd(template="ec2get")
    def aws_ec2get(self, msg, args):
        """
        Get the property of an ADS AWS EC2 instance
        :param msg: msg sent
        :param args: arguments passed
        """

        args = args.split(' ')
        if len(args) != 2:
            err_msg = 'Malformed request: !aws ec2get <instance> <property>'
            return {'title': '', 'data': [], 'error':err_msg}

        values = get_ec2_value(*args)

        data = []
        for value in values:
            data.append({'key': list(value.keys())[0], 'value': list(value.values())[0]})

        return {'title': args[0], 'data': data}
    
    @botcmd(template="rdsinfo")
    def aws_rdsinfo(self, msg, args):
        """
        Get information on the production Postgres DB instance:
        open connections and number of rollbacks per database
        :param msg: msg sent
        :param args: arguments passed
        """
        args = args.split(' ')
        try:
            data = get_rds_info(*args)
        except:
            err_msg = 'Malformed request: !aws_rdsinfo <connections|rollbacks> (connections is default)'
            return {'service': '', 'data': [], 'error':err_msg}
        
        return {'rdsinfo': data}

    @botcmd(template="microservice")
    def aws_microservice(self, msg, args):
        """
        Get information for a specific microservice
        :param msg: msg sent
        :param args: arguments passed
        """
        args = args.split(' ')
        try:
            production, staging = get_microservice_info(*args)
        except:
            err_msg = 'Malformed request: !aws_microservice <service name>'
            return {'service': '', 'data': [], 'error':err_msg}
            
        return {'service': args[0], 'production': production, 'staging': staging}

    @botcmd(template="s3buckets")
    def aws_s3buckets(self, msg, args):
        """
        Get a list of S3 buckets or the contents of a given one
        :param msg: msg sent
        :param args: arguments passed
        """
        args = args.split(' ')
        try:
            if args[0].strip() == 'list':
                buckets = get_s3_buckets()
                return {'title':'Buckets on S3', 'contents':buckets}
            else:
                contents = get_s3_bucket_contents(*args)
                return {'title':'Contents of S3 bucket %s'%args[0],'contents':contents}
        except:
            err_msg = 'Malformed request: !aws s3 <bucket name> or !aws s3 list'
            return {'service': '', 'data': [], 'error':err_msg}
    
    @botcmd(template="bibgroup")
    def check_bibgroup(self, msg, args):
        """
        For a given bibgroup, compare contents in Bumblebee versus Classic
        :param msg: msg sent
        :param args: arguments passed
        """
        args = args.split(' ')
        try:
            refereeed, notrefereed = get_bibgroup_discrepancies(*args)
        except:
            err_msg = 'Malformed request: !check_bibgroup <bibgroup> <refereed|notrefereed> (default: both)'
            return {'bibgroup': '', 'data': [], 'error':err_msg}
        if 'error' in results:
            return {'bibgroup': '', 'data': [], 'error':results['error']}
            
        return {'bibgroup': args[0], 'refereed': refereed, 'notrefereed': notrefereed}

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

def get_ec2_info(InstanceId):
    client = get_boto3_session().client('ec2')
    info = client.describe_instances(InstanceIds=[InstanceId])
    return info

def get_rds_info(mtype):
    sampleperiod=30
    # for now we allow either connections (default) OR rollbacks
    if not mtype or mtype not in ['connections', 'rollbacks']:
        mtype = 'connections'
    namespace = 'AdsAbsDatabase'
    instance = 'adsabs-psql'
    #
    dimensions = [{'Name':'InstanceName', 'Value': instance}]
    endtime = datetime.datetime.now()
    starttime = datetime.datetime.now() - datetime.timedelta(minutes=sampleperiod)
    # 
    client = get_boto3_session().client('cloudwatch')
    # Get the various metrics
    result = client.list_metrics(Namespace=namespace)
    if mtype in ['connections', 'rollbacks']:
        metrics = [m.get('MetricName') for m in result.get('Metrics') if m.get('MetricName').lower().find(mtype) > 0]
    else:
        metrics = [m.get('MetricName') for m in result.get('Metrics')]
    # For each of these metrics, gather data
    info = {}
    info.update({'namespace': namespace, 'instance': instance, 'sampleperiod': sampleperiod})
    info['data'] = []
    for metric in metrics:
        database = metric.replace('Rollbacks','').replace('Connections','').lower()
        metrictype = metric.lower().replace(database,'')
        res = client.get_metric_statistics(Namespace=namespace, 
        MetricName=metric, 
        Dimensions=dimensions, 
        StartTime=starttime, 
        EndTime=endtime, 
        Period=86400, 
        Statistics=['SampleCount', 'Maximum', 'Minimum', 'Average'], 
        Unit='Count')
        if len(res.get('Datapoints', [])) > 0:
            d = res.get('Datapoints')[-1]
            d['Average'] = round(d['Average'],1)
            d.update({'database': database, 'type': metrictype})
            info['data'].append(d)
    return info
    
def get_microservice_info(service):
    # We want to keep standard nomenclature in the results
    appname2env = {
            'eb-deploy':'production',
            'sandbox':'staging'
        }
    # The clients to talk to both Elastic Beanstalk and EC2
    client = get_boto3_session().client('elasticbeanstalk')
    ec2 = get_boto3_session().client('ec2')
    # Gather data for all our instances on EC2
    instances = []
    for reservation in ec2.describe_instances()['Reservations']:
        for instance in reservation['Instances']:
            try:
                idata = {
                    'tag': [i.get('Value') for i in instance['Tags'] if i['Key'] == 'Name'][0],
                    'status': instance['State']['Name'],
                    'type': instance['InstanceType'],
                    'ip': instance.get('PrivateIpAddress','NA')
                }
                instances.append(idata)
            except:
                pass
    # What environments do we have?
    result = client.describe_environments(IncludeDeleted=False)
    environments = result.get('Environments',[])
    # Filter them for the service we want
    environments = [e for e in environments if e['VersionLabel'].find(service) > -1]
    # Now we can start compiling the information we want to display
    data = []
    for entry in environments:
        d = {}
        version = entry['VersionLabel'].split(':')
        d['service'] = version[0]
        d['environment'] = entry['ApplicationName']
        d['environment_type'] = appname2env.get(entry['ApplicationName'],'NA')
        d['service_version'] = version[1]
        d['deploy_version'] = version[2]
        d['date_updated'] = entry['DateUpdated'].isoformat()
        d['instance_name'] = entry['EnvironmentName']
        d['health'] = entry['HealthStatus']
        try:
          insdata = [i for i in instances if i['tag'] == entry['EnvironmentName']][0]
          d['ip_address'] = insdata['ip']
          d['status'] = insdata['status']
          d['instance_type'] = insdata['type']
        except:
          d['ip_address'] = 'NA'
          d['status'] = 'NA'
          d['instance_type'] = 'NA'
        data.append(d)
    pdata = [d for d in data if d['environment_type'] == 'production']
    sdata = [d for d in data if d['environment_type'] == 'staging']
    return pdata, sdata

def get_s3_buckets():
    s3 = get_boto3_session().client('s3')
    resp = s3.list_buckets()
    return resp['Buckets']

def get_s3_bucket_contents(bucket):
    s3 = get_boto3_session().client('s3')
    resp = s3.list_objects(Bucket=bucket)
    return resp['Contents']

def check_bibliography(bibgroup, reftype):
    params = {'facet':'true',
                  'facet.limit':'-1',
                  'facet.pivot':'property,year',
                  'q':'bibgroup:%s'%bibgroup,
                  'sort':'date desc'}

    r = requests.get(queryURL, params=params, headers=headers)
    data = r.json()
    try:
        pivot = [d for d in data['facet_counts']['facet_pivot']['property,year'] if d['value'] == reftype][0]['pivot']
        BBBhist = dict([(int(p['value']), p['count']) for p in pivot])
    except:
        BBBhist = {2016: 0}
    minyear = min(BBBhist.keys())
    maxyear = max(BBBhist.keys())
    # Get the refereed bibcodes for the bibgroup
    cls_bibs = get_Classic_bibcodes(bibgroup, reftype)
    
    years = [int(b[:4]) for b in cls_bibs if len(b) > 0]
    CLShist = defaultdict(int)
    for y in years:
        CLShist[y] += 1
    results = [{'year':y, 'bumblebee':BBBhist.get(y,0), 'classic':CLShist.get(y,0)} for y in range(minyear, maxyear+1) if BBBhist.get(y,0) != CLShist.get(y,0)]
    return cls_bibs, results

def get_bibgroup_discrepancies(bibgroup):
    results = {}
    if bibgroup not in bibgrp2dir:
        return {'error':'unable to find data for bibgroup "%s"'%bibgroup}
    
    bibs, rf_discr = check_bibliography(bibgroup, 'refereed')
    bibs, nr_discr = check_bibliography(bibgroup, 'notrefereed')
    
    return rf_discr, nr_discr
    
def get_Classic_bibcodes(bibgroup, reftype, year=None):
    bibgroup_class_bibs = bibgrp2dir.get(bibgroup, None)
    if not bibgroup_class_bibs:
        return []
    bibcodes = []
    bibgroup_lnks = "%s/all.links" % bibgroup_class_bibs
    with open(bibgroup_lnks) as fh:
        for line in fh:
            if year and line.strip()[:4] == year:
                bibcodes.append(line.strip())
            else:
                if not year:
                    bibcodes.append(line.strip())

    ref_bibs = []
    with open(refcodes) as f:
        for line in f:
            if year and line.strip()[:4] == year:
                ref_bibs.append(line.strip())
            else:
                if not year:
                    ref_bibs.append(line.strip())

    bibcodes_ref = set(ref_bibs) & set(bibcodes)
    bibcodes_notref = set(bibcodes) - bibcodes_ref

    if reftype == 'refereed':
        return list(bibcodes_ref)
    else:
        return list(bibcodes_notref)

def get_BBB_bibcodes(bibgroup, reftype, year=None):
    # Get bibcodes for a given bibgroup
    #  reftype: refereed / notrefereed
    if year:
        params = {'q':'bibgroup:%s property:%s year:%s' % (bibgroup, reftype, year)}
    else:
        params = {'q':'bibgroup:%s property:%s' % (bibgroup, reftype)}

    params['fl'] = 'bibcode'
    params['rows'] = 2000

    r = requests.get(queryURL, params=params, headers=headers)
    data = r.json()
    try:
        bibcodes = [r['bibcode'] for r in data['response']['docs']]
    except:
        bibcodes = []

    return bibcodes

def methodsWithDecorator(cls, decoratorName):
    sourcelines = inspect.getsourcelines(cls)[0]
    for i,line in enumerate(sourcelines):
        line = line.strip()
        if line.split('(')[0].strip() == '@'+decoratorName: # leaving a bit out
            nextLine = sourcelines[i+1]
            name = nextLine.split('def')[1].split('(')[0].strip()
            hlp  = inspect.getdoc(eval('AdsAws.%s'%name)).split('\n')[0]
            yield({'command':name,'description':hlp})

if __name__ == '__main__':
    response = get_s3_bucket_contents('adsabs-consul-backups')
    print(response)
 
        
