# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Functions Applications."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_functions_application
short_description: Manage Functions Applications in OCI
description:
    - Create, update, and delete Functions Applications in Oracle Cloud Infrastructure.
    - This module uses the OCI Python SDK C(oci.functions.FunctionsManagementClient).
version_added: "1.0.0"
author:
    - Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment to contain the application.
            - Required when creating a new application.
        type: str
    application_id:
        description:
            - The OCID of an existing application.
            - Required for update and delete operations.
        type: str
    display_name:
        description:
            - The display name of the application.
            - Required when creating a new application.
        type: str
    subnet_ids:
        description:
            - List of subnet OCIDs for the application.
            - Required when creating a new application.
        type: list
        elements: str
    config:
        description:
            - Application configuration as key-value pairs.
        type: dict
    syslog_url:
        description:
            - A syslog URL to send application logs to.
        type: str
    state:
        description:
            - The desired state of the application.
        type: str
        choices:
            - present
            - absent
        default: present
    wait:
        description:
            - Whether to wait for the resource to reach the desired state.
        type: bool
        default: true
    wait_timeout:
        description:
            - Maximum time in seconds to wait for the resource to reach the desired state.
        type: int
        default: 1200
extends_documentation_fragment:
    - stevefulme1.oci_cloud.oci_common
requirements:
    - "python >= 3.8"
    - "oci >= 2.90.0"
"""

EXAMPLES = r"""
- name: Create a Functions application
  stevefulme1.oci_cloud.oci_functions_application:
    compartment_id: "ocid1.compartment.oc1..example"
    display_name: "my-fn-app"
    subnet_ids:
      - "ocid1.subnet.oc1..example"
    state: present

- name: Delete a Functions application
  stevefulme1.oci_cloud.oci_functions_application:
    application_id: "ocid1.fnapp.oc1..example"
    state: absent
"""

RETURN = r"""
functions_application:
    description: Details of the Functions application.
    returned: On success when state is present.
    type: dict
    sample:
        id: "ocid1.fnapp.oc1..example"
        display_name: "my-fn-app"
        lifecycle_state: "ACTIVE"
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from oci.functions import FunctionsManagementClient
    from oci.functions.models import (
        CreateApplicationDetails,
        UpdateApplicationDetails,
    )
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
    module_args = dict(
        compartment_id=dict(type="str"),
        application_id=dict(type="str"),
        display_name=dict(type="str"),
        subnet_ids=dict(type="list", elements="str"),
        config=dict(type="dict"),
        syslog_url=dict(type="str"),
        state=dict(type="str", choices=["present", "absent"], default="present"),
    )
    module_args.update(OCI_COMMON_ARGS)
    return module_args


def get_resource(client, resource_id):
    try:
        response = call_with_retry(client.get_application, resource_id)
        return response.data
    except ServiceError as e:
        if e.status == 404:
            return None
        raise


def find_resource(client, compartment_id, display_name):
    if not compartment_id:
        return None
    try:
        response = call_with_retry(
            client.list_applications, compartment_id=compartment_id,
        )
        for item in response.data:
            if item.lifecycle_state in DEAD_STATES:
                continue
            if display_name and item.display_name == display_name:
                return item
    except ServiceError:
        pass
    return None


def create_resource(module, client):
    params = module.params
    create_details = CreateApplicationDetails(
        compartment_id=params["compartment_id"],
        display_name=params["display_name"],
        subnet_ids=params["subnet_ids"],
        config=params.get("config"),
        syslog_url=params.get("syslog_url"),
        freeform_tags=params.get("freeform_tags"),
        defined_tags=params.get("defined_tags"),
    )
    response = call_with_retry(client.create_application, create_details)
    resource = response.data
    resource = wait_for_resource(
        module, client.get_application, resource.id, target_states=READY_STATES,
    )
    return resource


def update_resource(module, client, existing):
    params = module.params
    update_details = UpdateApplicationDetails(
        config=params.get("config"),
        syslog_url=params.get("syslog_url"),
        freeform_tags=params.get("freeform_tags"),
        defined_tags=params.get("defined_tags"),
    )
    response = call_with_retry(client.update_application, existing.id, update_details)
    resource = response.data
    resource = wait_for_resource(
        module, client.get_application, resource.id, target_states=READY_STATES,
    )
    return resource


def delete_resource(module, client, existing):
    call_with_retry(client.delete_application, existing.id)
    wait_for_resource(
        module, client.get_application, existing.id, target_states=DEAD_STATES,
    )


def needs_update(params, existing):
    updatable = ["syslog_url"]
    for attr in updatable:
        desired = params.get(attr)
        if desired is None:
            continue
        current = getattr(existing, attr, None)
        if current != desired:
            return True
    if params.get("config") is not None:
        if getattr(existing, "config", None) != params["config"]:
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
        required_if=[
            ("state", "present", ("compartment_id", "display_name", "subnet_ids"), True),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, FunctionsManagementClient)
    params = module.params
    state = params["state"]

    existing = None
    if params.get("application_id"):
        existing = get_resource(client, params["application_id"])
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
        for req in ("compartment_id", "display_name", "subnet_ids"):
            if not params.get(req):
                module.fail_json(msg=f"Parameter '{req}' is required to create a Functions application.")
        if module.check_mode:
            module.exit_json(changed=True)
        resource = create_resource(module, client)
        module.exit_json(changed=True, functions_application=to_dict(resource))
        return

    if needs_update(params, existing):
        if module.check_mode:
            module.exit_json(changed=True)
        resource = update_resource(module, client, existing)
        module.exit_json(changed=True, functions_application=to_dict(resource))
        return

    module.exit_json(changed=False, functions_application=to_dict(existing))


if __name__ == "__main__":
    main()
