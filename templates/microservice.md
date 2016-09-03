{% if error is defined %}
**{{error}}**
{% else %}
#### Info for: {{service}}
#### Environment: Production
{% for item in production %}
**Service version**: {{item.service_version}}

**Deploy version**: {{item.deploy_version}}

**Date updated**: {{item.date_updated}}

**IP address**: {{item.ip_address}}

**Container status**: {{item.status}}

**Service health**: {{item.health}}

**Instance type**: {{item.instance_type}}

**Instance name**: {{item.instance_name}}
{% endfor %}

----

#### Environment: Staging
{% for item in staging %}
**Service version**: {{item.service_version}}

**Deploy version**: {{item.deploy_version}}

**Date updated**: {{item.date_updated}}

**IP address**: {{item.ip_address}}

**Container status**: {{item.status}}

**Service health**: {{item.health}}

**Instance type**: {{item.instance_type}}

**Instance name**: {{item.instance_name}}

{% endfor %}
{% endif %}
