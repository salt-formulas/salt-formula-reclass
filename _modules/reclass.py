# -*- coding: utf-8 -*-
'''
Module for handling reclass metadata models.

'''

from __future__ import absolute_import

import io
import json
import logging
import os
import socket
import sys
import six
import yaml
import re

import urlparse

from reclass import get_storage, output
from reclass.adapters.salt import ext_pillar
from reclass.core import Core
from reclass.config import find_and_read_configfile
from string import Template
from reclass.errors import ReclassException


LOG = logging.getLogger(__name__)


def __virtual__():
    '''
    Only load this module if reclass
    is installed on this minion.
    '''
    return 'reclass'


def _deps(ret_classes=True, ret_errors=False):
    '''
    Returns classes if ret_classes=True, else returns soft_params if ret_classes=False
    '''
    defaults = find_and_read_configfile()
    path = defaults.get('inventory_base_uri')
    classes = {}
    soft_params = {}
    errors = []

    # find classes
    for root, dirs, files in os.walk(path):
        if 'init.yml' in files:
            class_file = root + '/' + 'init.yml'
            class_name = class_file.replace(path, '')[:-9].replace('/', '.')
            classes[class_name] = {'file': class_file}

        for f in files:
            if f.endswith('.yml') and f != 'init.yml':
                class_file = root + '/' + f
                class_name = class_file.replace(path, '')[:-4].replace('/', '.')
                classes[class_name] = {'file': class_file}

    # read classes
    for class_name, params in classes.items():
        with open(params['file'], 'r') as f:
            # read raw data
            raw = f.read()
            pr = re.findall('\${_param:(.*?)}', raw)
            if pr:
                params['params_required'] = list(set(pr))

            # load yaml
            try:
                data = yaml.load(raw)
            except yaml.scanner.ScannerError as e:
                errors.append(params['file'] + ' ' + str(e))
                pass

            if type(data) == dict:
                if data.get('classes'):
                    params['includes'] = data.get('classes', [])
                if data.get('parameters') and data['parameters'].get('_param'):
                    params['params_created'] = data['parameters']['_param']

                if not(data.get('classes') or data.get('parameters')):
                    errors.append(params['file'] + ' ' + 'file missing classes and parameters')
            else:
                errors.append(params['file'] + ' ' + 'is not valid yaml')

    if ret_classes:
        return classes
    elif ret_errors:
        return errors

    # find parameters and its usage
    for class_name, params in classes.items():
        for pn, pv in params.get('params_created', {}).items():
            # create param if missing
            if pn not in soft_params:
                soft_params[pn] = {'created_at': {}, 'required_at': []}

            # add created_at
            if class_name not in soft_params[pn]['created_at']:
                soft_params[pn]['created_at'][class_name] = pv

        for pn in params.get('params_required', []):
            # create param if missing
            if pn not in soft_params:
                soft_params[pn] = {'created_at': {}, 'required_at': []}

            # add created_at
            soft_params[pn]['required_at'].append(class_name)

    return soft_params


def _get_nodes_dir():
    defaults = find_and_read_configfile()
    return defaults.get('nodes_uri') or \
        os.path.join(defaults.get('inventory_base_uri'), 'nodes')


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


def soft_meta_list():
    '''
    Returns all defined soft metadata parameters.

    CLI Examples:

    .. code-block:: bash

        salt '*' reclass.soft_meta_list
    '''
    return _deps(ret_classes=False)


def class_list():
    '''
    Returns list of all classes defined within reclass inventory.

    CLI Examples:

    .. code-block:: bash

        salt '*' reclass.class_list
    '''
    return _deps(ret_classes=True)


def soft_meta_get(name):
    '''
    Returns single soft metadata parameter.

    :param name: expects the following format: apt_mk_version

    CLI Examples:

    .. code-block:: bash

        salt '*' reclass.soft_meta_get openstack_version
    '''
    soft_params = _deps(ret_classes=False)

    if name in soft_params:
        return {name: soft_params.get(name)}
    else:
        return {'Error': 'No param {0} found'.format(name)}


def class_get(name):
    '''
    Returns detailes information about class file in reclass inventory.

    :param name: expects the following format classes.system.linux.repo

    CLI Examples:

    .. code-block:: bash

        salt '*' reclass.class_get classes.system.linux.repo
    '''
    classes = _deps(ret_classes=True)
    tmp_name = '.' + name
    if tmp_name in classes:
        return {name: classes.get(tmp_name)}
    else:
        return {'Error': 'No class {0} found'.format(name)}


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


