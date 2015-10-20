{% if error is defined %}
**{{error}}**
{% else %}
#### Cluster Container info for: {{cluster}}
{% for item in data %}
**Container**: {{item.container}}

**Instance Type**: {{item.instance_type}}

**ec2InstanceId**: {{item.ec2InstanceId}}

**IP address**: {{item.private_ip}}

**Container status**: {{item.status}}

**Docker version**: {{item.docker_version}}

**Agent version**: {{item.agent_num}}

**Agent connected**: {{item.agent_connected}}

**Services**: {{item.services}}

  -----
{% endfor %}
{% endif %}