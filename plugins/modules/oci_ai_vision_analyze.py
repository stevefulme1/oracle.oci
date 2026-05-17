# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for OCI AI Vision image analysis."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_ai_vision_analyze
short_description: Analyze images using OCI AI Vision
description:
    - Perform image analysis including classification, object detection, and text detection
      using the OCI AI Vision service.
    - This is an B(action) module that calls AI inference APIs and returns results.
      It does not manage infrastructure resources.
    - Uses the OCI Python SDK C(oci.ai_vision.AIServiceVisionClient).
version_added: "1.0.0"
author:
    - Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment.
        type: str
        required: true
    image_source:
        description:
            - The source type for the image.
        type: str
        required: true
        choices:
            - url
            - base64
            - object_storage
    image_url:
        description:
            - The URL of the image to analyze.
            - Required when I(image_source=url).
        type: str
    image_data:
        description:
            - The base64-encoded image data.
            - Required when I(image_source=base64).
            - This is image content, not a secret, so it is not masked in logs.
        type: str
    namespace_name:
        description:
            - The Object Storage namespace.
            - Required when I(image_source=object_storage).
        type: str
    bucket_name:
        description:
            - The Object Storage bucket name.
            - Required when I(image_source=object_storage).
        type: str
    object_name:
        description:
            - The Object Storage object name.
            - Required when I(image_source=object_storage).
        type: str
    analysis_type:
        description:
            - The type of image analysis to perform.
        type: str
        required: true
        choices:
            - image_classification
            - object_detection
            - text_detection
extends_documentation_fragment:
    - oracle.oci.oci_common
requirements:
    - "python >= 3.8"
    - "oci >= 2.90.0"
"""

EXAMPLES = r"""
- name: Classify an image from a URL
  oracle.oci.oci_ai_vision_analyze:
    compartment_id: "ocid1.compartment.oc1..example"
    image_source: url
    image_url: "https://example.com/photo.jpg"
    analysis_type: image_classification
  register: classification_result

- name: Detect objects in an image from Object Storage
  oracle.oci.oci_ai_vision_analyze:
    compartment_id: "ocid1.compartment.oc1..example"
    image_source: object_storage
    namespace_name: "mytenancy"
    bucket_name: "images"
    object_name: "photo.jpg"
    analysis_type: object_detection

- name: Detect text in a base64-encoded image
  oracle.oci.oci_ai_vision_analyze:
    compartment_id: "ocid1.compartment.oc1..example"
    image_source: base64
    image_data: "/9j/4AAQSkZJRg..."
    analysis_type: text_detection

- name: Check mode - preview request
  oracle.oci.oci_ai_vision_analyze:
    compartment_id: "ocid1.compartment.oc1..example"
    image_source: url
    image_url: "https://example.com/photo.jpg"
    analysis_type: image_classification
  check_mode: true
"""

RETURN = r"""
result:
    description: Structured analysis results.
    returned: success
    type: dict
    contains:
        labels:
            description: Image classification labels with confidence scores.
            type: list
        objects:
            description: Detected objects with bounding boxes and confidence scores.
            type: list
        text_lines:
            description: Detected text lines from the image.
            type: list
raw_response:
    description: The full API response as a dictionary.
    returned: success
    type: dict