def _is_valid_ipv4_address(address):
    try:
        socket.inet_pton(socket.AF_INET, address)
    except AttributeError:
        try:
            socket.inet_aton(address)
        except socket.error:
            return False
        return address.count('.') == 3
    except socket.error:
        return False
    return True


def _is_valid_ipv6_address(address):
    try:
        socket.inet_pton(socket.AF_INET6, address)
    except socket.error:
        return False
    return True


def _get_grains(*args, **kwargs):
    res = __salt__['saltutil.cmd'](tgt='*',
                                   fun='grains.item',
                                   arg=args,
                                   **{'timeout': 10})
    return res or {}


def _guess_host_from_target(network_grains, host, domain=' '):
    '''
    Guess minion ID from given host and domain arguments. Host argument can contain
    hostname, FQDN, IPv4 or IPv6 addresses.
    '''
    key = None
    value = None

    if _is_valid_ipv4_address(host):
        key = 'ipv4'
        value = host
    elif _is_valid_ipv6_address(host):
        key = 'ipv6'
        value = host
    elif host.endswith(domain):
        key = 'fqdn'
        value = host
    else:
        key = 'fqdn'
        value = '%s.%s' % (host, domain)

    target = None
    if network_grains and isinstance(network_grains, dict) and key and value:
        for minion, grains in network_grains.items():
            if grains.get('retcode', 1) == 0 and value in grains.get('ret', {}).get(key, ''):
                target = minion

    return target or host


def _interpolate_graph_data(graph_data, **kwargs):
    new_nodes = []
    network_grains = _get_grains('ipv4', 'ipv6', 'fqdn')
    for node in graph_data:
        if not node.get('relations', []):
            node['relations'] = []
        for relation in node.get('relations', []):
            if not relation.get('status', None):
                relation['status'] = 'unknown'
            if relation.get('host_from_target', None):
                host = _guess_host_from_target(network_grains, relation.pop('host_from_target'))
                relation['host'] = host
            if relation.get('host_external', None):
                parsed_host_external = [urlparse.urlparse(item).netloc
                                        for item
                                        in relation.get('host_external', '').split(' ')
                                        if urlparse.urlparse(item).netloc]
                service = parsed_host_external[0] if parsed_host_external else ''
                host = relation.get('service', '')
                relation['host'] = host
                del relation['host_external']
                relation['service'] = service
                host_list = [n.get('host', '') for n in graph_data + new_nodes]
                service_list = [n.get('service', '') for n in graph_data + new_nodes if host in n.get('host', '')]
                if host not in host_list or (host in host_list and service not in service_list):
                    new_node = {
                        'host': host,
                        'service': service,
                        'type': relation.get('type', ''),
                        'relations': []
                    }
                    new_nodes.append(new_node)

    graph_data = graph_data + new_nodes

    return graph_data


def _grain_graph_data(*args, **kwargs):
    ret = _get_grains('salt:graph')
    graph_data = []
    for minion_ret in ret.values():
        if minion_ret.get('retcode', 1) == 0:
            graph_datum = minion_ret.get('ret', {}).get('salt:graph', [])
            graph_data = graph_data + graph_datum

    graph_nodes = _interpolate_graph_data(graph_data)
    graph = {}

    for node in graph_nodes:
        if node.get('host') not in graph:
            graph[node.get('host')] = {}
        graph[node.pop('host')][node.pop('service')] = node

    return {'graph': graph}


def _pillar_graph_data(*args, **kwargs):
    graph = {}
    nodes = inventory()
    for node, node_data in nodes.items():
        for role in node_data.get('roles', []):
            if node not in graph:
                graph[node] = {}
            graph[node][role] = {'relations': []}

    return {'graph': graph}


