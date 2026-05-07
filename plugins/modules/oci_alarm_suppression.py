# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Monitoring alarm suppressions."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_alarm_suppression
short_description: Manage OCI Monitoring alarm suppressions
description:
  - Create and delete alarm suppression windows in OCI Monitoring.
  - Alarm suppressions temporarily silence alarm notifications during maintenance windows.
version_added: "1.0.0"
author: Oracle (@oracle)
options:
  alarm_id:
    description:
      - The OCID of the alarm to suppress.
      - Required when creating a suppression.
    type: str
  alarm_suppression_id:
    description:
      - The OCID of the alarm suppression.
      - Required for delete operations.
    type: str
  display_name:
    description:
      - A user-friendly name for the suppression.
      - Required when creating.
    type: str
  time_suppress_from:
    description:
      - The start time of the suppression window (RFC 3339 format).
      - Required when creating.
    type: str
  time_suppress_until:
    description:
      - The end time of the suppression window (RFC 3339 format).
      - Required when creating.
    type: str
  description:
    description:
      - A description of the suppression.
    type: str
  state:
    description:
      - The desired state of the alarm suppression.
    type: str
    default: present
    choices: [present, absent]
extends_documentation_fragment:
  - stevefulme1.oci_cloud.oci_common
"""

EXAMPLES = r"""
- name: Create an alarm suppression for a maintenance window
  stevefulme1.oci_cloud.oci_alarm_suppression:
    alarm_id: "ocid1.alarm.oc1..example"
    display_name: "weekend-maintenance"
    time_suppress_from: "2026-04-11T22:00:00Z"
    time_suppress_until: "2026-04-12T06:00:00Z"
    description: "Suppress during weekend maintenance"
    state: present

- name: Delete an alarm suppression
  stevefulme1.oci_cloud.oci_alarm_suppression:
    alarm_suppression_id: "ocid1.alarmsuppression.oc1..example"
    state: absent
"""

RETURN = r"""
resource:
  description: The alarm suppression details.
  returned: on success
  type: dict
  contains:
    id:
      description: The OCID of the alarm suppression.
      type: str
    alarm_id:
      description: The OCID of the alarm being suppressed.
      type: str
    display_name:
      description: The display name of the suppression.
      type: str
    time_suppress_from:
      description: The start time of the suppression.
      type: str
    time_suppress_until:
      description: The end time of the suppression.
      type: str
    description:
      description: The description of the suppression.
      type: str
    lifecycle_state:
      description: The current lifecycle state.
      type: str
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_common import OCI_COMMON_ARGS
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_auth import create_service_client
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_wait import call_with_retry

try:
    import oci
    from oci.monitoring import MonitoringClient
    from oci.monitoring.models import CreateAlarmSuppressionDetails
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


def get_suppression(client, alarm_suppression_id):
    """Get an alarm suppression by OCID, return None if not found."""
    try:
        response = call_with_retry(client.get_alarm_suppression, alarm_suppression_id)
        suppression = response.data
        if suppression.lifecycle_state in ("DELETED", "TERMINATED"):
            return None
        return suppression
    except oci.exceptions.ServiceError as e:
        if e.status == 404:
            return None
        raise


def find_suppression(client, alarm_id, display_name):
    """Find an alarm suppression by alarm ID and display name."""
    if not alarm_id or not display_name:
        return None
    suppressions = call_with_retry(
        client.list_alarm_suppressions,
        alarm_id,
    ).data
    for s in suppressions:
        if s.display_name == display_name and s.lifecycle_state not in ("DELETED", "TERMINATED"):
            return get_suppression(client, s.id)
    return None


def create_suppression(module, client):
    """Create a new alarm suppression."""
    details = CreateAlarmSuppressionDetails(
        alarm_id=module.params["alarm_id"],
        display_name=module.params["display_name"],
        time_suppress_from=module.params["time_suppress_from"],
        time_suppress_until=module.params["time_suppress_until"],
        description=module.params.get("description"),
    )
    response = call_with_retry(client.create_alarm_suppression, details)
    return response.data


def delete_suppression(module, client, suppression):
    """Delete an alarm suppression."""
    call_with_retry(client.delete_alarm_suppression, suppression.id)


def run_module():
    """Main module execution."""
    module_args = dict(
        alarm_id=dict(type="str"),
        alarm_suppression_id=dict(type="str"),
        display_name=dict(type="str"),
        time_suppress_from=dict(type="str"),
        time_suppress_until=dict(type="str"),
        description=dict(type="str"),
        state=dict(type="str", default="present", choices=["present", "absent"]),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            ("state", "present", ("alarm_id", "display_name", "time_suppress_from", "time_suppress_until"), True),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, MonitoringClient)
    state = module.params.get("state", "present")
    alarm_suppression_id = module.params.get("alarm_suppression_id")

    # Get existing resource
    suppression = None
    if alarm_suppression_id:
        suppression = get_suppression(client, alarm_suppression_id)
    elif module.params.get("alarm_id") and module.params.get("display_name"):
        suppression = find_suppression(client, module.params["alarm_id"], module.params["display_name"])

    if state == "absent":
        if suppression is None:
            module.exit_json(changed=False)
        if module.check_mode:
            module.exit_json(changed=True)
        delete_suppression(module, client, suppression)
        module.exit_json(changed=True)
        return

    # state == present: create only (suppressions cannot be updated)
    if suppression is not None:
        module.exit_json(changed=False, resource=to_dict(suppression))
        return

    if module.check_mode:
        module.exit_json(changed=True)
    suppression = create_suppression(module, client)
    module.exit_json(changed=True, resource=to_dict(suppression))


def main():
    run_module()


if __name__ == "__main__":
    main()
