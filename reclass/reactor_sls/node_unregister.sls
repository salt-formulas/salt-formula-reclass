{%- set node_name = salt['pillar.get']('node_name') %}

unclassify_node_{{ node_name }}:
  reclass.dynamic_node_absent:
    - name: {{ node_name }}