def graph_data(*args, **kwargs):
    '''
    Returns graph data for visualization app

    CLI Examples:

    .. code-block:: bash

        salt-call reclass.graph_data
    
    '''
    pillar_data = _pillar_graph_data().get('graph')
    grain_data = _grain_graph_data().get('graph')

    for host, services in pillar_data.items():
        for service, service_data in services.items():
            grain_service = grain_data.get(host, {}).get(service, {})
            service_data.update(grain_service)

    graph = []
    for host, services in pillar_data.items():
        for service, service_data in services.items():
            additional_data = {
                'host': host,
                'service': service,
                'status': 'unknown'
            }
            service_data.update(additional_data)
            graph.append(service_data)

    for host, services in grain_data.items():
        for service, service_data in services.items():
            additional_data = {
                'host': host,
                'service': service,
                'status': 'success'
            }
            service_data.update(additional_data)
            host_list = [g.get('host', '') for g in graph]
            service_list = [g.get('service', '') for g in graph if g.get('host') == host]
            if host not in host_list or (host in host_list and service not in service_list):
                graph.append(service_data)

    return {'graph': graph}


def node_update(name, classes=None, parameters=None, **connection_args):
    '''
    Update a node metadata information, classes and parameters.

    CLI Examples:

    .. code-block:: bash

        salt '*' reclass.node_update name=nodename classes="[clas1, class2]" parameters="{param: value, another_param: another_value}"
    '''
    node = node_get(name=name)
    if node.has_key('Error'):
        LOG.debug("Error in retrieving node {0}".format(name))
        return {'Error': 'Error in retrieving node'}
    
    for name, values in node.items():
        param = values.get('parameters', {})
        path = values.get('path')
        cluster = values.get('cluster')
        environment = values.get('environment')
        write_class = values.get('classes', [])
        
    if parameters:
        param.update(parameters)
    
    if classes:
        for classe in classes:
            if not classe in write_class:
                write_class.append(classe)
    
    node_meta = _get_node_meta(name, cluster, environment, write_class, param)
    LOG.debug(node_meta)
    
    if path == None:
        file_path = os.path.join(_get_nodes_dir(), name + '.yml')
    else:
        file_path = os.path.join(_get_nodes_dir(), path, name + '.yml')
    
    with open(file_path, 'w') as node_file:
        node_file.write(yaml.safe_dump(node_meta, default_flow_style=False))
    
    return node_get(name)


def _get_node_classes(node_data, class_mapping_fragment):
    classes = []

    for value_tmpl_string in class_mapping_fragment.get('value_template', []):
        value_tmpl = Template(value_tmpl_string.replace('<<', '${').replace('>>', '}'))
        rendered_value = value_tmpl.safe_substitute(node_data)
        classes.append(rendered_value)

    for value in class_mapping_fragment.get('value', []):
        classes.append(value)

    return classes


def _get_params(node_data, class_mapping_fragment):
    params = {}

    for param_name, param in class_mapping_fragment.items():
        value = param.get('value', None)
        value_tmpl_string = param.get('value_template', None)
        if value:
            params.update({param_name: value})
        elif value_tmpl_string:
            value_tmpl = Template(value_tmpl_string.replace('<<', '${').replace('>>', '}'))
            rendered_value = value_tmpl.safe_substitute(node_data)
            params.update({param_name: rendered_value})

    return params


def _validate_condition(node_data, expressions):
    # allow string expression definition for single expression conditions
    if isinstance(expressions, six.string_types):
        expressions = [expressions]

    result = []
    for expression_tmpl_string in expressions:
        expression_tmpl = Template(expression_tmpl_string.replace('<<', '${').replace('>>', '}'))
        expression = expression_tmpl.safe_substitute(node_data)

        if expression and expression == 'all':
            result.append(True)
        elif expression:
            val_a = expression.split('__')[0]
            val_b = expression.split('__')[2]
            condition = expression.split('__')[1]
            if condition == 'startswith':
                result.append(val_a.startswith(val_b))
            elif condition == 'equals':
                result.append(val_a == val_b)

    return all(result)


