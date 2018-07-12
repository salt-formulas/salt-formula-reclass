{%- from "reclass/map.jinja" import storage with context %}
{%- if storage.enabled %}

{%- if storage.reclass_nodes_cleanup %}
{{ storage.base_dir }}/nodes/_generated_cleanup:
  file.directory:
    - name: {{ storage.base_dir }}/nodes/_generated
    - user: root
    - group: root
    - dir_mode: 755
    - file_mode: 644
    - makedirs: True
    - clean: True
{%- endif %}

{%- set storage_by_name = {} %}

{%- for node_name, node in storage.get('node', {}).iteritems() %}

{%- if node.name is defined and node.repeat is not defined %}
{%- set node_name = node.name %}

{%- if node_name in storage_by_name and storage_by_name[node_name].classes is defined %}
{%- do node.update({'classes': storage_by_name[node_name].classes + node.get('classes', []) }) %}
{%- endif %}

{%- endif %}

{%- do salt['defaults.merge'](storage_by_name, {node_name: node}) %}

{%- endfor %}

{%- for node_name, node in storage_by_name.iteritems() %}

{%- if node.repeat is defined %}

{%- for i in range(node.repeat.count) %}

{%- set extra_params = {} %}

{%- for param_name, param in node.repeat.params.iteritems() %}
{%- set param_count = (param.get('start', 1) + i)|string %}
{%- set param_value = {'value': param.value|replace(storage.repeat_count_replace_symbol, param_count.rjust(param.get('digits', 1), '0'))} %}
{%- if node.repeat.ip_ranges is defined %}
{%- for range_name, range in node.repeat.ip_ranges.iteritems() %}
{%- set ip_list = salt['netutils.parse_network_ranges'](range, node.repeat.count) %}
{%- do param_value.update({'value': param_value['value']|replace('<<' + range_name + '>>', ip_list[i])}) %}
{%- endfor %}
{%- endif %}
{%- do extra_params.update({param_name: {'value': param_value['value'], 'interpolate': param.get('interpolate', False)}}) %}
{%- endfor %}

{%- set node_count = (node.repeat.get('start', 1) + i)|string %}
{%- set node_name = node.name|replace(storage.repeat_count_replace_symbol, node_count.rjust(node.repeat.get('digits', 1), '0')) %}

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
{%- if storage.reclass_nodes_cleanup %}
  - require_in:
    - file: {{ storage.base_dir }}/nodes/_generated_cleanup
{%- endif %}

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
{%- if storage.reclass_nodes_cleanup %}
  - require_in:
    - file: {{ storage.base_dir }}/nodes/_generated_cleanup
{%- endif %}

{%- endif %}

{%- endfor %}

{%- endif %}
