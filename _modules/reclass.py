# -*- coding: utf-8 -*-
'''
Module for handling reclass metadata models.

'''

from __future__ import absolute_import

import io
import json
import logging
import os
import sys
import six
import yaml

from reclass import get_storage, output
from reclass.core import Core
from reclass.config import find_and_read_configfile

LOG = logging.getLogger(__name__)


def __virtual__():
    '''
    Only load this module if reclass
    is installed on this minion.
    '''
    return 'reclass'


def _get_nodes_dir():
    defaults = find_and_read_configfile()
    return os.path.join(defaults.get('inventory_base_uri'), 'nodes')


def _get_classes_dir():
    defaults = find_and_read_configfile()
    return os.path.join(defaults.get('inventory_base_uri'), 'classes')


def _get_cluster_dir():
    classes_dir = _get_classes_dir()
    return os.path.join(classes_dir, 'cluster')


def _get_node_meta(name, cluster="default", environment="prd", classes=None, parameters=None):
    host_name = name.split('.')[0]
    domain_name = '.'.join(name.split('.')[1:])

    if classes == None:
        meta_classes = []
    else:
        if isinstance(classes, six.string_types):
            meta_classes = json.loads(classes)
        else:
            meta_classes = classes

    if parameters == None:
        meta_parameters = {}
    else:
        if isinstance(parameters, six.string_types):
            meta_parameters = json.loads(parameters)
        else:
            # generate dict from OrderedDict
            meta_parameters = {k: v for (k, v) in parameters.items()}

    node_meta = {
        'classes': meta_classes,
        'parameters': {
            '_param': meta_parameters,
            'linux': {
                'system': {
                    'name': host_name,
                    'domain': domain_name,
                    'cluster': cluster,
                    'environment': environment,
                }
            }
        }
    }

    return node_meta


def node_create(name, path=None, cluster="default", environment="prd", classes=None, parameters=None, **kwargs):
    '''
    Create a reclass node

    :param name: new node FQDN
    :param path: custom path in nodes for new node
    :param classes: classes given to the new node
    :param parameters: parameters given to the new node
    :param environment: node's environment
    :param cluster: node's cluster

    CLI Examples:

    .. code-block:: bash

        salt '*' reclass.node_create server.domain.com classes=[system.neco1, system.neco2]
        salt '*' reclass.node_create namespace/test enabled=False
    
    '''
    ret = {}

    node = node_get(name=name)

    if node and not "Error" in node:
        LOG.debug("node {0} exists".format(name))
        ret[name] = node
        return ret

    host_name = name.split('.')[0]
    domain_name = '.'.join(name.split('.')[1:])

    node_meta = _get_node_meta(name, cluster, environment, classes, parameters)
    LOG.debug(node_meta)

    if path == None:
        file_path = os.path.join(_get_nodes_dir(), name + '.yml')
    else:
        file_path = os.path.join(_get_nodes_dir(), path, name + '.yml')

    with open(file_path, 'w') as node_file:
        node_file.write(yaml.safe_dump(node_meta, default_flow_style=False))

    return node_get(name)


def node_delete(name, **kwargs):
    '''
    Delete a reclass node

    :params node: Node name

    CLI Examples:

    .. code-block:: bash

        salt '*' reclass.node_delete demo01.domain.com
        salt '*' reclass.node_delete name=demo01.domain.com
    '''

    node = node_get(name=name)

    if 'Error' in node:
        return {'Error': 'Unable to retreive node'}

    if node[name]['path'] == '':
        file_path = os.path.join(_get_nodes_dir(), name + '.yml')
    else:
        file_path = os.path.join(_get_nodes_dir(), node[name]['path'], name + '.yml')

    os.remove(file_path)

    ret = 'Node {0} deleted'.format(name)

    return ret


def node_get(name, path=None, **kwargs):
    '''
    Return a specific node

    CLI Examples:

    .. code-block:: bash

        salt '*' reclass.node_get host01.domain.com
        salt '*' reclass.node_get name=host02.domain.com
    '''
    ret = {}
    nodes = node_list(**kwargs)

    if not name in nodes:
        return {'Error': 'Error in retrieving node'}
    ret[name] = nodes[name]
    return ret


