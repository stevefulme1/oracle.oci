# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI VMware Solution ESXi Hosts."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_ocvp_esxi_host
short_description: Manage VMware Solution ESXi Hosts in OCI
description:
    - Create, update, and delete ESXi hosts in an Oracle Cloud VMware Solution SDDC.
    - This module uses the OCI Python SDK C(oci.ocvp.EsxiHostClient).
version_added: "2.0.0"
author:
    - Oracle (@oracle)
options:
    cluster_id:
        description:
            - The OCID of the cluster to add the ESXi host to.
            - Required when creating a new ESXi host.
        type: str
    sddc_id:
        description:
            - The OCID of the SDDC for the ESXi host.
        type: str
    esxi_host_id:
        description:
            - The OCID of an existing ESXi host.
            - Required for update and delete operations.
        type: str
    display_name:
        description:
            - The display name of the ESXi host.
        type: str
    compute_availability_domain:
        description:
            - The availability domain for the ESXi host.
        type: str
    host_shape_name:
        description:
            - The compute shape name for the ESXi host.
        type: str
    host_ocpu_count:
        description:
            - The OCPU count for the ESXi host.
        type: float
    state:
        description:
            - The desired state of the ESXi host.
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
- name: Add an ESXi host to a cluster
  stevefulme1.oci_cloud.oci_ocvp_esxi_host:
    cluster_id: "ocid1.cluster.oc1..example"
    display_name: "esxi-host-04"
    state: present

- name: Remove an ESXi host
  stevefulme1.oci_cloud.oci_ocvp_esxi_host:
    esxi_host_id: "ocid1.esxihost.oc1..example"
    state: absent
"""

RETURN = r"""
esxi_host:
    description: Details of the ESXi host.
    returned: On success when state is present.
    type: dict
    sample:
        id: "ocid1.esxihost.oc1..example"
        display_name: "esxi-host-04"
        lifecycle_state: "ACTIVE"
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from oci.ocvp import EsxiHostClient
    from oci.ocvp.models import (
        CreateEsxiHostDetails,
        UpdateEsxiHostDetails,
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
        cluster_id=dict(type="str"),
        sddc_id=dict(type="str"),
        esxi_host_id=dict(type="str"),
        display_name=dict(type="str"),
        compute_availability_domain=dict(type="str"),
        host_shape_name=dict(type="str"),
        host_ocpu_count=dict(type="float"),
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
        response = call_with_retry(client.get_esxi_host, resource_id)
        return response.data
    except ServiceError as e:
        if e.status == 404:
            return None
        raise


def create_resource(module, client):
    params = module.params
    create_details = CreateEsxiHostDetails(
        cluster_id=params.get("cluster_id"),
        sddc_id=params.get("sddc_id"),
        display_name=params.get("display_name"),
        compute_availability_domain=params.get("compute_availability_domain"),
        host_shape_name=params.get("host_shape_name"),
        host_ocpu_count=params.get("host_ocpu_count"),
        freeform_tags=params.get("freeform_tags"),
        defined_tags=params.get("defined_tags"),
    )
    response = call_with_retry(client.create_esxi_host, create_details)
    resource = response.data
    resource = wait_for_resource(
        module, client.get_esxi_host, resource.id, target_states=READY_STATES,
    )
    return resource


def update_resource(module, client, existing):
    params = module.params
    update_details = UpdateEsxiHostDetails(
        display_name=params.get("display_name"),
        freeform_tags=params.get("freeform_tags"),
        defined_tags=params.get("defined_tags"),
    )
    response = call_with_retry(client.update_esxi_host, existing.id, update_details)
    resource = response.data
    return resource


def delete_resource(module, client, existing):
    call_with_retry(client.delete_esxi_host, existing.id)
    wait_for_resource(
        module, client.get_esxi_host, existing.id, target_states=DEAD_STATES,
    )


def needs_update(params, existing):
    if params.get("display_name") is not None:
        if getattr(existing, "display_name", None) != params["display_name"]:
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
            ("state", "absent", ("esxi_host_id",)),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, EsxiHostClient)
    params = module.params
    state = params["state"]

    existing = None
    if params.get("esxi_host_id"):
        existing = get_resource(client, params["esxi_host_id"])

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
        module.exit_json(changed=True, esxi_host=to_dict(resource))
        return

    if needs_update(params, existing):
        if module.check_mode:
            module.exit_json(changed=True)
        resource = update_resource(module, client, existing)
        module.exit_json(changed=True, esxi_host=to_dict(resource))
        return

    module.exit_json(changed=False, esxi_host=to_dict(existing))


if __name__ == "__main__":
    main()
