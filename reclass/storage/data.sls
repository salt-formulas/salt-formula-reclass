{%- from "reclass/map.jinja" import storage with context %}
{%- if storage.enabled %}

{%- if storage.data_source.engine == "git" %}

reclass_data_source:
  git.latest:
  - name: {{ storage.data_source.address }}
  - target: {{ storage.base_dir }}
  - reload_pillar: True
  {%- if grains.saltversioninfo.0 >= 2015.8 %}
  - rev: HEAD
  - branch: {{ storage.data_source.branch }}
  {%- else %}
  - rev: {{ storage.data_source.branch }}
  {%- endif %}

{%- endif %}

{%- if storage.data_source.engine == "local" %}

reclass_data_dir:
  file.managed:
  - name: {{ storage.base_dir }}
  - mode: 700

{%- endif %}

{%- endif %}
