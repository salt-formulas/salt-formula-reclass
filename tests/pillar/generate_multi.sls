reclass:
  storage:
    enabled: true
    reclass_nodes_cleanup: true
    repeat_replace_symbol: <<count>>
    node:
      service_node01:
        name: node<<count>>
        domain: deployment.local
        classes:
        - cluster.deployment.service.role
        repeat:
          ip_ranges:
            single_address: '172.16.10.101-172.16.10.254'
            deploy_address: '172.16.20.101-172.16.20.254'
          count: 2
          start: 5
          digits: 2
          params:
            single_address:
              value: <<single_address>>
              start: 100
            deploy_address:
              value: <<deploy_address>>
              start: 5
              digits: 3
        params:
          salt_master_host: <<salt-master-ip>>
          linux_system_codename: trusty
