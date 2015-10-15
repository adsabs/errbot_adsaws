{% if error is defined %}
**{{error}}**
{% else %}
### {{title}}:
{% for item in data %}
**{{ item.key }}**: {{ item.value }}
{% endfor %}
{% endif %}