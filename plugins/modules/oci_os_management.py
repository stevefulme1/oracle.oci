# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI OS Management managed instances."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_os_management
short_description: Manage OCI OS Management managed instances
description:
  - Read managed instances and perform attach/detach operations in OCI OS Management.
  - Managed instances are registered automatically and cannot be created via the API.
  - Supports attaching and detaching child software sources and managed instance groups.
version_added: "1.0.0"
author: Oracle (@oracle)
options:
  compartment_id:
    description:
      - The OCID of the compartment.
      - Used for listing managed instances.
    type: str
  managed_instance_id:
    description:
      - The OCID of the managed instance.
      - Required for all operations.
    type: str
    required: true
  display_name:
    description:
      - Filter by display name when listing.
    type: str
  software_source_id:
    description:
      - The OCID of the software source to attach or detach.
    type: str
  managed_instance_group_id:
    description:
      - The OCID of the managed instance group to attach or detach.
    type: str
  action:
    description:
      - The action to perform.
    type: str
    choices:
      - read
      - attach_software_source
      - detach_software_source
      - attach_managed_instance_group
      - detach_managed_instance_group
    default: read
  state:
    description:
      - The desired state. Only present is supported (read-only resource).
    type: str
    default: present
    choices: [present]
extends_documentation_fragment:
  - stevefulme1.oci_cloud.oci_common
"""

EXAMPLES = r"""
- name: Read a managed instance
  stevefulme1.oci_cloud.oci_os_management:
    managed_instance_id: "ocid1.instance.oc1..example"
    action: read
    state: present

- name: Attach a software source to a managed instance
  stevefulme1.oci_cloud.oci_os_management:
    managed_instance_id: "ocid1.instance.oc1..example"
    software_source_id: "ocid1.softwaresource.oc1..example"
    action: attach_software_source
    state: present

- name: Detach a software source from a managed instance
  stevefulme1.oci_cloud.oci_os_management:
    managed_instance_id: "ocid1.instance.oc1..example"
    software_source_id: "ocid1.softwaresource.oc1..example"
    action: detach_software_source
    state: present
"""

RETURN = r"""
resource:
  description: The managed instance details.
  returned: on success
  type: dict
  contains:
    display_name:
      description: The display name of the managed instance.
      type: str
    id:
      description: The OCID of the managed instance.
      type: str
    compartment_id:
      description: The OCID of the compartment.
      type: str
    os_name:
      description: The operating system name.
      type: str
    os_version:
      description: The operating system version.
      type: str
    status:
      description: The status of the managed instance.
      type: str
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_common import (
    OCI_COMMON_ARGS,
    to_dict,
)
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_auth import create_service_client
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_wait import call_with_retry

try:
    import oci
    from oci.os_management import OsManagementClient
    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False


def get_managed_instance(client, managed_instance_id):
    """Get a managed instance by OCID, return None if not found."""
    try:
        response = call_with_retry(client.get_managed_instance, managed_instance_id)
        return response.data
    except oci.exceptions.ServiceError as e:
        if e.status == 404:
            return None
        raise


def attach_software_source(module, client):
    """Attach a software source to a managed instance."""
    call_with_retry(
        client.attach_child_software_source_to_managed_instance,
        module.params["managed_instance_id"],
        module.params["software_source_id"],
    )


def detach_software_source(module, client):
    """Detach a software source from a managed instance."""
    call_with_retry(
        client.detach_child_software_source_from_managed_instance,
        module.params["managed_instance_id"],
        module.params["software_source_id"],
    )


def attach_managed_instance_group(module, client):
    """Attach a managed instance to a group."""
    call_with_retry(
        client.attach_managed_instance_to_managed_instance_group,
        module.params["managed_instance_group_id"],
        module.params["managed_instance_id"],
    )


def detach_managed_instance_group(module, client):
    """Detach a managed instance from a group."""
    call_with_retry(
        client.detach_managed_instance_from_managed_instance_group,
        module.params["managed_instance_group_id"],
        module.params["managed_instance_id"],
    )


def run_module():
    """Main module execution."""
    module_args = dict(
        compartment_id=dict(type="str"),
        managed_instance_id=dict(type="str", required=True),
        display_name=dict(type="str"),
        software_source_id=dict(type="str"),
        managed_instance_group_id=dict(type="str"),
        action=dict(
            type="str",
            default="read",
            choices=[
                "read",
                "attach_software_source",
                "detach_software_source",
                "attach_managed_instance_group",
                "detach_managed_instance_group",
            ],
        ),
        state=dict(type="str", default="present", choices=["present"]),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            ("action", "attach_software_source", ("software_source_id",)),
            ("action", "detach_software_source", ("software_source_id",)),
            ("action", "attach_managed_instance_group", ("managed_instance_group_id",)),
            ("action", "detach_managed_instance_group", ("managed_instance_group_id",)),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, OsManagementClient)
    action = module.params.get("action", "read")
    managed_instance_id = module.params["managed_instance_id"]

    instance = get_managed_instance(client, managed_instance_id)
    if instance is None:
        module.fail_json(msg="Managed instance not found: %s" % managed_instance_id)

    if action == "read":
        module.exit_json(changed=False, resource=to_dict(instance))
        return

    if module.check_mode:
        module.exit_json(changed=True)

    action_map = {
        "attach_software_source": attach_software_source,
        "detach_software_source": detach_software_source,
        "attach_managed_instance_group": attach_managed_instance_group,
        "detach_managed_instance_group": detach_managed_instance_group,
    }

    action_func = action_map.get(action)
    if action_func:
        action_func(module, client)

    instance = get_managed_instance(client, managed_instance_id)
    module.exit_json(changed=True, resource=to_dict(instance))


def main():
    run_module()


if __name__ == "__main__":
    main()
