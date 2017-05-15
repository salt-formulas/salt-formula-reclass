# -*- coding: utf-8 -*-
'''
Management of reclass metadata
==============================

.. code-block:: yaml

    node01:
      reclass.node_present:
      - name: hostaname.domain.com
      - path: _generated
      - cluster: default
      - environment: prd
      - classes:
        - neco.service.neco
        - neco2.class.neco.dal
      - parameters:
          neco: value1
          neco2: value2

'''
import json
import six


def __virtual__():
    '''
    Only load if the reclass module is in __salt__
    '''
    return 'reclass' if 'reclass.node_list' in __salt__ else False


def node_present(name, path=None, cluster="default", environment="prd", classes=None, parameters=None, **kwargs):
    '''
    Ensure that the reclass node exists

    :param name: new node FQDN
    :param path: custom path in nodes for new node
    :param classes: classes given to the new node
    :param parameters: parameters given to the new node
    :param environment: node's environment
    :param cluster: node's cluster

    '''
    ret = {'name': name,
           'changes': {},
           'result': True,
           'comment': 'Node "{0}" already exists and it is in correct state'.format(name)}

    # Check if node is already present
    node = __salt__['reclass.node_get'](name, **kwargs)

    if 'Error' in node:
        # Create node
        __salt__['reclass.node_create'](name, path, cluster, environment, classes, parameters, **kwargs)
        ret['comment'] = 'Node "{0}" has been created'.format(name)
        ret['changes']['Node'] = 'Created'
    return ret

