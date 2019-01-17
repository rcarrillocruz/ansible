#!/usr/bin/python
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}


DOCUMENTATION = """
---
module: checkpoint_access_layer
short_description: Manages access layer objects on Checkpoint over Web Services API
description:
  - Manages access layer objects on Checkpoint devices including creating, updating, removing access layers objects.
    All operations are performed over Web Services API.
version_added: "2.8"
author: "Ansible by Red Hat (@rcarrillocruz)"
options:
  name:
    description:
      - Name of the access rule.
    type: str
    required: True
  enable_firewall_blade:
    description:
      - Flag to enable or disable the firewall blade on the layer.
    type: bool
    default: true
  shared:
    description:
      - Flag to make the layer shared or not.
    type: bool
    required: true
  state:
    description:
      - State of the access rule (present or absent). Defaults to present.
    type: str
    default: present
  auto_publish_session:
    description:
      - Publish the current session if changes have been performed
        after task completes.
    type: bool
    default: 'yes'
  auto_install_policy:
    description:
      - Install the package policy if changes have been performed
        after the task completes.
    type: bool
    default: 'yes'
  policy_package:
    description:
      - Package policy name to be installed.
    type: bool
    default: 'standard'
  targets:
    description:
      - Targets to install the package policy on.
    type: list
"""

EXAMPLES = """
- name: Create access layer
  checkpoint_access_layer:
    name: new_layer
    enable_firewall_blade: yes

- name: Delete access layer
  checkpoint_access_layer:
    name: new_layer
    state: absent
"""

RETURN = """
checkpoint_access_layers:
  description: The checkpoint layers objects when created or updated.
  returned: always, except when deleting the access layer.
  type: list
"""


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection
from ansible.module_utils.network.checkpoint.checkpoint import checkpoint_argument_spec, publish, install_policy
import json


def get_access_layer(module, connection):
    name = module.params['name']

    payload = {'name': name}

    code, response = connection.send_request('/web_api/show-access-layer', payload)

    return code, response


def create_access_layer(module, connection):
    name = module.params['name']
    enable_firewall_blade = module.params['enable_firewall_blade']
    shared = module.params['shared']

    payload = {'name': name,
               'firewall': enable_firewall_blade,
               'shared': shared}

    code, response = connection.send_request('/web_api/add-access-layer', payload)

    return code, response


def update_access_layer(module, connection):
    name = module.params['name']
    enable_firewall_blade = module.params['enable_firewall_blade']
    shared = module.params['shared']

    payload = {'name': name,
               'firewall': enable_firewall_blade,
               'shared': shared}

    code, response = connection.send_request('/web_api/set-access-layer', payload)

    return code, response


def delete_access_layer(module, connection):
    name = module.params['name']

    payload = {'name': name}

    code, response = connection.send_request('/web_api/delete-access-layer', payload)

    return code, response


def needs_update(module, access_layer):
    res = False

    if module.params['enable_firewall_blade'] != access_layer['shared']:
        res = True

    if module.params['shared'] != access_layer['shared']:
        res = True

    return res


def main():
    argument_spec = dict(
        name=dict(type='str', required=True),
        enable_firewall_blade=dict(type='bool', default=True),
        shared=dict(type='bool', default=False),
        state=dict(type='str', default='present')
    )
    argument_spec.update(checkpoint_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec)
    connection = Connection(module._socket_path)
    code, response = get_access_layer(module, connection)
    result = {'changed': False}

    if module.params['state'] == 'present':
        if code == 200:
            if needs_update(module, response):
                code, response = update_access_layer(module, connection)

                if module.params['auto_publish_session']:
                    publish(connection)

                    if module.params['auto_install_policy']:
                        install_policy(connection, module.params['policy_package'], module.params['targets'])

                result['changed'] = True
                result['checkpoint_access_layers'] = response
            else:
                pass
        elif code == 404:
            code, response = create_access_layer(module, connection)

            if module.params['auto_publish_session']:
                publish(connection)

                if module.params['auto_install_policy']:
                    install_policy(connection, module.params['policy_package'], module.params['targets'])

            result['changed'] = True
            result['checkpoint_access_layers'] = response
    else:
        if code == 200:
            # Handle deletion
            code, response = delete_access_layer(module, connection)

            if module.params['auto_publish_session']:
                publish(connection)

                if module.params['auto_install_policy']:
                    install_policy(connection, module.params['policy_package'], module.params['targets'])

            result['changed'] = True
        elif code == 404:
            pass

    result['checkpoint_session_uid'] = connection.get_session_uid()
    module.exit_json(**result)


if __name__ == '__main__':
    main()
