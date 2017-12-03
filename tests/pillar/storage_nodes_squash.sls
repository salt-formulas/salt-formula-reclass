reclass:
  storage:
    enabled: true
    node:
      service_node01:
        name: svc01
        domain: deployment.local
        classes:
        - cluster.deployment_name.service.role
      service_node02:
        name: svc01
        domain: deployment.local
        classes:
        - cluster.deployment_name.service.role2
