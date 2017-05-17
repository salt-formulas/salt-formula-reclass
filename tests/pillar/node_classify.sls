reclass:
  storage:
    enabled: true
    class_mapping:
      common_node:
        type: all
        node_param:
          single_address:
            value_template: node_ip
          linux_system_codename:
            value_template: node_os
      infra_config_node:
        type: hostname__startswith
        expression: cfg
        node_class:
        - cluster.<<node_cluster>>.infra.config
        node_param:
          reclass_config_master:
            value_template: node_ip
      openstack_control:
        type: hostname__startswith
        expression: ctl
        node_class:
        - cluster.<<cluster>>.openstack.control
      openstack_control_node_member01:
        type: hostname__equals
        expression: ctl01
        cluster_param:
          openstack_control_node01_address:
            value_template: node_ip
        node_param:
          openstack_control_vip_address:
            value_template: node_ip
          keepalived_vip_priority:
            value: 103
          opencontrail_database_id:
            value: 1
          rabbitmq_cluster_role:
            value: master
      openstack_control_node_member02:
        type: hostname__equals
        expression: ctl02
        cluster_param:
          openstack_control_node01_address:
            value_template: node_ip
        node_param:
          keepalived_vip_priority:
            value: 102
          opencontrail_database_id:
            value: 2
          rabbitmq_cluster_role:
            value: slave
