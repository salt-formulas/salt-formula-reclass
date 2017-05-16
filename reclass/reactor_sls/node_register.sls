{%- set node_name = salt['pillar.get']('node_name') %}
{%- set node_data = salt['pillar.get']('node_data') %}
{%- set class_mapping = salt['pillar.get']('reclass:storage:class_mapping') %}

classify_node_{{ node_name }}:
  reclass.dynamic_node_present:
    - name: {{ node_name }}
    - node_data: {{ node_data }}
    - class_mapping: {{ class_mapping }}

