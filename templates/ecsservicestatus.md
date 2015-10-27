{% if error is defined %}
**{{error}}**
{% else %}
#### Service: {{service}}
{% for item in data %}
**Cluster**: {{item.cluster}}
**test URL**: {{item.service_info.testURL}}
**HTTP status**: {{item.service_info.httpStatus}}
**Running tasks**:

  {% for t in item.service_info.serviceTasks %}
  **IP / instance type**: {{t.taskDefinition.interfaces}}
  **Image**: {{t.taskDefinition.image}}
  **Revision**: {{t.taskDefinition.revision}}
  **Status**: {{t.lastStatus}}
  {% endfor %}
  -----
{% endfor %}
{% endif %}
