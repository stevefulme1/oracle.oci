# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for OCI AI Speech transcription."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_ai_speech_transcribe
short_description: Transcribe audio using OCI AI Speech
description:
    - Submit an audio transcription job to OCI AI Speech and optionally wait for completion.
    - This is an B(action) module that submits asynchronous transcription jobs.
      It does not manage infrastructure resources.
    - Uses the OCI Python SDK C(oci.ai_speech.AIServiceSpeechClient).
    - Audio files must be in Object Storage. The module submits a transcription job,
      then polls for completion when I(wait=true).
version_added: "1.0.0"
author:
    - Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment.
        type: str
        required: true
    display_name:
        description:
            - A display name for the transcription job.
        type: str
        required: true
    input_location:
        description:
            - The Object Storage location of the audio file to transcribe.
        type: dict
        required: true
        suboptions:
            namespace:
                description: Object Storage namespace.
                type: str
                required: true
            bucket:
                description: Object Storage bucket name.
                type: str
                required: true
            object:
                description: Object Storage object name.
                type: str
                required: true
    output_location:
        description:
            - The Object Storage location where transcription results will be written.
        type: dict
        required: true
        suboptions:
            namespace:
                description: Object Storage namespace.
                type: str
                required: true
            bucket:
                description: Object Storage bucket name.
                type: str
                required: true
            prefix:
                description: Object Storage prefix for output files.
                type: str
                required: true
    language_code:
        description:
            - The language of the audio file using BCP-47 language tags.
        type: str
        default: "en-US"
extends_documentation_fragment:
    - oracle.oci.oci_common
requirements:
    - "python >= 3.8"
    - "oci >= 2.90.0"
"""

EXAMPLES = r"""
- name: Submit a transcription job and wait for completion
  oracle.oci.oci_ai_speech_transcribe:
    compartment_id: "ocid1.compartment.oc1..example"
    display_name: "meeting-recording-transcription"
    input_location:
      namespace: "mytenancy"
      bucket: "audio-files"
      object: "meeting-2024-01-15.wav"
    output_location:
      namespace: "mytenancy"
      bucket: "transcriptions"
      prefix: "meeting-2024-01-15"
    language_code: "en-US"
    wait: true
    wait_timeout: 3600
  register: transcription_result

- name: Submit a transcription job without waiting
  oracle.oci.oci_ai_speech_transcribe:
    compartment_id: "ocid1.compartment.oc1..example"
    display_name: "podcast-transcription"
    input_location:
      namespace: "mytenancy"
      bucket: "audio-files"
      object: "podcast-ep42.mp3"
    output_location:
      namespace: "mytenancy"
      bucket: "transcriptions"
      prefix: "podcast-ep42"
    wait: false

- name: Check mode - preview request
  oracle.oci.oci_ai_speech_transcribe:
    compartment_id: "ocid1.compartment.oc1..example"
    display_name: "test-transcription"
    input_location:
      namespace: "mytenancy"
      bucket: "audio-files"
      object: "test.wav"
    output_location:
      namespace: "mytenancy"
      bucket: "transcriptions"
      prefix: "test"
  check_mode: true
"""

RETURN = r"""
result:
    description: Structured transcription job results.
    returned: success
    type: dict
    contains:
        transcription_job:
            description: Details of the transcription job including ID, status, and timestamps.
            type: dict
        transcript_text:
            description:
                - The transcribed text, if the job completed and results are accessible.
                - Empty string if the job is still running or results are in Object Storage.
            type: str
raw_response:
    description: The full API response as a dictionary.
    returned: success
    type: dict
request_payload:
    description: The request payload that was (or would be) sent. Returned in check mode.
    returned: check_mode
    type: dict
