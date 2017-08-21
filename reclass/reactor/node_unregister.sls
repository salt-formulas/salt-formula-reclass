
orchestrate_node_unregister:
  runner.state.orchestrate:
  - mods: reclass.orchestrate.reactor.node_unregister
  - queue: True
  - pillar:
      event_originator: {{ data.id }}
