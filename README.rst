
===============
Reclass Formula
===============

reclass is an "external node classifier" (ENC) as can be used with automation
tools, such as Puppet, Salt, and Ansible. It is also a stand-alone tool for
merging data sources recursively.


Sample Metadata
===============

Install sources from [repository, git, pip]


.. code-block:: yaml

    salt:
      source:
        engine: pkg
    ...
      source:
        engine: git
        repo: git+https://github.com/salt-formulas/reclass
        branch: master
    ...
      source:
        engine: pip
    ...

If reclass is pre-installed, set the engine to None to avoid updates.

.. code-block:: yaml

    salt:
      source:
        engine: None


Reclass storage with data fetched from git

.. literalinclude:: tests/pillar/storage_git.sls
   :language: yaml

Reclass storage with local data source

.. literalinclude:: tests/pillar/storage_local.sls
   :language: yaml

Reclass storage with archive data source

.. literalinclude:: tests/pillar/storage_archive.sls
   :language: yaml

Reclass storage with archive data source with content hash check

.. literalinclude:: tests/pillar/storage_archive_public.sls
   :language: yaml

Reclass model with single node definition

.. literalinclude:: tests/pillar/generate_single.sls
   :language: yaml

Reclass model with multiple node defined

.. literalinclude:: tests/pillar/generate_multi.sls
   :language: yaml

Reclass model with multiple node defined and interpolation enabled

.. literalinclude:: tests/pillar/generate_multi_interpolate.sls
   :language: yaml

Reclass storage with simple class mappings

.. literalinclude:: tests/pillar/class_mapping.sls
   :language: yaml

Reclass models with dynamic node classification

.. literalinclude:: tests/pillar/node_classify.sls
   :language: yaml

Classify node after creation and unclassify on node deletion

.. code-block:: yaml

    salt:
      master:
        reactor:
          reclass/minion/classify:
          - salt://reclass/reactor/node_register.sls
          reclass/minion/declassify:
          - salt://reclass/reactor/node_unregister.sls

Event to trigger the node classification

.. code-block:: bash

    salt-call event.send 'reclass/minion/classify' "{'node_master_ip': '$config_host', 'node_ip': '${node_ip}', 'node_domain': '$node_domain', 'node_cluster': '$node_cluster', 'node_hostname': '$node_hostname', 'node_os': '$node_os'}"

.. note::

    You can send any parameters in the event payload, all will be checked
    against dynamic node classification conditions.

    Both actions will use the minion ID as the node_name to be updated.

Confirmation of node classification

    Currently salt doesn't allow to get confirmation on minion upon successfull reactor execution on event. However there can be issues
    with reactor in salt 2017.7 (https://github.com/saltstack/salt/issues/47539) or reactor register state can fail if pillar failed
    to render, so node registration confirmation maybe needed. In order to enable this functionality add node_confirm_registration parameter to
    event data with value true:

.. code-block:: bash

    salt-call event.send 'reclass/minion/classify' "{'node_master_ip': '$config_host', 'node_ip': '${node_ip}', 'node_domain': '$node_domain', 'node_cluster': '$node_cluster', 'node_hostname': '$node_hostname', 'node_os': '$node_os', node_confirm_registration: true}"

    Then on minion side execute:
      salt-call mine.get 'salt:master' ${minion_id}_classified pillar

    If true is returned than registration has passed successfully

Event to trigger the node declassification

.. code-block:: bash

    salt-call event.send 'reclass/minion/declassify'

Nodes definitions generator
===========================

Generate nodes definitions by running:

.. code-block:: bash

    salt-call state.sls reclass.storage -l debug

Remove unnecessary files from nodes/_generated:

.. code-block:: yaml

    reclass:
      storage:
        reclass_nodes_cleanup: true

Static node definition:

.. code-block:: yaml

    reclass:
      storage:
        enabled: true
        node:
          openstack_benchmark_node01:
            classes:
            - cluster.example.openstack.benchmark
            domain: example.com
            name: bmk01
            params:
              linux_system_codename: xenial
              salt_master_host: 192.168.0.253
              single_address: 192.168.2.95

Multiple nodes definitions (using generator):

.. code-block:: yaml

    reclass:
      storage:
        enabled: true
        node:
          openstack_compute_rack01:
            classes:
            - cluster.example.openstack.compute
            domain: example.com
            name: cmp<<count>>
            params:
              linux_system_codename: xenial
              salt_master_host: 192.168.0.253
            repeat:
              start: 1
              count: 50
              digits: 3
              params:
                single_address:
                  start: 101
                  value: 192.168.2.<<count>>

Multiple nodes definitions (using generator) with IP address comprehension. Ranges are named and formatting symbol of the same name is replaced by IP address from corresponding range:

.. code-block:: yaml

    reclass:
      storage:
        enabled: true
        node:
          openstack_compute_rack01:
            classes:
            - cluster.example.openstack.compute
            domain: example.com
            name: cmp<<count>>
            params:
              linux_system_codename: xenial
              salt_master_host: 192.168.0.253
            repeat:
              ip_ranges:
                single_address: '172.16.10.97-172.16.10.98'
                tenant_address: '172.16.20.97-172.16.20.98'
              start: 1
              count: 50
              digits: 3
              params:
                single_address:
                  start: 101
                  value: 192.168.2.<<single_address>>
                tenant_address:
                  start: 101
                  value: 192.168.2.<<tenant_address>>

More Information
================

* http://reclass.pantsfullofunix.net/index.html
* http://reclass.pantsfullofunix.net/operations.html


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
