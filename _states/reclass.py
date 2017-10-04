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

.. code-block:: yaml

    node_meta_01:
      reclass.cluster_meta_present:
      - name: my_key
      - value: my_value
'''
from __future__ import absolute_import

import json
import os
import six

from reclass.config import find_and_read_configfile


def __virtual__():
    '''
    Only load if the reclass module is in __salt__
    '''
    return 'reclass' if 'reclass.node_list' in __salt__ else False


def _get_classes_dir():
    defaults = find_and_read_configfile()
    return os.path.join(defaults.get('inventory_base_uri'), 'classes')


def _get_cluster_dir():
    classes_dir = _get_classes_dir()
    return os.path.join(classes_dir, 'cluster')


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
        if __opts__['test']:
            ret['result'] = None
            ret['comment'] = 'Node "{0}" would be created'.format(name)
            return ret
        # Create node
        __salt__['reclass.node_create'](name, path, cluster, environment, classes, parameters, **kwargs)
        ret['comment'] = 'Node "{0}" has been created'.format(name)
        ret['changes']['Node'] = 'Created'
    return ret


def dynamic_node_present(name, node_data={}, class_mapping={}, **kwargs):
    '''
    Classify node, create cluster level overrides and node metadata

    :param name: node FQDN
    :param node_data: dictionary of known informations about the node
    :param class_mapping: dictionary of classes and parameters, with conditions

    '''
    ret = {'name': name,
           'changes': {},
           'result': True,
           'comment': 'Node "{0}" already exists and it is in correct state'.format(name)}

    if __opts__['test']:
        ret['result'] = None
        ret['comment'] = 'Classification of node "{0}" would be updated'.format(name)
        return ret

    classify_ret = __salt__['reclass.node_classify'](name, node_data, class_mapping, **kwargs)
    ret['comment'] = 'Node "{0}" has been created'.format(name)
    ret['changes']['Node'] = classify_ret

    return ret


def node_absent(name, **kwargs):
    '''
    Delete node from reclass metadata

    :param name: node minion ID

    '''
    ret = {'name': name,
           'changes': {},
           'result': True,
           'comment': 'Node "{0}" already absent'.format(name)}

    # Check if node is present
    node = __salt__['reclass.node_get'](name, **kwargs)
    if 'Error' in node:
        return ret

    if __opts__['test']:
        ret['result'] = None
        ret['comment'] = 'Node "{0}" would be deleted'.format(name)
        return ret

    delete_ret = __salt__['reclass.node_delete'](name, **kwargs)
    if 'Error' in delete_ret:
        ret['result'] = False
        ret['comment'] = delete_ret.get('Error', '')
        return ret

    ret['comment'] = 'Node "{0}" has been deleted'.format(name)
    ret['changes']['Node'] = delete_ret

    return ret


def cluster_meta_present(name, value, file_name="overrides.yml", cluster="", **kwargs):
    '''
    Ensures that the cluster metadata entry exists
    
    :param name: Metadata entry name
    :param value: Metadata entry value
    :param file_name: Name of metadata file, defaults to overrides.yml
    :param cluster: Name of cluster directory to put the metadata file into, optional
    '''
    value = value or ""
    cluster = cluster or ""
    path = os.path.join(_get_cluster_dir(), cluster, file_name)
    ret = {'name': name,
           'changes': {},
           'result': True,
           'comment': 'Cluster metadata entry "{0}" already exists and is in correct state'.format(name)}
    meta_check = __salt__['reclass.cluster_meta_get'](name, path, **kwargs)
    if not meta_check:
        if __opts__['test']:
            ret['result'] = None
            ret['comment'] = 'Cluster metadata entry "{0}" would be created'.format(name)
            return ret
        __salt__['reclass.cluster_meta_set'](name, value, path, **kwargs)
        ret['comment'] = 'Cluster metadata entry {0} has been created'.format(name)
        ret['changes']['Meta Entry'] = 'Cluster meta entry %s: "%s" has been created' % (name, value)
    elif 'Error' in meta_check:
        ret['comment'] = meta_check.get('Error')
        ret['result'] = False
    elif meta_check[name] != value:
        if __opts__['test']:
            ret['result'] = None
            ret['comment'] = 'Cluster metadata entry "{0}" would be updated'.format(name)
            ret['changes']['Old Meta Entry'] = '{0}: "{1}"'.format(name, meta_check[name])
            ret['changes']['New Meta Entry'] = '{0}: "{1}"'.format(name, value)
            return ret
        __salt__['reclass.cluster_meta_set'](name, value, path, **kwargs)
        ret['comment'] = 'Cluster metadata entry {0} has been updated'.format(name)
        ret['changes']['Old Meta Entry'] = '{0}: "{1}"'.format(name, meta_check[name])
        ret['changes']['New Meta Entry'] = '{0}: "{1}"'.format(name, value)
    return ret


def cluster_meta_absent(name, file_name="overrides.yml", cluster="", **kwargs):
    '''
    Ensures that the cluster metadata entry does not exist

    :param name: Metadata entry name
    :param file_name: Name of metadata file, defaults to overrides.yml
    :param cluster: Name of cluster directory to put the metadata file into, optional
    '''
    cluster = cluster or ""
    path = os.path.join(_get_cluster_dir(), cluster, file_name)
    ret = {'name': name,
           'changes': {},
           'result': True,
           'comment': 'Cluster metadata entry "{0}" is already absent'.format(name)}
    meta_check = __salt__['reclass.cluster_meta_get'](name, path, **kwargs)
    if meta_check:
        if __opts__['test']:
            ret['result'] = None
            ret['comment'] = 'Cluster metadata entry "{0}" would be deleted'.format(name)
            return ret
        __salt__['reclass.cluster_meta_delete'](name, path, **kwargs)
        ret['comment'] = 'Cluster metadata entry {0} has been deleted'.format(name)
        ret['changes']['Meta Entry'] = 'Cluster metadata entry %s: "%s" has been deleted' % (name, meta_check[name])
    elif 'Error' in meta_check:
        ret['comment'] = meta_check.get('Error')
        ret['result'] = False
    return ret

