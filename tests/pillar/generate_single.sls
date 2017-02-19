reclass:
  storage:
    enabled: true
    node:
      service_node01:
        name: svc01
        domain: deployment.local
        classes:
        - cluster.deployment_name.service.role
        params:
          salt_master_host: <<salt-master-ip>>
          linux_system_codename: trusty
          single_address: <<node-ip>>

