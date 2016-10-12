{% if error is defined %}
**{{error}}**
{% else %}
#### Discrepancies for bibgroup: {{bibgroup}}
#### Year: {{year}}
#### Refereed Status: {{reftype}}
Records in Bumblebee but not in Classic:

{% for item in bumblebee %}
{{item}}
{% endfor %}

----

Records in Classic but not in Bumblebee:

{% for item in classic %}
{{item}}
{% endfor %}
{% endif %}
