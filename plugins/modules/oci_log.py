# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Logging log resources."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_log
short_description: Manage OCI Logging log resources
description:
  - Create, update, and delete log resources in OCI Logging service.
  - Logs capture events from OCI services or custom applications.
version_added: "1.0.0"
author: Oracle (@oracle)
options:
  log_group_id:
    description:
      - The OCID of the log group.
      - Required for all operations.
    type: str
    required: true
  log_id:
    description:
      - The OCID of the log.
      - Required for update and delete operations.
    type: str
  display_name:
    description:
      - A user-friendly name for the log.
      - Required when creating.
    type: str
  log_type:
    description:
      - The type of log.
    type: str
    choices: [CUSTOM, SERVICE]
    default: CUSTOM
  configuration:
    description:
      - Log configuration details for SERVICE logs.
    type: dict
    suboptions:
      source:
        description: The source of the log.
        type: dict
      category:
        description: Log category.
        type: str
      service:
        description: The service generating the log.
        type: str
      resource:
        description: The resource generating the log.
        type: str
      compartment_id:
        description: The compartment of the resource.
        type: str
  is_enabled:
    description:
      - Whether the log is enabled.
    type: bool
    default: true
  retention_duration:
    description:
      - Log retention duration in days.
    type: int
  state:
    description:
      - The desired state of the log.
    type: str
    default: present
    choices: [present, absent]
extends_documentation_fragment:
  - stevefulme1.oci_cloud.oci_common
"""

EXAMPLES = r"""
- name: Create a custom log
  stevefulme1.oci_cloud.oci_log:
    log_group_id: "ocid1.loggroup.oc1..example"
    display_name: "my-custom-log"
    log_type: CUSTOM
    is_enabled: true
    state: present

- name: Create a service log
  stevefulme1.oci_cloud.oci_log:
    log_group_id: "ocid1.loggroup.oc1..example"
    display_name: "vcn-flow-log"
    log_type: SERVICE
    configuration:
      source:
        source_type: OCISERVICE
      service: flowlogs
      resource: "ocid1.subnet.oc1..example"
      category: all
      compartment_id: "ocid1.compartment.oc1..example"
    is_enabled: true
    state: present

- name: Delete a log
  stevefulme1.oci_cloud.oci_log:
    log_group_id: "ocid1.loggroup.oc1..example"
    log_id: "ocid1.log.oc1..example"
    state: absent
"""

RETURN = r"""
resource:
  description: The log resource details.
  returned: on success
  type: dict
  contains:
    id:
      description: The OCID of the log.
      type: str
    display_name:
      description: The display name of the log.
      type: str
    log_group_id:
      description: The OCID of the log group.
      type: str
    log_type:
      description: The type of log (CUSTOM or SERVICE).
      type: str
    is_enabled:
      description: Whether the log is enabled.
      type: bool
    lifecycle_state:
      description: The current lifecycle state.
      type: str
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_common import (
    OCI_COMMON_ARGS,
    to_dict,
)
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_auth import create_service_client
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_wait import (
    call_with_retry,
)

try:
    import oci
    from oci.logging import LoggingManagementClient
    from oci.logging.models import (
        CreateLogDetails,
        UpdateLogDetails,
        Configuration,
        OciService,
    )
    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False


def get_log(client, log_group_id, log_id):
    """Get a log by OCID, return None if not found."""
    try:
        response = call_with_retry(client.get_log, log_group_id, log_id)
        log = response.data
        if log.lifecycle_state in ("DELETED", "TERMINATED"):
            return None
        return log
    except oci.exceptions.ServiceError as e:
        if e.status == 404:
            return None
        raise


def find_log(client, log_group_id, display_name):
    """Find a log by display name within a log group."""
    if not display_name:
        return None
    logs = call_with_retry(client.list_logs, log_group_id).data
    for log_entry in logs:
        if log_entry.display_name == display_name and log_entry.lifecycle_state not in ("DELETED", "TERMINATED"):
            return get_log(client, log_group_id, log_entry.id)
    return None


