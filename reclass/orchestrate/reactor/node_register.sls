{%- set node_name = salt['pillar.get']('event_originator') %}
{%- set node_data = salt['pillar.get']('event_data') %}

classify_node_{{ node_name }}:
  salt.state:
  - tgt: 'salt:master'
  - tgt_type: pillar
  - sls: reclass.reactor_sls.node_register
  - queue: True
  - pillar:
      node_name: {{ node_name }}
      node_data: {{ node_data }}

regenerate_all_nodes:
  salt.state:
  - tgt: 'salt:master'
  - tgt_type: pillar
  - sls: reclass.storage.node
  - queue: True
  - require:
    - salt: classify_node_{{ node_name }}
