# encoding: utf-8
"""
ADS AWS functions that collect the relevant information requested by the user
"""
import inspect
import itertools
import requests
from core import get_boto3_session
from errbot import BotPlugin, botcmd, arg_botcmd

API_URL = {
    'staging':'http://ecs-staging-elb-2044121877.us-east-1.elb.amazonaws.com',
    'production':'https://api.adsabs.harvard.edu'
}

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
        
        data = get_rds_info()
        
        return {'rdsinfo': data}
        
    def aws_ecsclusters(self, msg, args):
        """
        Get a list of ECS clusters with their ARN
        """
        cluster_info = get_ecs_info()
        data = []
        for entry in cluster_info.get('clusterArns'):
            data.append({'name': entry.split('/')[1], 'ARN':entry})
        return {'data': data}

    def aws_ecsclusterinfo(self, msg, args, test=False):
        """
        Get a list of properties for a given ECS cluster
        :param msg: msg sent
        :param args: arguments passed
        Return properties for a given ECS cluster
        """
        args = args.split(' ')
        try:
            cluster_info = get_ecs_details(*args)
        except:
            err_msg = 'Malformed request: !aws ecsclusterinfo <cluster name>'
            return {'cluster': '', 'data': [], 'error':err_msg}
        data = []
        for entry in cluster_info.get('clusters'):
            if entry['clusterName'] != args[0]:
                continue
            data.append({'status': entry['status'],
                         'instance_num': entry['registeredContainerInstancesCount'],
                         'running_num': entry['runningTasksCount'],
                         'pending_num': entry['pendingTasksCount'],
                         'active_num': entry['activeServicesCount']
                     })
            
        return {'cluster': args[0], 'data': data}

    def aws_ecsclusterstatus(self, msg, args, test=False):
        """
        Get status info for a given ECS cluster
        :param msg: msg sent
        :param args: arguments passed
        Return properties for a given ECS clusters
        """
        args = args.split(' ')
        try:
            container_info = get_ecs_containers(*args)
        except:
            err_msg = 'Malformed request: !aws ecsclusterstatus <cluster name>'
            return {'cluster': '', 'data': [], 'error':err_msg}
        try:
            services = get_ecs_services(*args)
        except:
            services = {}
        data = []
        for entry in container_info.get('containerInstances'):
            id = entry['ec2InstanceId']
            instance_services = services.get(id,[])
            services_list = []
            for srv in instance_services:
                services_list.append("%s (%s, revision %s)" % (srv.get('service'),srv.get('lastStatus'), srv.get('revision')))
            srv_str = ",".join(services_list)
            info = get_ec2_info(id)
            instance_type = info.get('Reservations')[0].get('Instances')[0].get('InstanceType')
            ip_address = info.get('Reservations')[0].get('Instances')[0].get('PrivateIpAddress')
            data.append({'container': entry['containerInstanceArn'],
                         'ec2InstanceId': id,
                         'status': entry['status'],
                         'docker_version': entry['versionInfo']['dockerVersion'],
                         'agent_version': entry['versionInfo']['agentVersion'],
                         'agent_connected': entry['agentConnected'],
                         'instance_type': instance_type,
                         'private_ip': ip_address,
                         'services': srv_str
                     })
        return {'cluster': args[0], 'data': data}

    def aws_ecs(self, msg, args, test=False):
        """
        Get status info for a given service running on ECS
        :param msg: msg sent
        :param args: arguments passed
        """
        args = args.split(' ')
        try:
            service_info = get_ecs_service_status(*args)
        except:
            err_msg = 'Malformed request: !aws ecs <service> or !aws ecs list'
            return {'service': '', 'data': [], 'error':err_msg}

        if args[0].strip() == 'list':
            return {'services_list':",".join(SERVICES)}
        data = get_ecs_service_status(*args)
        return {'service':args[0], 'data':data}

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

def get_rds_info(mtype='connections', sampleperiod=30):
    # for now we allow either connections (default) OR rollbacks
    if mtype not in ['connections', 'rollbacks']:
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
            d.update({'database': database, 'type': metrictype})
            info['data'].append(d)
    return data
    

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

