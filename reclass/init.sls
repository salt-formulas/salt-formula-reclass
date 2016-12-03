{%- if pillar.reclass is defined %}
include:
{%- if pillar.reclass.storage is defined %}
- reclass.storage
{%- endif %}
{%- endif %}
