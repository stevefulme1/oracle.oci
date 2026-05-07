# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Health Checks HTTP monitors."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_health_check
short_description: Manage OCI Health Checks HTTP monitors
description:
  - Create, update, and delete HTTP monitors in OCI Health Checks service.
  - HTTP monitors perform external health checks against specified targets.
version_added: "1.0.0"
author: Oracle (@oracle)
options:
  compartment_id:
    description:
      - The OCID of the compartment.
      - Required when creating.
    type: str
  monitor_id:
    description:
      - The OCID of the HTTP monitor.
      - Required for update and delete operations.
    type: str
  display_name:
    description:
      - A user-friendly name for the monitor.
      - Required when creating.
    type: str
  targets:
    description:
      - A list of targets (hostnames or IP addresses) to monitor.
      - Required when creating.
    type: list
    elements: str
  protocol:
    description:
      - The protocol to use for the health check.
    type: str
    choices: [HTTP, HTTPS]
    default: HTTPS
  port:
    description:
      - The port to use for the health check.
    type: int
    default: 443
  path:
    description:
      - The URL path to check.
    type: str
    default: /
  interval_in_seconds:
    description:
      - The interval between health checks in seconds.
    type: int
    default: 30
  timeout_in_seconds:
    description:
      - The timeout for each health check in seconds.
    type: int
    default: 30
  is_enabled:
    description:
      - Whether the monitor is enabled.
    type: bool
    default: true
  freeform_tags:
    description:
      - Free-form tags for this resource.
    type: dict
  defined_tags:
    description:
      - Defined tags for this resource.
    type: dict
  state:
    description:
      - The desired state of the monitor.
    type: str
    default: present
    choices: [present, absent]
extends_documentation_fragment:
  - stevefulme1.oci_cloud.oci_common
"""

EXAMPLES = r"""
- name: Create an HTTP health check
  stevefulme1.oci_cloud.oci_health_check:
    compartment_id: "ocid1.compartment.oc1..example"
    display_name: "web-health-check"
    targets:
      - "www.example.com"
    protocol: HTTPS
    port: 443
    path: /health
    interval_in_seconds: 30
    timeout_in_seconds: 10
    is_enabled: true
    state: present

- name: Disable a health check
  stevefulme1.oci_cloud.oci_health_check:
    monitor_id: "ocid1.httpmonitor.oc1..example"
    is_enabled: false
    state: present

- name: Delete a health check
  stevefulme1.oci_cloud.oci_health_check:
    monitor_id: "ocid1.httpmonitor.oc1..example"
    state: absent
"""

RETURN = r"""
resource:
  description: The HTTP monitor details.
  returned: on success
  type: dict
  contains:
    id:
      description: The OCID of the HTTP monitor.
      type: str
    display_name:
      description: The display name of the monitor.
      type: str
    compartment_id:
      description: The OCID of the compartment.
      type: str
    targets:
      description: The list of targets.
      type: list
    protocol:
      description: The protocol used.
      type: str
    port:
      description: The port number.
      type: int
    is_enabled:
      description: Whether the monitor is enabled.
      type: bool
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_common import OCI_COMMON_ARGS
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_auth import create_service_client
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_wait import call_with_retry