def get_ecs_services(name):
    client = get_boto3_session().client('ecs')
    result = client.list_container_instances(cluster=name)
    containers = result.get('containerInstanceArns',[])
    services = {}
    for container in containers:
        cont_info = client.describe_container_instances(cluster=name, containerInstances=[container])
        cont_id = cont_info.get('containerInstances',[])[0].get('ec2InstanceId','NA')
        services[cont_id] = []
        info = client.list_tasks(cluster=name, containerInstance=container)
        tasks= info.get('taskArns',[])
        for task in tasks:
            task_info = client.describe_tasks(cluster=name, tasks=[task])
            items = task_info.get('tasks',[])
            data = {}
            for item in items:
                data['lastStatus'] = item.get('lastStatus','NA')
                data['desiredStatus']= item.get('desiredStatus','NA')
                data['service'] = item.get('containers','NA')[0].get('name','NA')
                data['revision'] = item.get('taskDefinitionArn','NA').split(':')[-1]
                services[cont_id].append(data)
    return services

def get_ecs_service_status(service_name):
    service_map = {
        'search':'solr-service'
    }
    serv = service_map.get(service_name, service_name)
    ec2_client = get_boto3_session().client('ec2')
    client = get_boto3_session().client('ecs')
    result = client.list_clusters()
    cnames = [e.split('/')[1] for e in result.get('clusterArns')]
    results = []
    for name in cnames:
        data = {}
        data['cluster'] = name
        data['service_info'] = {}
        containers = client.list_container_instances(cluster=name).get('containerInstanceArns',[])
        tasks = list(itertools.chain(*[client.list_tasks(cluster=name, containerInstance=c).get('taskArns',[]) for c in containers]))
        try:
            serv_tasks = [e for e in client.describe_tasks(cluster=name, tasks=tasks).get('tasks',[]) if serv in e.get('taskDefinitionArn','NA')]
            testURL, httpStatus = get_http_status(name, service_name)
        except:
            serv_tasks = []
            httpStatus = 'NA'
            testURL = 'NA'
        for item in serv_tasks:
            item.pop("overrides", None)
            ARN = item['containerInstanceArn']
            cont_info = client.describe_container_instances(cluster=name, containerInstances=[ARN])
            cont_id = cont_info.get('containerInstances',[])[0].get('ec2InstanceId','NA')
            instance_info = get_ec2_info(cont_id)
            interfaces = []
            for R in instance_info['Reservations']:
                for I in R['Instances']:
                    interfaces.append("(%s, %s)" % (I.get('PrivateIpAddress',"NA"), I.get('InstanceType',"NA")))
            try:
                info = client.describe_task_definition(taskDefinition=item.get('taskDefinitionArn')).get('taskDefinition')
            except:
                info = {}
            info['interfaces'] = ",".join(interfaces)
            item['taskDefinition'] = info
#            item['instanceInfo'] = instance_info
#            item['interfaces'] = ",".join(interfaces)
        data['service_info']['serviceTasks'] = serv_tasks
        data['service_info']['testURL'] = testURL
        data['service_info']['httpStatus'] = str(httpStatus)
        results.append(data)
    return results

def get_http_status(cluster, service):
    resp = requests.get("%s/resources"%API_URL[cluster])
    base = resp.json()['adsws.api']['base']
    tokenURL = "%s%s/accounts/bootstrap" % (API_URL[cluster], base)
    resp = requests.get(tokenURL)
    token = resp.json()['access_token']
    headers = {'Content-type': 'application/json', 'Accept': 'text/plain', 'Authorization':'Bearer %s' % token}
    serviceURL = "%s%s/%s/resources" % (API_URL[cluster], base, service)
    resp = requests.get(serviceURL, headers=headers)
    return (resp.url, resp.status_code)

def get_endpoints(cluster):
    exclude = [u'status', u'oauth', u'protected', u'user', u'vault']
    resp = requests.get("%s/resources"%API_URL[cluster])
    endpoints = list(set([e.split('/')[1] for e in resp.json()['adsws.api']['endpoints']]))
    endpoints = [e for e in endpoints if e not in exclude]
    return endpoints

def get_s3_buckets():
    s3 = get_boto3_session().client('s3')
    resp = s3.list_buckets()
    return resp['Buckets']

def get_s3_bucket_contents(bucket):
    s3 = get_boto3_session().client('s3')
    resp = s3.list_objects(Bucket=bucket)
    return resp['Contents']

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
 
        