def build_configuration(config_param):
    """Build a Configuration object from module params."""
    if not config_param:
        return None
    source = None
    if config_param.get("source"):
        source = OciService(
            source_type=config_param["source"].get("source_type", "OCISERVICE"),
            service=config_param.get("service"),
            resource=config_param.get("resource"),
            category=config_param.get("category"),
        )
    return Configuration(
        source=source,
        compartment_id=config_param.get("compartment_id"),
    )


def create_log(module, client):
    """Create a new log resource."""
    details = CreateLogDetails(
        display_name=module.params["display_name"],
        log_type=module.params.get("log_type", "CUSTOM"),
        configuration=build_configuration(module.params.get("configuration")),
        is_enabled=module.params.get("is_enabled", True),
        retention_duration=module.params.get("retention_duration"),
    )
    response = call_with_retry(
        client.create_log,
        module.params["log_group_id"],
        details,
    )
    work_request_id = response.headers.get("opc-work-request-id")
    if work_request_id and module.params.get("wait", True):
        # List logs to find the new one
        logs = call_with_retry(client.list_logs, module.params["log_group_id"]).data
        for log_entry in logs:
            if log_entry.display_name == module.params["display_name"]:
                return get_log(client, module.params["log_group_id"], log_entry.id)
    return response.data if hasattr(response, "data") else None


def update_log(module, client, log):
    """Update an existing log resource."""
    kwargs = {}
    if module.params.get("display_name") is not None:
        kwargs["display_name"] = module.params["display_name"]
    if module.params.get("is_enabled") is not None:
        kwargs["is_enabled"] = module.params["is_enabled"]
    if module.params.get("retention_duration") is not None:
        kwargs["retention_duration"] = module.params["retention_duration"]
    if module.params.get("configuration") is not None:
        kwargs["configuration"] = build_configuration(module.params["configuration"])

    if not kwargs:
        return log

    details = UpdateLogDetails(**kwargs)
    call_with_retry(
        client.update_log,
        module.params["log_group_id"],
        log.id,
        details,
    )
    return get_log(client, module.params["log_group_id"], log.id)


def delete_log(module, client, log):
    """Delete a log resource."""
    call_with_retry(
        client.delete_log,
        module.params["log_group_id"],
        log.id,
    )


def needs_update(module, log):
    """Check if the log needs updating."""
    for attr in ("display_name", "is_enabled", "retention_duration"):
        desired = module.params.get(attr)
        if desired is not None and getattr(log, attr, None) != desired:
            return True
    return False


def run_module():
    """Main module execution."""
    module_args = dict(
        log_group_id=dict(type="str", required=True),
        log_id=dict(type="str"),
        display_name=dict(type="str"),
        log_type=dict(type="str", choices=["CUSTOM", "SERVICE"], default="CUSTOM"),
        configuration=dict(type="dict"),
        is_enabled=dict(type="bool", default=True),
        retention_duration=dict(type="int"),
        state=dict(type="str", default="present", choices=["present", "absent"]),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            ("state", "present", ("display_name",), True),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, LoggingManagementClient)
    state = module.params.get("state", "present")
    log_group_id = module.params["log_group_id"]
    log_id = module.params.get("log_id")

    # Get existing resource
    log = None
    if log_id:
        log = get_log(client, log_group_id, log_id)
    elif module.params.get("display_name"):
        log = find_log(client, log_group_id, module.params["display_name"])

    if state == "absent":
        if log is None:
            module.exit_json(changed=False)
        if module.check_mode:
            module.exit_json(changed=True)
        delete_log(module, client, log)
        module.exit_json(changed=True)
        return

    # state == present
    if log is None:
        if not module.params.get("display_name"):
            module.fail_json(msg="display_name is required to create a log.")
        if module.check_mode:
            module.exit_json(changed=True)
        log = create_log(module, client)
        module.exit_json(changed=True, resource=to_dict(log))
        return

    if needs_update(module, log):
        if module.check_mode:
            module.exit_json(changed=True)
        log = update_log(module, client, log)
        module.exit_json(changed=True, resource=to_dict(log))
        return

    module.exit_json(changed=False, resource=to_dict(log))


def main():
    run_module()


if __name__ == "__main__":
    main()
