# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for OCI AI Anomaly Detection inference."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_ai_anomaly_detect
short_description: Detect anomalies using OCI AI Anomaly Detection
description:
    - Submit time-series or tabular data to an OCI AI Anomaly Detection model
      and return detected anomalies.
    - This is an B(action) module that calls AI inference APIs and returns results.
      It does not manage infrastructure resources.
    - Uses the OCI Python SDK C(oci.ai_anomaly_detection.AnomalyDetectionClient).
version_added: "1.0.0"
author:
    - Oracle (@oracle)
options:
    model_id:
        description:
            - The OCID of the trained anomaly detection model to use.
        type: str
        required: true
    data:
        description:
            - The data points to analyze for anomalies.
            - Each item is a dictionary with signal values keyed by signal name.
            - Must include a C(timestamp) key if the model expects time-series data.
        type: list
        elements: dict
        required: true
    signal_names:
        description:
            - List of signal (column) names in the data.
            - The order must match the order expected by the model.
        type: list
        elements: str
        required: true
extends_documentation_fragment:
    - oracle.oci.oci_common
requirements:
    - "python >= 3.8"
    - "oci >= 2.90.0"
"""

EXAMPLES = r"""
- name: Detect anomalies in sensor data
  oracle.oci.oci_ai_anomaly_detect:
    model_id: "ocid1.aianomalydetectionmodel.oc1..example"
    signal_names:
      - temperature
      - pressure
      - humidity
    data:
      - timestamp: "2024-01-15T10:00:00Z"
        temperature: 72.5
        pressure: 1013.2
        humidity: 45.0
      - timestamp: "2024-01-15T10:05:00Z"
        temperature: 150.0
        pressure: 800.0
        humidity: 95.0
      - timestamp: "2024-01-15T10:10:00Z"
        temperature: 73.1
        pressure: 1013.5
        humidity: 44.8
  register: anomaly_result

- name: Check mode - preview request
  oracle.oci.oci_ai_anomaly_detect:
    model_id: "ocid1.aianomalydetectionmodel.oc1..example"
    signal_names:
      - cpu_usage
      - memory_usage
    data:
      - timestamp: "2024-01-15T10:00:00Z"
        cpu_usage: 85.0
        memory_usage: 70.0
  check_mode: true
"""

RETURN = r"""
result:
    description: Structured anomaly detection results.
    returned: success
    type: dict
    contains:
        anomalies:
            description: List of detected anomalies with details.
            type: list
            elements: dict
            contains:
                timestamp:
                    description: When the anomaly was detected.
                    type: str
                signal:
                    description: Which signal showed the anomaly.
                    type: str
                score:
                    description: Anomaly score (higher means more anomalous).
                    type: float
        anomaly_count:
            description: Total number of detected anomalies.
            type: int
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
    from oci.ai_anomaly_detection import AnomalyDetectionClient
    from oci.ai_anomaly_detection.models import (
        InlineDetectAnomaliesRequest,
        DataItem,
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
        model_id=dict(type="str", required=True),
        data=dict(type="list", elements="dict", required=True),
        signal_names=dict(type="list", elements="str", required=True),
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


def _build_data_items(data, signal_names):
    """Convert input data dicts to DataItem list."""
    items = []
    for row in data:
        timestamp = row.get("timestamp")
        values = [float(row.get(name, 0.0)) for name in signal_names]
        item = DataItem(
            timestamp=timestamp,
            values=values,
        )
        items.append(item)
    return items


def _extract_anomalies(response_data, signal_names):
    """Extract structured anomaly information from the response."""
    anomalies = []

    # Handle detection_results
    for result_item in getattr(response_data, "detection_results", []):
        timestamp = str(getattr(result_item, "timestamp", ""))
        row_index = getattr(result_item, "row_index", None)

        # Each result may have anomaly details per signal
        for anomaly in getattr(result_item, "anomalies", []):
            signal_index = getattr(anomaly, "signal_index", None)
            signal_name = ""
            if signal_index is not None and signal_index < len(signal_names):
                signal_name = signal_names[signal_index]

            anomalies.append({
                "timestamp": timestamp,
                "row_index": row_index,
                "signal": signal_name,
                "signal_index": signal_index,
                "actual_value": getattr(anomaly, "actual_value", None),
                "estimated_value": getattr(anomaly, "estimated_value", None),
                "score": getattr(anomaly, "anomaly_score", 0.0),
            })

    return anomalies


def main():
    module = AnsibleModule(
        argument_spec=get_module_args(),
        supports_check_mode=True,
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    params = module.params
    signal_names = params["signal_names"]
    data = params["data"]

    payload_info = {
        "model_id": params["model_id"],
        "signal_names": signal_names,
        "data_point_count": len(data),
        "data": data,
    }

    if module.check_mode:
        module.exit_json(
            changed=False,
            request_payload=payload_info,
            result={"anomalies": [], "anomaly_count": 0},
            raw_response={},
        )

    client = create_service_client(module, AnomalyDetectionClient)

    try:
        data_items = _build_data_items(data, signal_names)

        detect_request = InlineDetectAnomaliesRequest(
            model_id=params["model_id"],
            signal_names=signal_names,
            data=data_items,
        )

        response = call_with_retry(client.detect_anomalies, detect_request)
        response_data = response.data

        anomalies = _extract_anomalies(response_data, signal_names)

        result = {
            "anomalies": anomalies,
            "anomaly_count": len(anomalies),
        }

        module.exit_json(
            changed=False,
            result=result,
            raw_response=to_dict(response_data),
        )
    except ServiceError as e:
        module.fail_json(
            msg=f"OCI AI Anomaly Detection failed: {e.message}",
            status=e.status,
            code=e.code,
            request_payload=payload_info,
        )


if __name__ == "__main__":
    main()
