{%- from "reclass/map.jinja" import storage with context %}
{%- if storage.enabled %}

{%- if storage.data_source.engine == "git" %}

reclass_data_source:
  git.latest:
  - name: {{ storage.data_source.address }}
  - target: {{ storage.base_dir }}
  - rev: {{ storage.data_source.branch }}
  - reload_pillar: True

{%- endif %}

{%- if storage.data_source.engine == "local" %}

reclass_data_dir:
  file.managed:
  - name: {{ storage.base_dir }}
  - mode: 700

{%- endif %}

{%- endif %}