"""

import time

from ansible.module_utils.basic import AnsibleModule

try:
    from oci.ai_speech import AIServiceSpeechClient
    from oci.ai_speech.models import (
        CreateTranscriptionJobDetails,
        ObjectLocation,
        OutputLocation,
        TranscriptionModelDetails,
        ObjectListInlineInputLocation,
    )
    from oci.exceptions import ServiceError

    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False

from ansible_collections.oracle.oci.plugins.module_utils.oci_common import (
    OCI_COMMON_ARGS,
)
from ansible_collections.oracle.oci.plugins.module_utils.oci_auth import create_service_client
from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import call_with_retry


def get_module_args():
    module_args = dict(
        compartment_id=dict(type="str", required=True),
        display_name=dict(type="str", required=True),
        input_location=dict(
            type="dict", required=True,
            options=dict(
                namespace=dict(type="str", required=True),
                bucket=dict(type="str", required=True),
                object=dict(type="str", required=True),
            ),
        ),
        output_location=dict(
            type="dict", required=True,
            options=dict(
                namespace=dict(type="str", required=True),
                bucket=dict(type="str", required=True),
                prefix=dict(type="str", required=True),
            ),
        ),
        language_code=dict(type="str", default="en-US"),
    )
    module_args.update(OCI_COMMON_ARGS)
    return module_args


def to_dict(resource):
    """Recursively convert an OCI model object to a plain dict."""
    if resource is None:
        return {}
    if isinstance(resource, dict):
        return {k: to_dict(v) for k, v in resource.items()}
    if isinstance(resource, list):
        return [to_dict(i) for i in resource]
    if hasattr(resource, "__dict__"):
        result = {}
        for key, value in resource.__dict__.items():
            if key.startswith("_"):
                continue
            result[key] = to_dict(value)
        return result
    return resource


def _wait_for_transcription_job(module, client, job_id):
    """Poll a transcription job until it completes or fails."""
    timeout = module.params.get("wait_timeout", 1200)
    interval = module.params.get("wait_interval", 30)

    start = time.monotonic()
    while True:
        response = call_with_retry(client.get_transcription_job, job_id)
        job = response.data
        state = getattr(job, "lifecycle_state", None)

        if state in ("SUCCEEDED", "COMPLETED"):
            return job
        if state in ("FAILED", "CANCELED"):
            module.fail_json(
                msg=f"Transcription job {job_id} {state}",
                transcription_job=to_dict(job),
            )

        elapsed = time.monotonic() - start
        if elapsed >= timeout:
            module.fail_json(
                msg=f"Timed out waiting for transcription job {job_id}. "
                f"Current state: {state}",
                transcription_job=to_dict(job),
            )
        time.sleep(min(interval, timeout - elapsed))


def main():
    module = AnsibleModule(
        argument_spec=get_module_args(),
        supports_check_mode=True,
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    params = module.params
    input_loc = params["input_location"]
    output_loc = params["output_location"]

    payload_info = {
        "compartment_id": params["compartment_id"],
        "display_name": params["display_name"],
        "input_location": input_loc,
        "output_location": output_loc,
        "language_code": params["language_code"],
    }

    if module.check_mode:
        module.exit_json(
            changed=False,
            request_payload=payload_info,
            result={
                "transcription_job": {},
                "transcript_text": "",
            },
            raw_response={},
        )

    client = create_service_client(module, AIServiceSpeechClient)

    try:
        object_location = ObjectLocation(
            namespace_name=input_loc["namespace"],
            bucket_name=input_loc["bucket"],
            object_names=[input_loc["object"]],
        )
        input_location = ObjectListInlineInputLocation(
            object_locations=[object_location],
        )
        output_location = OutputLocation(
            namespace_name=output_loc["namespace"],
            bucket_name=output_loc["bucket"],
            prefix=output_loc["prefix"],
        )
        model_details = TranscriptionModelDetails(
            language_code=params["language_code"],
            model_type="WHISPER_MEDIUM",
        )

        create_details = CreateTranscriptionJobDetails(
            compartment_id=params["compartment_id"],
            display_name=params["display_name"],
            input_location=input_location,
            output_location=output_location,
            model_details=model_details,
            freeform_tags=params.get("freeform_tags"),
            defined_tags=params.get("defined_tags"),
        )

        response = call_with_retry(client.create_transcription_job, create_details)
        job = response.data
        job_id = job.id

        # If wait is enabled, poll for completion
        wait = params.get("wait", True)
        if wait:
            job = _wait_for_transcription_job(module, client, job_id)

        job_dict = to_dict(job)
        job_state = getattr(job, "lifecycle_state", "UNKNOWN")

        result = {
            "transcription_job": {
                "id": getattr(job, "id", ""),
                "display_name": getattr(job, "display_name", ""),
                "lifecycle_state": job_state,
                "time_started": str(getattr(job, "time_started", "")),
                "time_finished": str(getattr(job, "time_finished", "")),
                "output_location": to_dict(getattr(job, "output_location", None)),
            },
            "transcript_text": "",
        }

        module.exit_json(
            changed=True,
            result=result,
            raw_response=job_dict,
        )
    except ServiceError as e:
        module.fail_json(
            msg=f"OCI AI Speech transcription failed: {e.message}",
            status=e.status,
            code=e.code,
            request_payload=payload_info,
        )


if __name__ == "__main__":
    main()
