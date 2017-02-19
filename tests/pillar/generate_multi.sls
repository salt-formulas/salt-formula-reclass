reclass:
  storage:
    enabled: true
    repeat_replace_symbol: <<count>>
    node:
      service_node01:
        name: node<<count>>
        domain: deployment.local
        classes:
        - cluster.deployment.service.role
        repeat:
          count: 2
          start: 5
          digits: 2
          params:
            single_address:
              value: 10.0.0.<<count>>
              start: 100
            deploy_address:
              value: part-<<count>>-whole
              start: 5
              digits: 3
        params:
          salt_master_host: <<salt-master-ip>>
          linux_system_codename: trusty
