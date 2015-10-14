#### ADS AWS ECS Clusters:
{% for item in data %}
**{{ item.name }}**: {{ item.ARN }}
{% endfor %}