def node_list(**connection_args):
    '''
    Return a list of available nodes

    CLI Example:

    .. code-block:: bash

        salt '*' reclass.node_list
    '''
    ret = {}

    for root, sub_folders, files in os.walk(_get_nodes_dir()):
        for fl in files:
            file_path = os.path.join(root, fl)
            with open(file_path, 'r') as file_handle:
                file_read = yaml.load(file_handle.read())
            file_data = file_read or {}
            classes = file_data.get('classes', [])
            parameters = file_data.get('parameters', {}).get('_param', [])
            name = fl.replace('.yml', '')
            host_name = name.split('.')[0]
            domain_name = '.'.join(name.split('.')[1:])
            path = root.replace(_get_nodes_dir()+'/', '')
            ret[name] = {
                'name': host_name,
                'domain': domain_name,
                'cluster': 'default',
                'environment': 'prd',
                'path': path,
                'classes': classes,
                'parameters': parameters
            }

    return ret


def node_update(name, classes=None, parameters=None, **connection_args):
    '''
    Update a node metadata information, classes and parameters.

    CLI Examples:

    .. code-block:: bash

        salt '*' reclass.node_update name=nodename classes="[clas1, class2]"
    '''
    node = node_get(name=name)
    if not node.has_key('Error'):
        node = node[name.split("/")[1]]
    else:
        return {'Error': 'Error in retrieving node'}


def inventory(**connection_args):
    '''
    Get all nodes in inventory and their associated services/roles classification.

    CLI Examples:

    .. code-block:: bash

        salt '*' reclass.inventory
    '''
    defaults = find_and_read_configfile()
    storage = get_storage(defaults['storage_type'], _get_nodes_dir(), _get_classes_dir())
    reclass = Core(storage, None)
    nodes = reclass.inventory()["nodes"]
    output = {}

    for node in nodes:
        service_classification = []
        role_classification = []
        for service in nodes[node]['parameters']:
            if service not in ['_param', 'private_keys', 'public_keys', 'known_hosts']:
                service_classification.append(service)
                for role in nodes[node]['parameters'][service]:
                    if role not in ['_support', '_orchestrate', 'common']:
                        role_classification.append('%s.%s' % (service, role))
        output[node] = {
            'roles': role_classification,
            'services': service_classification,
        }
    return output


def cluster_meta_list(file_name="overrides.yml", cluster="", **kwargs):
    path = os.path.join(_get_cluster_dir(), cluster, file_name)
    try:
        with io.open(path, 'r') as file_handle:
            meta_yaml = yaml.safe_load(file_handle.read())
        meta = meta_yaml or {}
    except Exception as e:
        msg = "Unable to load cluster metadata YAML %s: %s" % (path, repr(e))
        LOG.debug(msg)
        meta = {'Error': msg}
    return meta


def cluster_meta_delete(name, file_name="overrides.yml", cluster="", **kwargs):
    ret = {}
    path = os.path.join(_get_cluster_dir(), cluster, file_name)
    meta = __salt__['reclass.cluster_meta_list'](path, **kwargs)
    if 'Error' not in meta:
        metadata = meta.get('parameters', {}).get('_param', {})
        if name not in metadata:
            return ret
        del metadata[name]
        try:
            with io.open(path, 'w') as file_handle:
                file_handle.write(unicode(yaml.dump(meta, default_flow_style=False)))
        except Exception as e:
            msg = "Unable to save cluster metadata YAML: %s" % repr(e)
            LOG.error(msg)
            return {'Error': msg}
        ret = 'Cluster metadata entry {0} deleted'.format(name)
    return ret


def cluster_meta_set(name, value, file_name="overrides.yml", cluster="", **kwargs):
    path = os.path.join(_get_cluster_dir(), cluster, file_name)
    meta = __salt__['reclass.cluster_meta_list'](path, **kwargs)
    if 'Error' not in meta:
        if not meta:
            meta = {'parameters': {'_param': {}}}
        metadata = meta.get('parameters', {}).get('_param', {})
        if name in metadata and metadata[name] == value:
            return {name: 'Cluster metadata entry %s already exists and is in correct state' % name}
        metadata.update({name: value})
        try:
            with io.open(path, 'w') as file_handle:
                file_handle.write(unicode(yaml.dump(meta, default_flow_style=False)))
        except Exception as e:
            msg = "Unable to save cluster metadata YAML %s: %s" % (path, repr(e))
            LOG.error(msg)
            return {'Error': msg}
        return cluster_meta_get(name, path, **kwargs)
    return meta


def cluster_meta_get(name, file_name="overrides.yml", cluster="", **kwargs):
    ret = {}
    path = os.path.join(_get_cluster_dir(), cluster, file_name)
    meta = __salt__['reclass.cluster_meta_list'](path, **kwargs)
    metadata = meta.get('parameters', {}).get('_param', {})
    if 'Error' in meta:
        ret['Error'] = meta['Error']
    elif name in metadata:
        ret[name] = metadata.get(name)

    return ret

