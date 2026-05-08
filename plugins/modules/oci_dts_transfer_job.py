# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Data Transfer Service Transfer Jobs."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_dts_transfer_job
short_description: Manage Data Transfer Service Transfer Jobs in OCI
description:
    - Create, update, and delete Data Transfer Service Transfer Jobs in Oracle Cloud Infrastructure.
    - This module uses the OCI Python SDK C(oci.dts.TransferJobClient).
version_added: "2.1.0"
author:
    - Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment to contain the transfer job.
            - Required when creating a new transfer job.
        type: str
    transfer_job_id:
        description:
            - The OCID of an existing transfer job.
            - Required for update and delete operations.
        type: str
        aliases:
            - id
    display_name:
        description:
            - The display name of the transfer job.
        type: str
    device_type:
        description:
            - The type of device used for the transfer.
        type: str
        choices:
            - DISK
            - APPLIANCE
    upload_bucket_name:
        description:
            - The name of the bucket to upload data to.
        type: str
    label:
        description:
            - A label for the transfer job.
        type: str
    state:
        description:
            - The desired state of the transfer job.
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
- name: Create a transfer job
  stevefulme1.oci_cloud.oci_dts_transfer_job:
    compartment_id: "ocid1.compartment.oc1..example"
    display_name: "my-transfer-job"
    device_type: "DISK"
    upload_bucket_name: "my-bucket"
    state: present

- name: Delete a transfer job
  stevefulme1.oci_cloud.oci_dts_transfer_job:
    transfer_job_id: "ocid1.transferjob.oc1..example"
    state: absent
"""

RETURN = r"""
transfer_job:
    description: Details of the transfer job.
    returned: On success when state is present.
    type: dict
    sample:
        id: "ocid1.transferjob.oc1..example"
        display_name: "my-transfer-job"
        lifecycle_state: "ACTIVE"
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from oci.dts import TransferJobClient
    from oci.dts.models import (
        CreateTransferJobDetails,
        UpdateTransferJobDetails,
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
        transfer_job_id=dict(type="str", aliases=["id"]),
        display_name=dict(type="str"),
        device_type=dict(type="str", choices=["DISK", "APPLIANCE"]),
        upload_bucket_name=dict(type="str"),
        label=dict(type="str"),
        state=dict(type="str", choices=["present", "absent"], default="present"),
    )
    module_args.update(OCI_COMMON_ARGS)
    return module_args


def get_resource(client, resource_id):
    try:
        response = call_with_retry(client.get_transfer_job, resource_id)
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
            client.list_transfer_jobs, compartment_id=compartment_id,
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
    create_details = CreateTransferJobDetails(
        compartment_id=params["compartment_id"],
        display_name=params.get("display_name"),
        device_type=params.get("device_type"),
        upload_bucket_name=params.get("upload_bucket_name"),
        freeform_tags=params.get("freeform_tags"),
        defined_tags=params.get("defined_tags"),
    )
    response = call_with_retry(client.create_transfer_job, create_details)
    resource = response.data
    resource = wait_for_resource(
        module, client.get_transfer_job, resource.id, target_states=READY_STATES,
    )
    return resource


def update_resource(module, client, existing):
    params = module.params
    update_details = UpdateTransferJobDetails(
        display_name=params.get("display_name"),
        device_type=params.get("device_type"),
        freeform_tags=params.get("freeform_tags"),
        defined_tags=params.get("defined_tags"),
    )
    response = call_with_retry(client.update_transfer_job, existing.id, update_details)
    resource = response.data
    resource = wait_for_resource(
        module, client.get_transfer_job, resource.id, target_states=READY_STATES,
    )
    return resource


def delete_resource(module, client, existing):
    call_with_retry(client.delete_transfer_job, existing.id)
    wait_for_resource(
        module, client.get_transfer_job, existing.id, target_states=DEAD_STATES,
    )


def needs_update(params, existing):
    updatable = ["display_name", "device_type"]
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
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, TransferJobClient)
    params = module.params
    state = params["state"]

    existing = None
    if params.get("transfer_job_id"):
        existing = get_resource(client, params["transfer_job_id"])
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
        for req in ("compartment_id",):
            if not params.get(req):
                module.fail_json(msg=f"Parameter '{req}' is required to create a transfer job.")
        if module.check_mode:
            module.exit_json(changed=True)
        resource = create_resource(module, client)
        module.exit_json(changed=True, transfer_job=to_dict(resource))
        return

    if needs_update(params, existing):
        if module.check_mode:
            module.exit_json(changed=True)
        resource = update_resource(module, client, existing)
        module.exit_json(changed=True, transfer_job=to_dict(resource))
        return

    module.exit_json(changed=False, transfer_job=to_dict(existing))


if __name__ == "__main__":
    main()
