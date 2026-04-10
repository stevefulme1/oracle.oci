#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI instance console connections."""

from __future__ import annotations

DOCUMENTATION = r"""
---
module: oci_console_connection
short_description: Manage OCI instance console connections
description:
  - Create and delete instance console connections in Oracle Cloud Infrastructure.
  - Console connections provide serial console and VNC access to compute instances.
  - Uses the OCI Compute service via C(oci.core.ComputeClient).
version_added: "1.0.0"
author:
  - Oracle (@oracle)
options:
  instance_id:
    description:
      - The OCID of the instance to create the console connection for.
      - Required when creating a new console connection.
    type: str
  public_key:
    description:
      - The SSH public key used to authenticate the console connection.
      - Required when creating a new console connection.
    type: str
  console_connection_id:
    description:
      - The OCID of the console connection.
      - Required when deleting a console connection.
    type: str
  state:
    description:
      - The desired state of the console connection.
    type: str
    choices: [present, absent]
    default: present
extends_documentation_fragment:
  - oracle.oci.oci_common
"""

EXAMPLES = r"""
- name: Create an instance console connection
  oracle.oci.oci_console_connection:
    instance_id: "ocid1.instance.oc1.phx.example"
    public_key: "ssh-rsa AAAA..."
    state: present
  register: result

- name: Delete an instance console connection
  oracle.oci.oci_console_connection:
    console_connection_id: "ocid1.instanceconsoleconnection.oc1.phx.example"
    state: absent

- name: Create console connection and display connection strings
  oracle.oci.oci_console_connection:
    instance_id: "ocid1.instance.oc1.phx.example"
    public_key: "{{ lookup('file', '~/.ssh/id_rsa.pub') }}"
    state: present
  register: console

- name: Show serial console connection command
  ansible.builtin.debug:
    var: console.resource.connection_string

- name: Show VNC connection command
  ansible.builtin.debug:
    var: console.resource.vnc_connection_string
"""

RETURN = r"""
resource:
  description: The console connection details.
  returned: on success
  type: dict
  sample:
    id: "ocid1.instanceconsoleconnection.oc1.phx.example"
    instance_id: "ocid1.instance.oc1.phx.example"
    lifecycle_state: "ACTIVE"
    compartment_id: "ocid1.compartment.oc1..example"
    connection_string: "ssh -o ProxyCommand='ssh -W %h:%p ...' ocid1.instance..."
    vnc_connection_string: "ssh -o ProxyCommand='ssh -W %h:%p ...' -L 5900:localhost:5900 ..."
    fingerprint: "SHA256:..."
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.oracle.oci.plugins.module_utils.oci_common import (
    OCI_COMMON_ARGS,
    LIFECYCLE_ACTIVE,
    LIFECYCLE_DELETED,
    LIFECYCLE_FAILED,
)
from ansible_collections.oracle.oci.plugins.module_utils.oci_resource import OciResourceBase
from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import (
    call_with_retry,
    wait_for_resource,
)

try:
    import oci
    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False


class OciConsoleConnection(OciResourceBase):
    """Manage OCI instance console connections."""

    def __init__(self, module):
        self.client_class = oci.core.ComputeClient
        super().__init__(module)

    def get_resource(self):
        console_connection_id = self.module.params.get("console_connection_id")
        if not console_connection_id:
            # Try to find an existing active console connection for the instance
            instance_id = self.module.params.get("instance_id")
            if instance_id:
                return self._find_active_connection(instance_id)
            return None
        try:
            response = self.client.get_instance_console_connection(console_connection_id)
            resource = response.data
            if resource.lifecycle_state == LIFECYCLE_DELETED:
                return None
            return resource
        except oci.exceptions.ServiceError as e:
            if e.status == 404:
                return None
            raise

    def _find_active_connection(self, instance_id):
        """Find an existing active console connection for the given instance."""
        try:
            response = self.client.list_instance_console_connections(
                compartment_id=None,
                instance_id=instance_id,
            )
            for conn in response.data:
                if conn.lifecycle_state == LIFECYCLE_ACTIVE:
                    return conn
        except oci.exceptions.ServiceError:
            pass
        return None

    def create_resource(self):
        params = self.module.params
        create_details = oci.core.models.CreateInstanceConsoleConnectionDetails(
            instance_id=params["instance_id"],
            public_key=params["public_key"],
        )

        freeform_tags, defined_tags = self.get_tags()
        if freeform_tags:
            create_details.freeform_tags = freeform_tags
        if defined_tags:
            create_details.defined_tags = defined_tags

        response = call_with_retry(
            self.client.create_instance_console_connection, create_details,
        )
        connection = response.data

        if self.module.params.get("wait", True):
            connection = wait_for_resource(
                self.module,
                self.client.get_instance_console_connection,
                connection.id,
                target_states={LIFECYCLE_ACTIVE},
                failure_states={LIFECYCLE_FAILED, LIFECYCLE_DELETED},
            )
        return connection

    def update_resource(self, resource):
        # Console connections do not support updates
        return resource

    def delete_resource(self, resource):
        call_with_retry(
            self.client.delete_instance_console_connection, resource.id,
        )
        if self.module.params.get("wait", True):
            wait_for_resource(
                self.module,
                self.client.get_instance_console_connection,
                resource.id,
                target_states={LIFECYCLE_DELETED},
            )

    def _updatable_attributes(self):
        return []


def main():
    module_args = dict(
        instance_id=dict(type="str"),
        public_key=dict(type="str", no_log=False),
        console_connection_id=dict(type="str"),
        state=dict(type="str", default="present", choices=["present", "absent"]),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            ("state", "present", ("instance_id", "public_key")),
            ("state", "absent", ("console_connection_id",)),
        ],
    )

    oci_conn = OciConsoleConnection(module)
    oci_conn.run()


if __name__ == "__main__":
    main()
