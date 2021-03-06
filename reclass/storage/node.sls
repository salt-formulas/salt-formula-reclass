{%- from "reclass/map.jinja" import storage with context %}

{%- if storage.enabled %}

  {%- if storage.reclass_nodes_cleanup %}
{{ storage.base_dir }}/nodes/_generated_cleanup:
  file.directory:
    - name: {{ storage.base_dir }}/nodes/_generated
    - user: root
    - group: root
    - dir_mode: 755
    - file_mode: 644
    - makedirs: True
    - clean: True
  {%- endif %}

  {%- set storage_by_name = {} %}

  {%- for node_name, node in storage.get('node', {}).iteritems() %}
    {%- if node.repeat is defined %}

      {%- if node.repeat.ip_ranges is defined %}
        {%- set ip_ranges = {} %}
        {%- for ip_range_name, ip_range in node.repeat.ip_ranges.iteritems() %}
          {%- set ip_list = salt['netutils.parse_ip_ranges'](ip_range, node.repeat.count) %}
          {%- do ip_ranges.update({ip_range_name: ip_list}) %}
        {%- endfor %}
      {%- endif %}
      {%- if node.repeat.network_ranges is defined %}
        {%- set network_ranges = {} %}
        {%- for network_range_name, network_range in node.repeat.network_ranges.iteritems() %}
          {%- set ip_list = salt['netutils.parse_network_ranges'](network_range, iterate=True) %}
          {%- do network_ranges.update({network_range_name: ip_list}) %}
        {%- endfor %}
      {%- endif %}

      {%- for i in range(node.repeat.count) %}
        {%- set extra_params = {} %}

        {%- for param_name, param in node.repeat.params.iteritems() %}
          {%- set param_count = (param.get('start', 1) + i)|string %}
          {%- set param_value = {'value': param.value|replace(storage.repeat_count_replace_symbol, param_count.rjust(param.get('digits', 1), '0'))} %}
          {%- if node.repeat.ip_ranges is defined %}
            {%- for ip_range_name, ip_range in node.repeat.ip_ranges.iteritems() %}
              {%- do param_value.update({'value': param_value['value']|replace('<<' + ip_range_name + '>>', ip_ranges[ip_range_name][i])}) %}
            {%- endfor %}
          {%- endif %}
          {%- if node.repeat.network_ranges is defined %}
            {%- for network_range_name, network_range in node.repeat.network_ranges.iteritems() %}
              {% do param_value.update({'value': param_value['value']|replace('<<' + network_range_name + '>>', network_ranges[network_range_name][i])}) %}
            {%- endfor %}
          {%- endif %}
          {%- do extra_params.update({param_name: {'value': param_value['value'], 'interpolate': param.get('interpolate', False)}}) %}
        {%- endfor %}

        {%- set node_count = (node.repeat.get('start', 1) + i)|string %}
        {%- set repeat_node_name = node.name|replace(storage.repeat_count_replace_symbol, node_count.rjust(node.repeat.get('digits', 1), '0')) %}
        {%- set repeat_node = {} %}
        {%- do repeat_node.update(node) %}
        {%- do repeat_node.update({'__extra_params': extra_params}) %}
        {%- do salt['defaults.merge'](storage_by_name, {repeat_node_name: repeat_node}) %}
      {%- endfor %}

    {%- elif node.name is defined and node.repeat is not defined %}
      {%- set static_node_name = node.name %}
      {%- if static_node_name in storage_by_name and storage_by_name[static_node_name].classes is defined %}
        {%- do node.update({'classes': storage_by_name[static_node_name].classes + node.get('classes', []) }) %}
      {%- endif %}
      {%- do salt['defaults.merge'](storage_by_name, {static_node_name: node}) %}
    {%- endif %}
  {%- endfor %}

  {%- for node_name, node in storage_by_name.iteritems() %}

{{ storage.base_dir }}/nodes/_generated/{{ node_name }}.{{ node.domain }}.yml:
  file.managed:
  - source: salt://reclass/files/node.yml
  - user: root
  - group: root
  - template: jinja
  - makedirs: True
  - defaults:
      node: {{ node|yaml }}
      node_name: "{{ node_name }}"
      extra_params: {{ node.get('__extra_params', {}) }}
    {%- if storage.reclass_nodes_cleanup %}
  - require_in:
    - file: {{ storage.base_dir }}/nodes/_generated_cleanup
    {%- endif %}

  {%- endfor %}

{%- endif %}
