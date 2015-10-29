{% if error is defined %}
**{{error}}**
{% else %}
#### **{{title}}**:
{% for item in contents %}
{% if item.Name is defined %}
{{ item.Name }}
{% else %}
{{ item.Key }}
{% endif %}
{% endfor %}
{% endif %}