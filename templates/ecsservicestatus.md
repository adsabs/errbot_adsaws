{% if error is defined %}
**{{error}}**
{% elif services_list is defined %}
**Info available for**: {{services_list}}
{% else %}
#### Service: {{service}}
{% for item in data %}
**Cluster**: {{item.cluster}}

{% if item.service_info.testURL != "NA" %}
**test URL**: {{item.service_info.testURL}}

**HTTP status**: {{item.service_info.httpStatus}}

**Running tasks**:

  {% for t in item.service_info.serviceTasks %}
  **IP / instance type**: {{t.taskDefinition.interfaces}}
  
  **Image**: {{t.taskDefinition.containerDefinitions[0].image}}
  
  **Revision**: {{t.taskDefinition.revision}}
  
  **Status**: {{t.lastStatus}}
  
  {% endfor %}
 {% endif %}
  -----
{% endfor %}
{% endif %}
