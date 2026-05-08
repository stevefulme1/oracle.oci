# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI VMware Solution SDDCs."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_ocvp_sddc
short_description: Manage VMware Solution SDDCs in OCI
description:
    - Create, update, and delete Oracle Cloud VMware Solution SDDCs in Oracle Cloud Infrastructure.
    - This module uses the OCI Python SDK C(oci.ocvp.SddcClient).
version_added: "2.0.0"
author:
    - Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment to contain the SDDC.
            - Required when creating a new SDDC.
        type: str
    sddc_id:
        description:
            - The OCID of an existing SDDC.
            - Required for update and delete operations.
        type: str
    display_name:
        description:
            - The display name of the SDDC.
        type: str
    vmware_software_version:
        description:
            - The VMware software version for the SDDC.
        type: str
    ssh_authorized_keys:
        description:
            - One or more public SSH keys for the default ESXi hosts access.
        type: str
    compute_availability_domain:
        description:
            - The availability domain for the SDDC compute instances.
        type: str
    esxi_hosts_count:
        description:
            - The number of ESXi hosts to create in the SDDC.
        type: int
    provisioning_subnet_id:
        description:
            - The OCID of the management subnet for provisioning the SDDC.
        type: str
    initial_configuration:
        description:
            - Initial cluster configuration details for the SDDC.
        type: dict
    state:
        description:
            - The desired state of the SDDC.
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
- name: Create a VMware SDDC
  stevefulme1.oci_cloud.oci_ocvp_sddc:
    compartment_id: "ocid1.compartment.oc1..example"
    display_name: "my-sddc"
    vmware_software_version: "7.0 update 3"
    ssh_authorized_keys: "ssh-rsa AAAA..."
    compute_availability_domain: "Uocm:PHX-AD-1"
    esxi_hosts_count: 3
    provisioning_subnet_id: "ocid1.subnet.oc1..example"
    state: present

- name: Delete a VMware SDDC
  stevefulme1.oci_cloud.oci_ocvp_sddc:
    sddc_id: "ocid1.sddc.oc1..example"
    state: absent
"""

RETURN = r"""
sddc:
    description: Details of the SDDC.
    returned: On success when state is present.
    type: dict
    sample:
        id: "ocid1.sddc.oc1..example"
        display_name: "my-sddc"
        lifecycle_state: "ACTIVE"
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from oci.ocvp import SddcClient
    from oci.ocvp.models import (
        CreateSddcDetails,
        UpdateSddcDetails,
    )
    from oci.exceptions import ServiceError

    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False

from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_common import (
    OCI_COMMON_ARGS,
    DEAD_STATES,
    READY_STATES,
)
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_auth import create_service_client
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_wait import (
    call_with_retry,
    wait_for_resource,
)


def get_module_args():
    module_args = dict(
        compartment_id=dict(type="str"),
        sddc_id=dict(type="str"),
        display_name=dict(type="str"),
        vmware_software_version=dict(type="str"),
        ssh_authorized_keys=dict(type="str"),
        compute_availability_domain=dict(type="str"),
        esxi_hosts_count=dict(type="int"),
        provisioning_subnet_id=dict(type="str"),
        initial_configuration=dict(type="dict"),
        state=dict(type="str", choices=["present", "absent"], default="present"),
    )
    module_args.update(OCI_COMMON_ARGS)
    return module_args


def to_dict(resource):
    if resource is None:
        return {}
    if hasattr(resource, "__dict__"):
        result = {}
        for key, value in resource.__dict__.items():
            if key.startswith("_"):
                continue
            if isinstance(value, list):
                result[key] = [to_dict(i) if hasattr(i, "__dict__") else i for i in value]
            elif hasattr(value, "__dict__") and not isinstance(value, (str, int, float, bool, dict)):
                result[key] = to_dict(value)
            else:
                result[key] = value
        return result
    return resource


def get_resource(client, resource_id):
    try:
        response = call_with_retry(client.get_sddc, resource_id)
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
            client.list_sddcs, compartment_id=compartment_id,
        )
        for item in response.data.items:
            if item.lifecycle_state in DEAD_STATES:
                continue
            if display_name and item.display_name == display_name:
                return item
    except ServiceError:
        pass
    return None


def create_resource(module, client):
    params = module.params
    create_details = CreateSddcDetails(
        compartment_id=params["compartment_id"],
        display_name=params.get("display_name"),
        vmware_software_version=params.get("vmware_software_version"),
        ssh_authorized_keys=params.get("ssh_authorized_keys"),
        compute_availability_domain=params.get("compute_availability_domain"),
        esxi_hosts_count=params.get("esxi_hosts_count"),
        provisioning_subnet_id=params.get("provisioning_subnet_id"),
        initial_configuration=params.get("initial_configuration"),
        freeform_tags=params.get("freeform_tags"),
        defined_tags=params.get("defined_tags"),
    )
    response = call_with_retry(client.create_sddc, create_details)
    resource = response.data
    resource = wait_for_resource(
        module, client.get_sddc, resource.id, target_states=READY_STATES,
    )
    return resource


def update_resource(module, client, existing):
    params = module.params
    update_details = UpdateSddcDetails(
        display_name=params.get("display_name"),
        vmware_software_version=params.get("vmware_software_version"),
        ssh_authorized_keys=params.get("ssh_authorized_keys"),
        freeform_tags=params.get("freeform_tags"),
        defined_tags=params.get("defined_tags"),
    )
    response = call_with_retry(client.update_sddc, existing.id, update_details)
    resource = response.data
    resource = wait_for_resource(
        module, client.get_sddc, resource.id, target_states=READY_STATES,
    )
    return resource


def delete_resource(module, client, existing):
    call_with_retry(client.delete_sddc, existing.id)
    wait_for_resource(
        module, client.get_sddc, existing.id, target_states=DEAD_STATES,
    )


def needs_update(params, existing):
    updatable = ["display_name", "vmware_software_version", "ssh_authorized_keys"]
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
        required_if=[
            ("state", "present", ("compartment_id",), True),
            ("state", "absent", ("sddc_id",)),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, SddcClient)
    params = module.params
    state = params["state"]

    existing = None
    if params.get("sddc_id"):
        existing = get_resource(client, params["sddc_id"])
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
        module.exit_json(changed=True, sddc=to_dict(resource))
        return

    if needs_update(params, existing):
        if module.check_mode:
            module.exit_json(changed=True)
        resource = update_resource(module, client, existing)
        module.exit_json(changed=True, sddc=to_dict(resource))
        return

    module.exit_json(changed=False, sddc=to_dict(existing))


if __name__ == "__main__":
    main()
