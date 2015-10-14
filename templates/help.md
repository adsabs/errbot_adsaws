#### Available Bot Commands:
{% for item in commands %}
  * {{ item.command }}: {{ item.description }}
{% endfor %}