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

{%- elif storage.data_source.engine == "archive" %}

reclass_archive_data_dir:
  archive.extracted:
    - name: {{ storage.base_dir }}
    - source: {{ storage.data_source.address }}
    {%- if storage.data_source.hash is string %}
    - source_hash: {{ storage.data_source.hash }}
    {%- endif %}
    {%- if storage.data_source.options is string %}
    - options: {{ storage.data_source.options }}
    {%- endif %}
    - user: root
    - group: root
    - if_missing: {{ storage.base_dir }}/classes

{%- endif %}

reclass_data_dir:
  file.directory:
  - name: {{ storage.base_dir }}
  - mode: 700
{%- if storage.data_source.engine == "git" %}
  - require:
    - git: reclass_git_data_dir
{%- elif storage.data_source.engine == "archive" %}
  - require:
    - archive: reclass_archive_data_dir
{%- endif %}

{%- endif %}
