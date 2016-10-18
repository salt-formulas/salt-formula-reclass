{%- if pillar.reclass is defined %}
include:
- reclass.storage.service
- reclass.storage.data
{%- if pillar.reclass.storage.node is defined %}
- reclass.storage.node
{%- endif %}
{%- endif %}
