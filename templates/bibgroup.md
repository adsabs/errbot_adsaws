{% if error is defined %}
**{{error}}**
{% else %}
#### Discrepancies for bibgroup: {{bibgroup}}
#### Refereed Publications
Year Bumblebee Classic
{% for item in refereed %}
{{item.year}} {{item.bumblebee}} {{item.classic}}
{% endfor %}

----

#### Non-Refereed Publications
Year Bumblebee Classic
{% for item in notrefereed %}
{item.year}} {{item.bumblebee}} {{item.classic}}
{% endfor %}
{% endif %}
