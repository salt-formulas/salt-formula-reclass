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

{% if node_data.get('node_confirm_registration', False) | to_bool %}
confirm_node_classification_{{ node_name }}:
  salt.function:
    - tgt: 'salt:master'
    - tgt_type: pillar
    - name: mine.send
    - arg:
      - '{{ node_name }}_classified'
      - 'mine_function=cmd.shell'
      - 'echo true'
    - require:
      - salt: regenerate_all_nodes
{% endif %}
