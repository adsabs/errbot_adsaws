{% if error is defined %}
**{{error}}**
{% else %}
### Statistics for RDS instance: {{rdsinfo.instance}}
**Sample period**: {{rdsinfo.sampleperiod}} minutes
database type  minmum  maximum  average
{% for row in rdsinfo.data %}
{{row.database}}  {{row.type}}  {{row.Minimum}}  {{row.Maximum}}  {{row.Average}}
{% endfor %}
{% endif %}