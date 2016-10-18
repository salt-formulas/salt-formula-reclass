{%- from "reclass/map.jinja" import storage with context %}
{%- if storage.enabled %}

include:
  - reclass.storage.data

{{ storage.base_dir }}/nodes/_generated:
  file.directory

{%- for node_name, node in storage.node.iteritems() %}

{{ storage.base_dir }}/nodes/_generated/{{ node.name }}.{{ node.domain }}.yml:
  file.managed:
  - source: salt://reclass/files/node.yml
  - user: root
  - group: root
  - template: jinja
  - defaults:
      node_name: "{{ node_name }}"
  - require:
    - file: reclass_data_dir

{%- endfor %}

{%- endif %}