def node_classify(node_name, node_data={}, class_mapping={}, **kwargs):
    '''
    CLassify node by given class_mapping dictionary

    :param node_name: node FQDN
    :param node_data: dictionary of known informations about the node
    :param class_mapping: dictionary of classes and parameters, with conditions

    '''
    # clean node_data
    node_data = {k: v for (k, v) in node_data.items() if not k.startswith('__')}

    classes = []
    node_params = {}
    cluster_params = {}
    ret = {'node_create': '', 'cluster_param': {}}

    for type_name, node_type in class_mapping.items():
        valid = _validate_condition(node_data, node_type.get('expression', ''))
        if valid:
            gen_classes = _get_node_classes(node_data, node_type.get('node_class', {}))
            classes = classes + gen_classes
            gen_node_params = _get_params(node_data, node_type.get('node_param', {}))
            node_params.update(gen_node_params)
            gen_cluster_params = _get_params(node_data, node_type.get('cluster_param', {}))
            cluster_params.update(gen_cluster_params)

    if classes:
        create_kwargs = {'name': node_name, 'path': '_generated', 'classes': classes, 'parameters': node_params}
        ret['node_create'] = node_create(**create_kwargs)

    for name, value in cluster_params.items():
        ret['cluster_param'][name] = cluster_meta_set(name, value)

    return ret


def validate_yaml():
    '''
    Returns list of all reclass YAML files that contain syntax
    errors.

    CLI Examples:

    .. code-block:: bash

        salt-call reclass.validate_yaml
    '''
    errors = _deps(ret_classes=False, ret_errors=True)
    if errors:
        ret = {'Errors': errors}
        return ret


def validate_pillar(node_name=None, **kwargs):
    '''
    Validates whether the pillar of given node is in correct state.
    If node is not specified it validates pillars of all known nodes.
    Returns error message for every node with currupted metadata.

    :param node_name: target minion ID

    CLI Examples:

    .. code-block:: bash

        salt-call reclass.validate_pillar
        salt-call reclass.validate_pillar minion-id
    '''
    if node_name is None:
        ret={}
        nodes = node_list(**kwargs)
        for node_name, node in nodes.items():
                ret.update(validate_pillar(node_name))
        return ret
    else:
        defaults = find_and_read_configfile()
        meta = ''
        error = None
        try:
            pillar = ext_pillar(node_name, {}, defaults['storage_type'], defaults['inventory_base_uri'])
        except (ReclassException, Exception) as e:
            msg = "Validation failed in %s on %s" % (repr(e), node_name)
            LOG.error(msg)
            meta = {'Error': msg}
            s = str(type(e))
            if 'yaml.scanner.ScannerError' in s:
                error = re.sub(r"\r?\n?$", "", repr(str(e)), 1)
            else:
                error = e.message
        if 'Error' in meta:
            ret = {node_name: error}
        else:
            ret = {node_name: ''}
        return ret


def node_pillar(node_name, **kwargs):
    '''
    Returns pillar metadata for given node from reclass inventory.

    :param node_name: target minion ID

    CLI Examples:

    .. code-block:: bash

        salt-call reclass.node_pillar minion_id

    '''
    defaults = find_and_read_configfile()
    pillar = ext_pillar(node_name, {}, defaults['storage_type'], defaults['inventory_base_uri'])
    output = {node_name: pillar}

    return output


def inventory(**connection_args):
    '''
    Get all nodes in inventory and their associated services/roles.

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
    '''
    List all cluster level soft metadata overrides.

    :param file_name: name of the override file, defaults to: overrides.yml

    CLI Examples:

    .. code-block:: bash

        salt-call reclass.cluster_meta_list
    '''
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
    '''
    Delete cluster level soft metadata override entry.

    :param name: name of the override entry (dictionary key)
    :param file_name: name of the override file, defaults to: overrides.yml

    CLI Examples:

    .. code-block:: bash

        salt-call reclass.cluster_meta_delete foo
    '''
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
    '''
    Create cluster level metadata override entry.

    :param name: name of the override entry (dictionary key)
    :param value: value of the override entry (dictionary value)
    :param file_name: name of the override file, defaults to: overrides.yml

    CLI Examples:

    .. code-block:: bash

        salt-call reclass.cluster_meta_set foo bar
    '''
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
    '''
    Get single cluster level override entry

    :param name: name of the override entry (dictionary key)
    :param file_name: name of the override file, defaults to: overrides.yml

    CLI Examples:

    .. code-block:: bash

        salt-call reclass.cluster_meta_get foo

    '''
    ret = {}
    path = os.path.join(_get_cluster_dir(), cluster, file_name)
    meta = __salt__['reclass.cluster_meta_list'](path, **kwargs)
    metadata = meta.get('parameters', {}).get('_param', {})
    if 'Error' in meta:
        ret['Error'] = meta['Error']
    elif name in metadata:
        ret[name] = metadata.get(name)

    return ret

