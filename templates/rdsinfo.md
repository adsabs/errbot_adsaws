{% if error is defined %}
**{{error}}**
{% else %}
### Statistics for RDS instance: {{rdsinfo.instance}}
**Sample period**: {{rdsinfo.sampleperiod}}
<table>
	<tr><td>database</td><td>type</td><td>minmum</td><td>maximum</td><td>average</td></tr>
	{% for row in rdsinfo.data %}
	<tr><td>{{row.database}}</td><td>{{row.type}}</td><td>{{row.Minimum}}</td><td>{{row.Maximum}}</td><td>{{row.Average}}</td></tr>
	{% endfor %}
</table>
{% endif %}