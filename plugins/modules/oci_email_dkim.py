# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI dkims."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_email_dkim
short_description: Manage OCI Dkims
description:
    - Create, update, and delete dkims in Oracle Cloud Infrastructure.
    - This module uses the OCI Python SDK.
version_added: "2.2.0"
author:
    - Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment.
            - Required when creating a new dkim.
        type: str
    dkim_id:
        description:
            - The OCID of the dkim.
            - Required for update and delete operations.
        type: str
    display_name:
        description:
            - The display name of the dkim.
        type: str
    email_domain_id:
        description:
            - The OCID of the email domain.
        type: str
    name:
        description:
            - Name for the DKIM record.
        type: str
    description:
        description:
            - Description for the DKIM record.
        type: str
    state:
        description:
            - The desired state of the dkim.
        type: str
        choices:
            - present
            - absent
        default: present
extends_documentation_fragment:
    - stevefulme1.oci_cloud.oci_common
requirements:
    - "python >= 3.8"
    - "oci >= 2.90.0"
"""

EXAMPLES = r"""
- name: Create a dkim
  stevefulme1.oci_cloud.oci_email_dkim:
    compartment_id: "ocid1.compartment.oc1..example"
    display_name: "my-dkim"
    state: present

- name: Delete a dkim
  stevefulme1.oci_cloud.oci_email_dkim:
    dkim_id: "ocid1.dkim.oc1..example"
    state: absent
"""

RETURN = r"""
dkim:
    description: Details of the dkim.
    returned: On success when state is present.
    type: dict
    sample:
        id: "ocid1.dkim.oc1..example"
        display_name: "my-dkim"
        lifecycle_state: "ACTIVE"
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from oci.email import EmailClient
    from oci.email.models import CreateDkimDetails
    from oci.exceptions import ServiceError
    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False

from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_common import (
    OCI_COMMON_ARGS,
    DEAD_STATES,
    READY_STATES,
    to_dict,
)
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_auth import create_service_client
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_wait import (
    call_with_retry,
    wait_for_resource,
)


def get_module_args():
    """Build module argument spec."""
    module_args = dict(
        compartment_id=dict(type="str"),
        dkim_id=dict(type="str"),
        display_name=dict(type="str"),
        email_domain_id=dict(type="str"),
        name=dict(type="str"),
        description=dict(type="str"),
        state=dict(type="str", choices=["present", "absent"], default="present"),
    )
    module_args.update(OCI_COMMON_ARGS)
    return module_args


def get_resource(client, resource_id):
    """Get a dkim by OCID."""
    try:
        response = call_with_retry(client.get_dkim, resource_id)
        return response.data
    except ServiceError as e:
        if e.status == 404:
            return None
        raise


def find_resource(client, compartment_id, display_name):
    """Find a dkim by display name in a compartment."""
    if not compartment_id:
        return None
    try:
        response = call_with_retry(
            client.list_dkims, compartment_id=compartment_id,
        )
        for item in response.data.items:
            if getattr(item, "lifecycle_state", None) in DEAD_STATES:
                continue
            if display_name and getattr(item, "display_name", None) == display_name:
                return item
    except ServiceError:
        pass
    return None


def create_resource(module, client):
    """Create a new dkim."""
    params = module.params
    create_details = CreateDkimDetails(
        email_domain_id=params.get("email_domain_id"),
        name=params.get("name"),
        description=params.get("description"),
        freeform_tags=params.get("freeform_tags"),
        defined_tags=params.get("defined_tags"),
    )
    response = call_with_retry(client.create_dkim, create_details)
    resource = response.data
    if hasattr(resource, "id") and module.params.get("wait", True):
        resource = wait_for_resource(
            module, client.get_dkim, resource.id, target_states=READY_STATES,
        )
    return resource


def delete_resource(module, client, existing):
    """Delete a dkim."""
    call_with_retry(client.delete_dkim, existing.id)
    if module.params.get("wait", True):
        wait_for_resource(
            module, client.get_dkim, existing.id, target_states=DEAD_STATES,
        )


def needs_update(params, existing):
    """Check if resource attributes differ from desired state."""
    updatable = []
    for attr in updatable:
        desired = params.get(attr)
        if desired is None:
            continue
        current = getattr(existing, attr, None)
        if current != desired:
            return True
    if params.get("freeform_tags") is not None:
        if getattr(existing, "freeform_tags", None) != params["freeform_tags"]:
            return True
    if params.get("defined_tags") is not None:
        if getattr(existing, "defined_tags", None) != params["defined_tags"]:
            return True
    return False


def main():
    module = AnsibleModule(
        argument_spec=get_module_args(),
        supports_check_mode=True,
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, EmailClient)
    params = module.params
    state = params["state"]

    existing = None
    if params.get("dkim_id"):
        existing = get_resource(client, params["dkim_id"])
    elif params.get("compartment_id"):
        existing = find_resource(client, params["compartment_id"], params.get("display_name"))

    if state == "absent":
        if existing is None:
            module.exit_json(changed=False)
        if module.check_mode:
            module.exit_json(changed=True)
        delete_resource(module, client, existing)
        module.exit_json(changed=True)
        return

    if existing is None:
        if module.check_mode:
            module.exit_json(changed=True)
        resource = create_resource(module, client)
        module.exit_json(changed=True, dkim=to_dict(resource))
        return

    module.exit_json(changed=False, dkim=to_dict(existing))


if __name__ == "__main__":
    main()