try:
    import oci
    from oci.healthchecks import HealthChecksClient
    from oci.healthchecks.models import (
        CreateHttpMonitorDetails,
        UpdateHttpMonitorDetails,
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


def get_monitor(client, monitor_id):
    """Get an HTTP monitor by OCID, return None if not found."""
    try:
        response = call_with_retry(client.get_http_monitor, monitor_id)
        return response.data
    except oci.exceptions.ServiceError as e:
        if e.status == 404:
            return None
        raise


def find_monitor(client, compartment_id, display_name):
    """Find an HTTP monitor by compartment and display name."""
    if not compartment_id or not display_name:
        return None
    monitors = call_with_retry(
        client.list_http_monitors,
        compartment_id,
    ).data
    for m in monitors:
        if m.display_name == display_name:
            return get_monitor(client, m.id)
    return None


def create_monitor(module, client):
    """Create a new HTTP monitor."""
    freeform_tags = module.params.get("freeform_tags") or {}
    defined_tags = module.params.get("defined_tags") or {}

    details = CreateHttpMonitorDetails(
        compartment_id=module.params["compartment_id"],
        display_name=module.params["display_name"],
        targets=module.params["targets"],
        protocol=module.params.get("protocol", "HTTPS"),
        port=module.params.get("port", 443),
        path=module.params.get("path", "/"),
        interval_in_seconds=module.params.get("interval_in_seconds", 30),
        timeout_in_seconds=module.params.get("timeout_in_seconds", 30),
        is_enabled=module.params.get("is_enabled", True),
        freeform_tags=freeform_tags,
        defined_tags=defined_tags,
    )
    response = call_with_retry(client.create_http_monitor, details)
    return response.data


def update_monitor(module, client, monitor):
    """Update an existing HTTP monitor."""
    kwargs = {}
    for attr in ("display_name", "targets", "protocol", "port", "path",
                 "interval_in_seconds", "timeout_in_seconds", "is_enabled"):
        value = module.params.get(attr)
        if value is not None:
            kwargs[attr] = value
    if module.params.get("freeform_tags") is not None:
        kwargs["freeform_tags"] = module.params["freeform_tags"]
    if module.params.get("defined_tags") is not None:
        kwargs["defined_tags"] = module.params["defined_tags"]

    if not kwargs:
        return monitor

    details = UpdateHttpMonitorDetails(**kwargs)
    response = call_with_retry(client.update_http_monitor, monitor.id, details)
    return response.data


def delete_monitor(module, client, monitor):
    """Delete an HTTP monitor."""
    call_with_retry(client.delete_http_monitor, monitor.id)


def needs_update(module, monitor):
    """Check if the monitor needs updating."""
    check_attrs = [
        "display_name", "targets", "protocol", "port", "path",
        "interval_in_seconds", "timeout_in_seconds", "is_enabled",
    ]
    for attr in check_attrs:
        desired = module.params.get(attr)
        if desired is not None and getattr(monitor, attr, None) != desired:
            return True
    if module.params.get("freeform_tags") is not None:
        if getattr(monitor, "freeform_tags", None) != module.params["freeform_tags"]:
            return True
    if module.params.get("defined_tags") is not None:
        if getattr(monitor, "defined_tags", None) != module.params["defined_tags"]:
            return True
    return False


def run_module():
    """Main module execution."""
    module_args = dict(
        compartment_id=dict(type="str"),
        monitor_id=dict(type="str"),
        display_name=dict(type="str"),
        targets=dict(type="list", elements="str"),
        protocol=dict(type="str", choices=["HTTP", "HTTPS"], default="HTTPS"),
        port=dict(type="int", default=443),
        path=dict(type="str", default="/"),
        interval_in_seconds=dict(type="int", default=30),
        timeout_in_seconds=dict(type="int", default=30),
        is_enabled=dict(type="bool", default=True),
        state=dict(type="str", default="present", choices=["present", "absent"]),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            ("state", "present", ("compartment_id", "display_name", "targets"), True),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, HealthChecksClient)
    state = module.params.get("state", "present")
    monitor_id = module.params.get("monitor_id")

    # Get existing resource
    monitor = None
    if monitor_id:
        monitor = get_monitor(client, monitor_id)
    elif module.params.get("compartment_id") and module.params.get("display_name"):
        monitor = find_monitor(client, module.params["compartment_id"], module.params["display_name"])

    if state == "absent":
        if monitor is None:
            module.exit_json(changed=False)
        if module.check_mode:
            module.exit_json(changed=True)
        delete_monitor(module, client, monitor)
        module.exit_json(changed=True)
        return

    # state == present
    if monitor is None:
        if not module.params.get("compartment_id") or not module.params.get("display_name"):
            module.fail_json(msg="compartment_id, display_name, and targets are required to create a monitor.")
        if module.check_mode:
            module.exit_json(changed=True)
        monitor = create_monitor(module, client)
        module.exit_json(changed=True, resource=to_dict(monitor))
        return

    if needs_update(module, monitor):
        if module.check_mode:
            module.exit_json(changed=True)
        monitor = update_monitor(module, client, monitor)
        module.exit_json(changed=True, resource=to_dict(monitor))
        return

    module.exit_json(changed=False, resource=to_dict(monitor))


def main():
    run_module()


if __name__ == "__main__":
    main()
