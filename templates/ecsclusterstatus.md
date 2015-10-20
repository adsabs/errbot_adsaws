{% if error is defined %}
**{{error}}**
{% else %}
#### Cluster Container info for: {{cluster}}
{% for item in data %}
**Container**: {{item.container}}

**Instance Type**: {{item.instance_type}}

**ec2InstanceId**: {{item.ec2InstanceId}}

**IP address**: {{item.ip_address}}

**Container status**: {{item.status}}

**Docker version**: {{item.docker_version}}

**Agent version**: {{item.agent_num}}

**Agent connected**: {{item.agent_connected}}

**Services**: {{item.srv_str}}

  -----
{% endfor %}
{% endif %}