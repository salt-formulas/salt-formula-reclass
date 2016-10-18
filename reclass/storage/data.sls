{%- from "reclass/map.jinja" import storage with context %}
{%- if storage.enabled %}

{%- if storage.data_source.engine == "git" %}

reclass_git_data_dir:
  git.latest:
  - name: {{ storage.data_source.address }}
  - target: {{ storage.base_dir }}
  - reload_pillar: True
  - rev: {{ storage.data_source.revision|default(storage.data_source.branch) }}
  {%- if grains.saltversion >= "2015.8.0" %}
  - branch: {{ storage.data_source.branch|default(storage.data_source.revision) }}
  {%- endif %}
  - force_reset: {{ storage.data_source.force_reset|default(False) }}

{%- endif %}

reclass_data_dir:
  file.directory:
  - name: {{ storage.base_dir }}
  - mode: 700
{%- if storage.data_source.engine == "git" %}
  - require:
    - git: reclass_git_data_dir
{%- endif %}

{%- endif %}
