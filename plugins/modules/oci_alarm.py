#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Monitoring alarms."""

from __future__ import annotations

DOCUMENTATION = r"""
---
module: oci_alarm
short_description: Manage OCI Monitoring alarms
description:
  - Create, update, and delete monitoring alarms in OCI.
  - Alarms evaluate metrics and trigger notifications when thresholds are breached.
version_added: "1.0.0"
author: Oracle (@oracle)
options:
  compartment_id:
    description:
      - The OCID of the compartment where the alarm resides.
      - Required when creating a new alarm.
    type: str
  display_name:
    description:
      - A user-friendly name for the alarm.
      - Required when creating a new alarm.
    type: str
  metric_compartment_id:
    description:
      - The OCID of the compartment containing the metric being evaluated.
      - Required when creating a new alarm.
    type: str
  namespace:
    description:
      - The source service or application emitting the metric (e.g., oci_computeagent).
      - Required when creating a new alarm.
    type: str
  query:
    description:
      - The Monitoring Query Language (MQL) expression to evaluate.
      - "Example: CpuUtilization[1m].mean() > 80"
      - Required when creating a new alarm.
    type: str
  severity:
    description:
      - The perceived type of response required when the alarm fires.
    type: str
    choices: [CRITICAL, ERROR, WARNING, INFO]
    default: CRITICAL
  destinations:
    description:
      - List of notification topic OCIDs to deliver alarm notifications to.
      - Required when creating a new alarm.
    type: list
    elements: str
  is_enabled:
    description:
      - Whether the alarm is enabled.
    type: bool
    default: true
  alarm_id:
    description:
      - The OCID of the alarm.
      - Required for update and delete operations.
    type: str
  state:
    description:
      - The desired state of the alarm.
    type: str
    choices: [present, absent]
    default: present
  freeform_tags:
    description:
      - Free-form tags for this resource.
    type: dict
  defined_tags:
    description:
      - Defined tags for this resource.
    type: dict
extends_documentation_fragment:
  - oracle.oci.oci_common
"""

EXAMPLES = r"""
- name: Create a CPU utilization alarm
  oracle.oci.oci_alarm:
    compartment_id: ocid1.compartment.oc1..example
    display_name: high-cpu-alarm
    metric_compartment_id: ocid1.compartment.oc1..example
    namespace: oci_computeagent
    query: "CpuUtilization[1m].mean() > 80"
    severity: CRITICAL
    destinations:
      - ocid1.onstopic.oc1..example
    is_enabled: true
    state: present

- name: Create a memory warning alarm
  oracle.oci.oci_alarm:
    compartment_id: ocid1.compartment.oc1..example
    display_name: memory-warning
    metric_compartment_id: ocid1.compartment.oc1..example
    namespace: oci_computeagent
    query: "MemoryUtilization[5m].mean() > 90"
    severity: WARNING
    destinations:
      - ocid1.onstopic.oc1..example
    state: present

- name: Disable an alarm
  oracle.oci.oci_alarm:
    alarm_id: ocid1.alarm.oc1..example
    is_enabled: false
    state: present

- name: Delete an alarm
  oracle.oci.oci_alarm:
    alarm_id: ocid1.alarm.oc1..example
    state: absent
"""

