reclass:
  storage:
    enabled: true
    class_mapping:
      common_node:
        expression: all
        node_param:
          single_address:
            value_template: <<node_ip>>
          linux_system_codename:
            value_template: <<node_os>>
          salt_master_host:
            value_template: <<node_master_ip>>
      infra_config:
        expression: <<node_hostname>>__startswith__cfg
        cluster_param:
          infra_config_address:
            value_template: <<node_ip>>
          infra_config_deploy_address:
            value_template: <<node_ip>>
      infra_proxy:
        expression: <<node_hostname>>__startswith__prx
        node_class:
          value_template:
            - cluster.<<node_cluster>>.stacklight.proxy
      kubernetes_control01:
        expression: <<node_hostname>>__equals__ctl01
        cluster_param:
          kubernetes_control_node01_address:
            value_template: <<node_ip>>
      kubernetes_control02:
        expression: <<node_hostname>>__equals__ctl02
        cluster_param:
          kubernetes_control_node02_address:
            value_template: <<node_ip>>
      kubernetes_control03:
        expression: <<node_hostname>>__equals__ctl03
        cluster_param:
          kubernetes_control_node03_address:
            value_template: <<node_ip>>
      kubernetes_compute:
        expression: <<node_hostname>>__startswith__cmp
        node_class:
          value_template:
            - cluster.<<node_cluster>>.kubernetes.compute
