# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Data Science Pipeline Runs."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_data_science_pipeline_run
short_description: Manage Data Science Pipeline Runs in OCI
description:
    - Create and delete Data Science Pipeline Runs in Oracle Cloud Infrastructure.
    - This module uses the OCI Python SDK C(oci.data_science.DataScienceClient).
    - This is a create/delete only resource; update is not supported.
version_added: "2.0.0"
author:
    - Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment to contain the pipeline run.
            - Required when creating a new pipeline run.
        type: str
    pipeline_run_id:
        description:
            - The OCID of an existing pipeline run.
            - Required for delete operations.
        type: str
    pipeline_id:
        description:
            - The OCID of the pipeline to run.
            - Required when creating a new pipeline run.
        type: str
    project_id:
        description:
            - The OCID of the Data Science project.
            - Required when creating a new pipeline run.
        type: str
    display_name:
        description:
            - The display name of the pipeline run.
        type: str
    configuration_override_details:
        description:
            - Configuration override details for this specific run.
        type: dict
    log_configuration_override_details:
        description:
            - Logging configuration override details for this specific run.
        type: dict
    step_override_details:
        description:
            - Step-level override details for this specific run.
        type: list
        elements: dict
    state:
        description:
            - The desired state of the pipeline run.
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
- name: Create a Data Science pipeline run
  stevefulme1.oci_cloud.oci_data_science_pipeline_run:
    compartment_id: "ocid1.compartment.oc1..example"
    project_id: "ocid1.datascienceproject.oc1..example"
    pipeline_id: "ocid1.datasciencepipeline.oc1..example"
    display_name: "pipeline-run-001"
    state: present

- name: Delete a Data Science pipeline run
  stevefulme1.oci_cloud.oci_data_science_pipeline_run:
    pipeline_run_id: "ocid1.datasciencepipelinerun.oc1..example"
    state: absent
"""

RETURN = r"""
data_science_pipeline_run:
    description: Details of the Data Science pipeline run.
    returned: On success when state is present.
    type: dict
    sample:
        id: "ocid1.datasciencepipelinerun.oc1..example"
        display_name: "pipeline-run-001"
        lifecycle_state: "SUCCEEDED"
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from oci.data_science import DataScienceClient
    from oci.data_science.models import CreatePipelineRunDetails
    from oci.exceptions import ServiceError

    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False

from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_common import (
    OCI_COMMON_ARGS,
    DEAD_STATES,
)
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_auth import create_service_client
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_wait import (
    call_with_retry,
    wait_for_resource,
)

SUCCEEDED_STATES = frozenset({"SUCCEEDED", "COMPLETED"})


def get_module_args():
    module_args = dict(
        compartment_id=dict(type="str"),
        pipeline_run_id=dict(type="str"),
        pipeline_id=dict(type="str"),
        project_id=dict(type="str"),
        display_name=dict(type="str"),
        configuration_override_details=dict(type="dict"),
        log_configuration_override_details=dict(type="dict"),
        step_override_details=dict(type="list", elements="dict"),
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
        response = call_with_retry(client.get_pipeline_run, resource_id)
        return response.data
    except ServiceError as e:
        if e.status == 404:
            return None
        raise


def create_resource(module, client):
    params = module.params
    create_details = CreatePipelineRunDetails(
        compartment_id=params["compartment_id"],
        project_id=params["project_id"],
        pipeline_id=params["pipeline_id"],
        display_name=params.get("display_name"),
        configuration_override_details=params.get("configuration_override_details"),
        log_configuration_override_details=params.get("log_configuration_override_details"),
        step_override_details=params.get("step_override_details"),
        freeform_tags=params.get("freeform_tags"),
        defined_tags=params.get("defined_tags"),
    )
    response = call_with_retry(client.create_pipeline_run, create_details)
    resource = response.data
    resource = wait_for_resource(
        module, client.get_pipeline_run, resource.id, target_states=SUCCEEDED_STATES,
    )
    return resource


def delete_resource(module, client, existing):
    call_with_retry(client.delete_pipeline_run, existing.id)
    wait_for_resource(
        module, client.get_pipeline_run, existing.id, target_states=DEAD_STATES,
    )


def main():
    module = AnsibleModule(
        argument_spec=get_module_args(),
        supports_check_mode=True,
        required_if=[
            ("state", "present", ("compartment_id", "project_id", "pipeline_id"), True),
            ("state", "absent", ("pipeline_run_id",)),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, DataScienceClient)
    params = module.params
    state = params["state"]

    existing = None
    if params.get("pipeline_run_id"):
        existing = get_resource(client, params["pipeline_run_id"])

    if state == "absent":
        if existing is None:
            module.exit_json(changed=False)
        if module.check_mode:
            module.exit_json(changed=True)
        delete_resource(module, client, existing)
        module.exit_json(changed=True)
        return

    if existing is not None:
        module.exit_json(changed=False, data_science_pipeline_run=to_dict(existing))
        return

    if module.check_mode:
        module.exit_json(changed=True)
    resource = create_resource(module, client)
    module.exit_json(changed=True, data_science_pipeline_run=to_dict(resource))


if __name__ == "__main__":
    main()
