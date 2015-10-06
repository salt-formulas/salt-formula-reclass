{%- from "reclass/map.jinja" import storage with context %}
{%- if storage.enabled %}

reclass_conf_dir:
  file.directory:
  - name: /etc/reclass

/etc/reclass/reclass-config.yml:
  file.managed:
  - source: salt://reclass/files/reclass-config.yml
  - template: jinja
  - require:
    - file: reclass_conf_dir

reclass_packages:
  pkg.latest:
  - names: {{ storage.pkgs }}

{%- endif %}
