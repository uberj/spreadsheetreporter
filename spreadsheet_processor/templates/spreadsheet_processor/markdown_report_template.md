# Report for Row {{ row_number }}

## Data Summary
{% for field, value in data.items() %}
- **{{ field }}**: {{ value }}
{% endfor %}

## Generated Details
- **Report ID**: {{ report_id }}
- **Generated At**: {{ generated_at }}
- **Total Fields**: {{ data|length }} 