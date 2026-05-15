# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI AI Speech Transcription Jobs."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_ai_speech_transcription
short_description: Manage AI Speech Transcription Jobs in OCI
description:
    - Create and delete AI Speech Transcription Jobs in Oracle Cloud Infrastructure.
    - This module uses the OCI Python SDK C(oci.ai_speech.AIServiceSpeechClient).
    - This is a create/delete only resource; update is not supported.
version_added: "1.0.0"
author:
    - Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment to contain the transcription job.
            - Required when creating a new job.
        type: str
    transcription_job_id:
        description:
            - The OCID of an existing transcription job.
            - Required for delete operations.
        type: str
    display_name:
        description:
            - The display name of the transcription job.
        type: str
    input_location:
        description:
            - The input location details for the transcription job.
        type: dict
    output_location:
        description:
            - The output location details for the transcription job.
        type: dict
    model_details:
        description:
            - Model details for the transcription job.
        type: dict
    state:
        description:
            - The desired state of the transcription job.
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
- name: Create a transcription job
  stevefulme1.oci_cloud.oci_ai_speech_transcription:
    compartment_id: "ocid1.compartment.oc1..example"
    display_name: "my-transcription-job"
    input_location:
      location_type: "OBJECT_LIST_INLINE_INPUT_LOCATION"
      object_locations:
        - namespace_name: "my-namespace"
          bucket_name: "my-bucket"
          object_names: ["audio.wav"]
    output_location:
      namespace_name: "my-namespace"
      bucket_name: "my-output-bucket"
      prefix: "transcription-output"
    state: present

- name: Delete a transcription job
  stevefulme1.oci_cloud.oci_ai_speech_transcription:
    transcription_job_id: "ocid1.aispechtranscriptionjob.oc1..example"
    state: absent
"""

RETURN = r"""
transcription_job:
    description: Details of the transcription job.
    returned: On success when state is present.
    type: dict
    sample:
        id: "ocid1.aispechtranscriptionjob.oc1..example"
        display_name: "my-transcription-job"
        lifecycle_state: "SUCCEEDED"
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from oci.ai_speech import AIServiceSpeechClient
    from oci.ai_speech.models import CreateTranscriptionJobDetails
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
        transcription_job_id=dict(type="str"),
        display_name=dict(type="str"),
        input_location=dict(type="dict"),
        output_location=dict(type="dict"),
        model_details=dict(type="dict"),
        state=dict(type="str", choices=["present", "absent"], default="present"),
    )
    module_args.update(OCI_COMMON_ARGS)
    return module_args


def get_resource(client, resource_id):
    try:
        response = call_with_retry(client.get_transcription_job, resource_id)
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
            client.list_transcription_jobs, compartment_id=compartment_id,
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
    create_details = CreateTranscriptionJobDetails(
        compartment_id=params["compartment_id"],
        display_name=params.get("display_name"),
        input_location=params.get("input_location"),
        output_location=params.get("output_location"),
        model_details=params.get("model_details"),
        freeform_tags=params.get("freeform_tags"),
        defined_tags=params.get("defined_tags"),
    )
    response = call_with_retry(client.create_transcription_job, create_details)
    resource = response.data
    resource = wait_for_resource(
        module, client.get_transcription_job, resource.id, target_states=READY_STATES,
    )
    return resource


def delete_resource(module, client, existing):
    call_with_retry(client.delete_transcription_job, existing.id)
    wait_for_resource(
        module, client.get_transcription_job, existing.id, target_states=DEAD_STATES,
    )


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

    client = create_service_client(module, AIServiceSpeechClient)
    params = module.params
    state = params["state"]

    existing = None
    if params.get("transcription_job_id"):
        existing = get_resource(client, params["transcription_job_id"])
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
                module.fail_json(msg=f"Parameter '{req}' is required to create a transcription job.")
        if module.check_mode:
            module.exit_json(changed=True)
        resource = create_resource(module, client)
        module.exit_json(changed=True, transcription_job=to_dict(resource))
        return

    # No update supported for transcription jobs
    module.exit_json(changed=False, transcription_job=to_dict(existing))


if __name__ == "__main__":
    main()