request_payload:
    description: The request payload that was (or would be) sent. Returned in check mode.
    returned: check_mode
    type: dict
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from oci.ai_vision import AIServiceVisionClient
    from oci.ai_vision.models import (
        AnalyzeImageDetails,
        ImageClassificationFeature,
        ObjectDetectionFeature,
        TextDetectionFeature,
        InlineImageDetails,
        ObjectStorageImageDetails,
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
        image_source=dict(type="str", required=True, choices=["url", "base64", "object_storage"]),
        image_url=dict(type="str"),
        image_data=dict(type="str"),
        namespace_name=dict(type="str"),
        bucket_name=dict(type="str"),
        object_name=dict(type="str"),
        analysis_type=dict(
            type="str", required=True,
            choices=["image_classification", "object_detection", "text_detection"],
        ),
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


def _build_image_details(params):
    """Build the image details based on source type."""
    image_source = params["image_source"]

    if image_source == "base64":
        return InlineImageDetails(data=params["image_data"])
    elif image_source == "object_storage":
        return ObjectStorageImageDetails(
            namespace_name=params["namespace_name"],
            bucket_name=params["bucket_name"],
            object_name=params["object_name"],
        )
    else:
        # URL source - use inline with source url
        return InlineImageDetails(source="URL", source_image_url=params["image_url"])


def _build_features(analysis_type):
    """Build the analysis feature list."""
    feature_map = {
        "image_classification": ImageClassificationFeature(),
        "object_detection": ObjectDetectionFeature(),
        "text_detection": TextDetectionFeature(),
    }
    return [feature_map[analysis_type]]


def _extract_classification_results(response_data):
    """Extract image classification results."""
    labels = []
    for result in getattr(response_data, "image_classification_model_version", None) or []:
        pass  # version info, skip

    image_objects = getattr(response_data, "labels", [])
    for label_obj in image_objects:
        labels.append({
            "name": getattr(label_obj, "name", ""),
            "confidence": getattr(label_obj, "confidence", 0.0),
        })

    # Also check image_classification_result
    for result_item in getattr(response_data, "image_classification_result", None) or []:
        for label_obj in getattr(result_item, "labels", []):
            labels.append({
                "name": getattr(label_obj, "name", ""),
                "confidence": getattr(label_obj, "confidence", 0.0),
            })

    return {"labels": labels, "objects": [], "text_lines": []}


def _extract_detection_results(response_data):
    """Extract object detection results."""
    objects = []
    for result_item in getattr(response_data, "image_objects", []):
        bounding_box = getattr(result_item, "bounding_polygon", None)
        bbox_dict = to_dict(bounding_box) if bounding_box else {}
        objects.append({
            "name": getattr(result_item, "name", ""),
            "confidence": getattr(result_item, "confidence", 0.0),
            "bounding_box": bbox_dict,
        })

    # Also check object_detection_result
    for result_item in getattr(response_data, "object_detection_result", None) or []:
        for obj in getattr(result_item, "objects", []):
            bounding_box = getattr(obj, "bounding_polygon", None)
            bbox_dict = to_dict(bounding_box) if bounding_box else {}
            objects.append({
                "name": getattr(obj, "name", ""),
                "confidence": getattr(obj, "confidence", 0.0),
                "bounding_box": bbox_dict,
            })

    return {"labels": [], "objects": objects, "text_lines": []}


def _extract_text_results(response_data):
    """Extract text detection results."""
    text_lines = []
    for line in getattr(response_data, "image_text", None) or []:
        words = getattr(line, "words", [])
        for word in words:
            text_lines.append({
                "text": getattr(word, "text", ""),
                "confidence": getattr(word, "confidence", 0.0),
                "bounding_polygon": to_dict(getattr(word, "bounding_polygon", None)),
            })

    # Also check text_detection_result
    for result_item in getattr(response_data, "text_detection_result", None) or []:
        for line in getattr(result_item, "lines", []):
            text_lines.append({
                "text": getattr(line, "text", ""),
                "confidence": getattr(line, "confidence", 0.0),
                "bounding_polygon": to_dict(getattr(line, "bounding_polygon", None)),
            })

    # Fallback: check for lines directly
    for line in getattr(response_data, "lines", []):
        text_lines.append({
            "text": getattr(line, "text", ""),
            "confidence": getattr(line, "confidence", 0.0),
            "bounding_polygon": to_dict(getattr(line, "bounding_polygon", None)),
        })

    return {"labels": [], "objects": [], "text_lines": text_lines}


def main():
    module = AnsibleModule(
        argument_spec=get_module_args(),
        supports_check_mode=True,
        required_if=[
            ("image_source", "url", ("image_url",)),
            ("image_source", "base64", ("image_data",)),
            ("image_source", "object_storage", ("namespace_name", "bucket_name", "object_name")),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    params = module.params
    analysis_type = params["analysis_type"]

    # Build payload description for check mode
    payload_info = {
        "compartment_id": params["compartment_id"],
        "image_source": params["image_source"],
        "analysis_type": analysis_type,
    }
    if params["image_source"] == "url":
        payload_info["image_url"] = params["image_url"]
    elif params["image_source"] == "object_storage":
        payload_info["namespace_name"] = params["namespace_name"]
        payload_info["bucket_name"] = params["bucket_name"]
        payload_info["object_name"] = params["object_name"]
    elif params["image_source"] == "base64":
        payload_info["image_data_length"] = len(params.get("image_data") or "")

    if module.check_mode:
        module.exit_json(
            changed=False,
            request_payload=payload_info,
            result={"labels": [], "objects": [], "text_lines": []},
            raw_response={},
        )

    client = create_service_client(module, AIServiceVisionClient)

    try:
        image_details = _build_image_details(params)
        features = _build_features(analysis_type)

        analyze_details = AnalyzeImageDetails(
            compartment_id=params["compartment_id"],
            image=image_details,
            features=features,
        )

        response = call_with_retry(client.analyze_image, analyze_details)
        response_data = response.data

        extractors = {
            "image_classification": _extract_classification_results,
            "object_detection": _extract_detection_results,
            "text_detection": _extract_text_results,
        }
        result = extractors[analysis_type](response_data)

        module.exit_json(
            changed=False,
            result=result,
            raw_response=to_dict(response_data),
        )
    except ServiceError as e:
        module.fail_json(
            msg=f"OCI AI Vision analysis failed: {e.message}",
            status=e.status,
            code=e.code,
            request_payload=payload_info,
        )


if __name__ == "__main__":
    main()
