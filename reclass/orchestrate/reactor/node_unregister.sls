{%- set node_name = salt['pillar.get']('event_originator') %}

unregister_node_{{ node_name }}:
  salt.state:
  - tgt: 'salt:master'
  - tgt_type: pillar
  - sls: reclass.reactor_sls.node_unregister
  - queue: True
  - pillar:
      node_name: {{ node_name }}

{% if salt['mine.get']('salt:master', node_name + '_classified', 'pillar') %}
confirm_node_unregistration_{{ node_name }}:
  salt.function:
    - tgt: 'salt:master'
    - tgt_type: pillar
    - name: mine.delete
    - arg:
      - '{{ node_name }}_classified'
    - require:
      - salt: unregister_node_{{ node_name }}
{% endif %}
