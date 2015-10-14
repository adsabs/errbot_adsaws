#### ADS AWS EC2 Instances:
{% for item in ec2info %}
**{{ item.tag }}**: {{ item.status }}
{% endfor %}