RETURN = r"""
resource:
  description: The alarm resource details.
  returned: on success
  type: dict
  contains:
    id:
      description: The OCID of the alarm.
      type: str
    compartment_id:
      description: The OCID of the compartment.
      type: str
    display_name:
      description: The display name of the alarm.
      type: str
    metric_compartment_id:
      description: The OCID of the compartment containing the metric.
      type: str
    namespace:
      description: The source service or application emitting the metric.
      type: str
    query:
      description: The MQL expression to evaluate.
      type: str
    severity:
      description: The alarm severity.
      type: str
    destinations:
      description: List of notification destination OCIDs.
      type: list
    is_enabled:
      description: Whether the alarm is enabled.
      type: bool
    lifecycle_state:
      description: The current lifecycle state of the alarm.
      type: str
    time_created:
      description: The date and time the alarm was created.
      type: str
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.oracle.oci.plugins.module_utils.oci_common import (
    OCI_COMMON_ARGS,
)
from ansible_collections.oracle.oci.plugins.module_utils.oci_auth import (
    create_service_client,
)
from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import (
    call_with_retry,
    wait_for_resource,
)

try:
    import oci
    from oci.monitoring import MonitoringClient
    from oci.monitoring.models import (
        CreateAlarmDetails,
        UpdateAlarmDetails,
    )
    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False


def to_dict(resource):
    """Convert an OCI SDK resource to a serializable dict."""
    if resource is None:
        return {}
    result = {}
    for key, value in resource.__dict__.items():
        if key.startswith("_"):
            continue
        if hasattr(value, "__dict__") and not isinstance(value, (str, int, float, bool, list, dict)):
            result[key] = to_dict(value)
        elif isinstance(value, list):
            result[key] = [to_dict(i) if hasattr(i, "__dict__") else i for i in value]
        else:
            result[key] = value
    return result


def get_alarm(client, alarm_id):
    """Get an alarm by OCID, return None if not found."""
    try:
        response = call_with_retry(client.get_alarm, alarm_id)
        alarm = response.data
        if alarm.lifecycle_state in ("DELETED", "TERMINATED"):
            return None
        return alarm
    except oci.exceptions.ServiceError as e:
        if e.status == 404:
            return None
        raise


def find_alarm(client, compartment_id, display_name):
    """Find an alarm by compartment and display name."""
    if not compartment_id or not display_name:
        return None
    alarms = call_with_retry(
        client.list_alarms,
        compartment_id,
    ).data
    for a in alarms:
        if a.display_name == display_name and a.lifecycle_state not in (
            "DELETED",
            "TERMINATED",
        ):
            return get_alarm(client, a.id)
    return None


def create_alarm(module, client):
    """Create a new monitoring alarm."""
    freeform_tags = module.params.get("freeform_tags") or {}
    defined_tags = module.params.get("defined_tags") or {}

    details = CreateAlarmDetails(
        compartment_id=module.params["compartment_id"],
        display_name=module.params["display_name"],
        metric_compartment_id=module.params["metric_compartment_id"],
        namespace=module.params["namespace"],
        query=module.params["query"],
        severity=module.params.get("severity", "CRITICAL"),
        destinations=module.params["destinations"],
        is_enabled=module.params.get("is_enabled", True),
        freeform_tags=freeform_tags,
        defined_tags=defined_tags,
    )
    response = call_with_retry(client.create_alarm, details)
    alarm = response.data

    if module.params.get("wait", True):
        alarm = wait_for_resource(
            module,
            client.get_alarm,
            alarm.id,
            target_states={"ACTIVE"},
        )
    return alarm


def update_alarm(module, client, alarm):
    """Update an existing alarm."""
    kwargs = {}
    for attr in ("display_name", "metric_compartment_id", "namespace", "query",
                 "severity", "destinations", "is_enabled"):
        value = module.params.get(attr)
        if value is not None:
            kwargs[attr] = value
    if module.params.get("freeform_tags") is not None:
        kwargs["freeform_tags"] = module.params["freeform_tags"]
    if module.params.get("defined_tags") is not None:
        kwargs["defined_tags"] = module.params["defined_tags"]

    if not kwargs:
        return alarm

    details = UpdateAlarmDetails(**kwargs)
    response = call_with_retry(client.update_alarm, alarm.id, details)
    return response.data


def delete_alarm(module, client, alarm):
    """Delete an alarm."""
    call_with_retry(client.delete_alarm, alarm.id)


def needs_update(module, alarm):
    """Check if alarm needs to be updated."""
    check_attrs = [
        "display_name", "metric_compartment_id", "namespace", "query",
        "severity", "destinations", "is_enabled",
    ]
    for attr in check_attrs:
        desired = module.params.get(attr)
        if desired is not None and getattr(alarm, attr, None) != desired:
            return True
    freeform = module.params.get("freeform_tags")
    if freeform is not None and getattr(alarm, "freeform_tags", None) != freeform:
        return True
    defined = module.params.get("defined_tags")
    if defined is not None and getattr(alarm, "defined_tags", None) != defined:
        return True
    return False


def run_module():
    """Main module execution."""
    module_args = dict(
        compartment_id=dict(type="str"),
        display_name=dict(type="str"),
        metric_compartment_id=dict(type="str"),
        namespace=dict(type="str"),
        query=dict(type="str"),
        severity=dict(type="str", choices=["CRITICAL", "ERROR", "WARNING", "INFO"], default="CRITICAL"),
        destinations=dict(type="list", elements="str"),
        is_enabled=dict(type="bool", default=True),
        alarm_id=dict(type="str"),
        state=dict(type="str", choices=["present", "absent"], default="present"),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            ("state", "present", ("compartment_id", "display_name", "metric_compartment_id",
                                  "namespace", "query", "destinations"), True),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, MonitoringClient)
    state = module.params.get("state", "present")
    alarm_id = module.params.get("alarm_id")

    # Get existing resource
    alarm = None
    if alarm_id:
        alarm = get_alarm(client, alarm_id)
    elif module.params.get("compartment_id") and module.params.get("display_name"):
        alarm = find_alarm(client, module.params["compartment_id"], module.params["display_name"])

    if state == "absent":
        if alarm is None:
            module.exit_json(changed=False)
        if module.check_mode:
            module.exit_json(changed=True)
        delete_alarm(module, client, alarm)
        module.exit_json(changed=True)
        return

    # state == present
    if alarm is None:
        if not module.params.get("compartment_id") or not module.params.get("display_name"):
            module.fail_json(
                msg="compartment_id, display_name, and other required params are needed to create an alarm."
            )
        if module.check_mode:
            module.exit_json(changed=True)
        alarm = create_alarm(module, client)
        module.exit_json(changed=True, resource=to_dict(alarm))
        return

    if needs_update(module, alarm):
        if module.check_mode:
            module.exit_json(changed=True)
        alarm = update_alarm(module, client, alarm)
        module.exit_json(changed=True, resource=to_dict(alarm))
        return

    module.exit_json(changed=False, resource=to_dict(alarm))


def main():
    run_module()


if __name__ == "__main__":
    main()
