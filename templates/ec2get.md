### {{title}}:
{% for item in data %}
**{{ item.key }}**: {{ item.value }}
{% endfor %}