
orchestrate_node_register:
  runner.state.orchestrate:
    - mods: reclass.orchestrate.reactor.node_register
    - queue: True
    - pillar:
        event_originator: {{ data.id }}
        event_data: {{ data.data }}
