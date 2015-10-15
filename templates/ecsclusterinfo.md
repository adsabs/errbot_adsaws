{% if error is defined %}
**{{error}}**
{% else %}
#### Information for cluster "{{cluster}}":
{% for item in data %}
**Status**: {{item.status}}

**Number Registered Container Instances**: {{item.instance_num}}

**Number Running Tasks**: {{item.running_num}}

**Number Pending Tasks**: {{item.pending_num}}

**Number Active Tasks**: {{item.active_num}}
{% endfor %}
{% endif %}