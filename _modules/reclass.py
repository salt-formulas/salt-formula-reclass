# -*- coding: utf-8 -*-
'''
Module for handling reclass files.

'''

from __future__ import absolute_import

import logging
import os
import sys
import six
import yaml
import json

LOG = logging.getLogger(__name__)

RECLASS_NODES_DIR = "/srv/salt/reclass/nodes"
RECLASS_CLASSES_DIR = "/srv/salt/reclass/classes"


def __virtual__():
    '''
    Only load this module if reclass
    is installed on this minion.
    '''
    return 'reclass'


__opts__ = {}


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
            meta_parameters = parameters

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
    LOG.debug(node_meta)

    if path == None:
        file_path = os.path.join(RECLASS_NODES_DIR, name + '.yml')
    else:
        file_path = os.path.join(RECLASS_NODES_DIR, path, name + '.yml')

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
        file_path = os.path.join(RECLASS_NODES_DIR, name + '.yml')
    else:
        file_path = os.path.join(RECLASS_NODES_DIR, node[name]['path'], name + '.yml')

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

    for root, sub_folders, files in os.walk(RECLASS_NODES_DIR):
        for file in files:
            file_path = os.path.join(root, file)
            file_content = open(file_path, 'r')
            file_data = yaml.load(file_content.read())
            file_content.close()
            if 'classes' in file_data:
                classes = file_data.get('classes')
            else:
                classes = []
            if 'parameters' in file_data:
                if '_param' in file_data.get('parameters'):
                    parameters = file_data.get('parameters').get('_param')
                else:
                    parameters = []
            else:
                parameters = []
            name = file.replace('.yml', '')
            host_name = name.split('.')[0]
            domain_name = '.'.join(name.split('.')[1:])
            path = root.replace(RECLASS_NODES_DIR+'/', '')
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
