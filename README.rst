
=======
reclass
=======

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

Reclass storage with arbitrary class mappings

.. code-block:: yaml

    reclass:
      storage:
        enabled: true
        ...
        class_mappings:
        - target: '\*'
          class: default

Read more
=========

* http://reclass.pantsfullofunix.net/index.html
* http://reclass.pantsfullofunix.net/operations.html
* http://ryandlane.com/blog/2014/12/10/reloading-grains-and-pillars-during-a-saltstack-run/
