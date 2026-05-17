# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI compute image capability schemas."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_compute_image_capability_schema
short_description: Manage OCI Compute Image Capability Schemas
description:
    - Create, update, and delete compute image capability schemas in Oracle Cloud Infrastructure.
    - This module uses the OCI Python SDK.
version_added: "2.2.0"
author:
    - Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment.
            - Required when creating a new compute image capability schema.
        type: str
    compute_image_capability_schema_id:
        description:
            - The OCID of the compute image capability schema.
            - Required for update and delete operations.
        type: str
    display_name:
        description:
            - The display name of the compute image capability schema.
        type: str
    compute_global_image_capability_schema_version_name:
        description:
            - The name of the compute global image capability schema version.
        type: str
    image_id:
        description:
            - The OCID of the image.
        type: str
    schema_data:
        description:
            - The map of each capability name to its ImageCapabilitySchemaDescriptor.
        type: dict
    state:
        description:
            - The desired state of the compute image capability schema.
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
- name: Create a compute image capability schema
  stevefulme1.oci_cloud.oci_compute_image_capability_schema:
    compartment_id: "ocid1.compartment.oc1..example"
    display_name: "my-compute-image-capability-schema"
    state: present

- name: Delete a compute image capability schema
  stevefulme1.oci_cloud.oci_compute_image_capability_schema:
    compute_image_capability_schema_id: "ocid1.compute_image_capability_schema.oc1..example"
    state: absent
"""

RETURN = r"""
compute_image_capability_schema:
    description: Details of the compute image capability schema.
    returned: On success when state is present.
    type: dict
    sample:
        id: "ocid1.compute_image_capability_schema.oc1..example"
        display_name: "my-compute-image-capability-schema"
        lifecycle_state: "ACTIVE"
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from oci.core import ComputeClient
    from oci.core.models import (
        CreateComputeImageCapabilitySchemaDetails,
        UpdateComputeImageCapabilitySchemaDetails,
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
    """Build module argument spec."""
    module_args = dict(
        compartment_id=dict(type="str"),
        compute_image_capability_schema_id=dict(type="str"),
        display_name=dict(type="str"),
        compute_global_image_capability_schema_version_name=dict(type="str"),
        image_id=dict(type="str"),
        schema_data=dict(type="dict"),
        state=dict(type="str", choices=["present", "absent"], default="present"),
    )
    module_args.update(OCI_COMMON_ARGS)
    return module_args


def get_resource(client, resource_id):
    """Get a compute image capability schema by OCID."""
    try:
        response = call_with_retry(client.get_compute_image_capability_schema, resource_id)
        return response.data
    except ServiceError as e:
        if e.status == 404:
            return None
        raise


def find_resource(client, compartment_id, display_name):
    """Find a compute image capability schema by display name in a compartment."""
    if not compartment_id:
        return None
    try:
        response = call_with_retry(
            client.list_compute_image_capability_schemas, compartment_id=compartment_id,
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
    """Create a new compute image capability schema."""
    params = module.params
    create_details = CreateComputeImageCapabilitySchemaDetails(
        compartment_id=params.get("compartment_id"),
        display_name=params.get("display_name"),
        image_id=params.get("image_id"),
        compute_global_image_capability_schema_version_name=params.get(
            "compute_global_image_capability_schema_version_name"
        ),
        schema_data=params.get("schema_data"),
        freeform_tags=params.get("freeform_tags"),
        defined_tags=params.get("defined_tags"),
    )
    response = call_with_retry(client.create_compute_image_capability_schema, create_details)
    resource = response.data
    if hasattr(resource, "id") and module.params.get("wait", True):
        resource = wait_for_resource(
            module, client.get_compute_image_capability_schema, resource.id, target_states=READY_STATES,
        )
    return resource


def update_resource(module, client, existing):
    """Update an existing compute image capability schema."""
    params = module.params
    update_details = UpdateComputeImageCapabilitySchemaDetails(
        display_name=params.get("display_name"),
        schema_data=params.get("schema_data"),
        freeform_tags=params.get("freeform_tags"),
        defined_tags=params.get("defined_tags"),
    )
    response = call_with_retry(client.update_compute_image_capability_schema, existing.id, update_details)
    resource = response.data
    if hasattr(resource, "id") and module.params.get("wait", True):
        resource = wait_for_resource(
            module, client.get_compute_image_capability_schema, resource.id, target_states=READY_STATES,
        )
    return resource


def delete_resource(module, client, existing):
    """Delete a compute image capability schema."""
    call_with_retry(client.delete_compute_image_capability_schema, existing.id)
    if module.params.get("wait", True):
        wait_for_resource(
            module, client.get_compute_image_capability_schema, existing.id, target_states=DEAD_STATES,
        )


def needs_update(params, existing):
    """Check if resource attributes differ from desired state."""
    updatable = ["display_name"]
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

    client = create_service_client(module, ComputeClient)
    params = module.params
    state = params["state"]

    existing = None
    if params.get("compute_image_capability_schema_id"):
        existing = get_resource(client, params["compute_image_capability_schema_id"])
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
        module.exit_json(changed=True, compute_image_capability_schema=to_dict(resource))
        return

    if needs_update(params, existing):
        if module.check_mode:
            module.exit_json(changed=True)
        resource = update_resource(module, client, existing)
        module.exit_json(changed=True, compute_image_capability_schema=to_dict(resource))
        return

    module.exit_json(changed=False, compute_image_capability_schema=to_dict(existing))


if __name__ == "__main__":
    main()
