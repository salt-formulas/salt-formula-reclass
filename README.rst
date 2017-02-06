
===============
reclass formula
===============

reclass is an “external node classifier” (ENC) as can be used with automation tools, such as Puppet, Salt, and Ansible. It is also a stand-alone tool for merging data sources recursively.

Sample pillars
==============

Reclass storage with data fetched from git

.. code-block:: yaml

    reclass:
      storage:
        enabled: true
        base_dir: /srv/reclass
        data_source:
          engine: git
          address: git@repo.domain.com:reclass/reclass-project.git
          revision: master

Reclass storage with local data source

.. code-block:: yaml

    reclass:
      storage:
        enabled: true
        base_dir: /srv/reclass
        data_source:
          engine: local

Reclass model with single node definition

.. code-block:: yaml

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

Reclass model with multiple node defined

.. code-block:: yaml

    reclass:
      storage:
        enabled: true
        repeat_replace_symbol: '<<count>>'
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

Reclass storage with arbitrary class mappings

.. code-block:: yaml

    reclass:
      storage:
        enabled: true
        ...
        class_mappings:
        - target: '\*'
          class: default

External links
==============

* http://reclass.pantsfullofunix.net/index.html
* http://reclass.pantsfullofunix.net/operations.html
* http://ryandlane.com/blog/2014/12/10/reloading-grains-and-pillars-during-a-saltstack-run/

Documentation and Bugs
======================

To learn how to install and update salt-formulas, consult the documentation
available online at:

    http://salt-formulas.readthedocs.io/

In the unfortunate event that bugs are discovered, they should be reported to
the appropriate issue tracker. Use Github issue tracker for specific salt
formula:

    https://github.com/salt-formulas/salt-formula-reclass/issues

For feature requests, bug reports or blueprints affecting entire ecosystem,
use Launchpad salt-formulas project:

    https://launchpad.net/salt-formulas

You can also join salt-formulas-users team and subscribe to mailing list:

    https://launchpad.net/~salt-formulas-users

Developers wishing to work on the salt-formulas projects should always base
their work on master branch and submit pull request against specific formula.

    https://github.com/salt-formulas/salt-formula-reclass

Any questions or feedback is always welcome so feel free to join our IRC
channel:

    #salt-formulas @ irc.freenode.net
