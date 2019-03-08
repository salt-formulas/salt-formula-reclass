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

{%- if storage.source.engine == 'pkg' %}
reclass_packages:
  pkg.installed:
    - names: {{ storage.pkgs }}

{%- elif storage.source.engine == 'git' %}
storage_install_git_python_pip:
  pkg.installed:
    - names: {{ storage.dependency.pkgs }}

storage_install_reclass_git:
  pip.installed:
    - name: reclass
    - editable: git+{{ storage.source.repo }}@{{ storage.source.branch }}#egg=reclass
    - upgrade: True
    - force_reinstall: True
    - ignore_installed: True
    - require:
      - pkg: storage_install_git_python_pip

{%- elif storage.source.engine == 'pip' %}
storage_install_python_pip:
  pkg.installed:
    - names: {{ storage.dependency.pkgs }}

storage_install_reclass_pip:
  pip.installed:
    - name: reclass
    - upgrade: True
    - force_reinstall: True
    - ignore_installed: True
    - require:
      - pkg: storage_install_git_python_pip

{%- endif %}
{%- endif %}
