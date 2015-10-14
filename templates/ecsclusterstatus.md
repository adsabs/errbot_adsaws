#### Cluster Container info for: {{cluster}}
{% for item in data %}
**Container**: {{item.container}}

**ec2InstanceId**: {{item.ec2InstanceId}}

**Container status**: {{item.status}}

**Docker version**: {{item.docker_version}}

**Agent version**: {{item.agent_num}}

**Agent connected**: {{item.agent_connected}}

  -----
{% endfor %}