# Invoice {{ invoice_id }}

**Client:** {{ client_name }}
**Date:** {{ date }}

| Description | Qty | Unit Price | Line Total |
|---|---|---|---|
{% for item in line_items %}| {{ item.description }} | {{ item.quantity }} | {{ item.unit_price }} | {{ item.line_total }} |
{% endfor %}
**Total: {{ total_amount }}**
