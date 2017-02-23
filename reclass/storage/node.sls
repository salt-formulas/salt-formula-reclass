{%- from "reclass/map.jinja" import storage with context %}
{%- if storage.enabled %}

{%- for node_name, node in storage.get('node', {}).iteritems() %}

{%- if node.repeat is defined %}

{%- for i in range(node.repeat.count) %}

{%- set extra_params = {} %}

{%- for param_name, param in node.repeat.params.iteritems() %}
{%- set param_count = (param.get('start', 1) + i)|string %}
{%- set param_value = param.value|replace(storage.repeat_replace_symbol, param_count.rjust(param.get('digits', 1), '0')) %}
{%- do extra_params.update({param_name: param_value}) %}
{%- endfor %}

{%- set node_count = (node.repeat.get('start', 1) + i)|string %}
{%- set node_name = node.name|replace(storage.repeat_replace_symbol, node_count.rjust(node.repeat.get('digits', 1), '0')) %}

{{ storage.base_dir }}/nodes/_generated/{{ node_name }}.{{ node.domain }}.yml:
  file.managed:
  - source: salt://reclass/files/node.yml
  - user: root
  - group: root
  - template: jinja
  - makedirs: True
  - defaults:
      node: {{ node|yaml }}
      node_name: "{{ node_name }}"
      extra_params: {{ extra_params }}

{%- endfor %}

{%- else %}

{{ storage.base_dir }}/nodes/_generated/{{ node.name }}.{{ node.domain }}.yml:
  file.managed:
  - source: salt://reclass/files/node.yml
  - user: root
  - group: root
  - template: jinja
  - makedirs: True
  - defaults:
      node: {{ node|yaml }}
      node_name: "{{ node.get('name', node_name) }}"
      extra_params: {}

{%- endif %}

{%- endfor %}

{%- endif %}
