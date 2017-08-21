{%- set node_name = salt['pillar.get']('event_originator') %}

unregister_node_{{ node_name }}:
  salt.state:
  - tgt: 'salt:master'
  - tgt_type: pillar
  - sls: reclass.reactor_sls.node_unregister
  - queue: True
  - pillar:
      node_name: {{ node_name }}
