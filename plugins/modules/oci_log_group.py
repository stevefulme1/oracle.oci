# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Logging log groups."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_log_group
short_description: Manage OCI Logging log groups
description:
  - Create, update, and delete log groups in OCI Logging service.
  - Log groups are logical containers for organizing and managing logs.
version_added: "1.0.0"
author: Oracle (@oracle)
options:
  compartment_id:
    description:
      - The OCID of the compartment where the log group resides.
      - Required when creating a new log group.
    type: str
  display_name:
    description:
      - A user-friendly name for the log group.
      - Required when creating a new log group.
    type: str
  description:
    description:
      - Description for the log group.
    type: str
  log_group_id:
    description:
      - The OCID of the log group.
      - Required for update and delete operations.
    type: str
  state:
    description:
      - The desired state of the log group.
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
- name: Create a log group
  oracle.oci.oci_log_group:
    compartment_id: ocid1.compartment.oc1..example
    display_name: my-log-group
    description: Application logs for production
    state: present

- name: Update a log group description
  oracle.oci.oci_log_group:
    log_group_id: ocid1.loggroup.oc1..example
    description: Updated description for log group
    state: present

- name: Delete a log group
  oracle.oci.oci_log_group:
    log_group_id: ocid1.loggroup.oc1..example
    state: absent
"""

RETURN = r"""
resource:
  description: The log group resource details.
  returned: on success
  type: dict
  contains:
    id:
      description: The OCID of the log group.
      type: str
    compartment_id:
      description: The OCID of the compartment.
      type: str
    display_name:
      description: The display name of the log group.
      type: str
    description:
      description: The description of the log group.
      type: str
    lifecycle_state:
      description: The current lifecycle state of the log group.
      type: str
    time_created:
      description: The date and time the log group was created.
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
    wait_for_work_request,
)

try:
    import oci
    from oci.logging import LoggingManagementClient
    from oci.logging.models import (
        CreateLogGroupDetails,
        UpdateLogGroupDetails,
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


def get_log_group(client, log_group_id):
    """Get a log group by OCID, return None if not found."""
    try:
        response = call_with_retry(client.get_log_group, log_group_id)
        log_group = response.data
        if log_group.lifecycle_state in ("DELETED",):
            return None
        return log_group
    except oci.exceptions.ServiceError as e:
        if e.status == 404:
            return None
        raise


def find_log_group(client, compartment_id, display_name):
    """Find a log group by compartment and display name."""
    if not compartment_id or not display_name:
        return None
    log_groups = call_with_retry(
        client.list_log_groups,
        compartment_id,
    ).data
    for lg in log_groups:
        if lg.display_name == display_name and lg.lifecycle_state not in ("DELETED",):
            return get_log_group(client, lg.id)
    return None


def create_log_group(module, client):
    """Create a new log group."""
    freeform_tags = module.params.get("freeform_tags") or {}
    defined_tags = module.params.get("defined_tags") or {}

    kwargs = dict(
        compartment_id=module.params["compartment_id"],
        display_name=module.params["display_name"],
        freeform_tags=freeform_tags,
        defined_tags=defined_tags,
    )
    if module.params.get("description") is not None:
        kwargs["description"] = module.params["description"]

    details = CreateLogGroupDetails(**kwargs)
    response = call_with_retry(client.create_log_group, details)

    # Logging service uses work requests
    work_request_id = response.headers.get("opc-work-request-id")
    if work_request_id and module.params.get("wait", True):
        wait_for_work_request(module, client, work_request_id)

    # Extract the log group ID from the response or work request
    log_group_id = response.data.id if hasattr(response.data, "id") else None
    if log_group_id:
        return get_log_group(client, log_group_id)

    # If the ID was in headers (common pattern)
    resource_id = response.headers.get("location", "").split("/")[-1] if response.headers.get("location") else None
    if resource_id:
        return get_log_group(client, resource_id)

    return response.data


def update_log_group(module, client, log_group):
    """Update an existing log group."""
    kwargs = {}
    if module.params.get("display_name") is not None:
        kwargs["display_name"] = module.params["display_name"]
    if module.params.get("description") is not None:
        kwargs["description"] = module.params["description"]
    if module.params.get("freeform_tags") is not None:
        kwargs["freeform_tags"] = module.params["freeform_tags"]
    if module.params.get("defined_tags") is not None:
        kwargs["defined_tags"] = module.params["defined_tags"]

    if not kwargs:
        return log_group

    details = UpdateLogGroupDetails(**kwargs)
    response = call_with_retry(client.update_log_group, log_group.id, details)

    work_request_id = response.headers.get("opc-work-request-id")
    if work_request_id and module.params.get("wait", True):
        wait_for_work_request(module, client, work_request_id)

    return get_log_group(client, log_group.id)


def delete_log_group(module, client, log_group):
    """Delete a log group."""
    response = call_with_retry(client.delete_log_group, log_group.id)

    work_request_id = response.headers.get("opc-work-request-id")
    if work_request_id and module.params.get("wait", True):
        wait_for_work_request(module, client, work_request_id)


def needs_update(module, log_group):
    """Check if log group needs to be updated."""
    if module.params.get("display_name") and log_group.display_name != module.params["display_name"]:
        return True
    if (module.params.get("description") is not None
            and getattr(log_group, "description", None) != module.params["description"]):
        return True
    freeform = module.params.get("freeform_tags")
    if freeform is not None and getattr(log_group, "freeform_tags", None) != freeform:
        return True
    defined = module.params.get("defined_tags")
    if defined is not None and getattr(log_group, "defined_tags", None) != defined:
        return True
    return False


def run_module():
    """Main module execution."""
    module_args = dict(
        compartment_id=dict(type="str"),
        display_name=dict(type="str"),
        description=dict(type="str"),
        log_group_id=dict(type="str"),
        state=dict(type="str", choices=["present", "absent"], default="present"),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            ("state", "present", ("compartment_id", "display_name"), True),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, LoggingManagementClient)
    state = module.params.get("state", "present")
    log_group_id = module.params.get("log_group_id")

    # Get existing resource
    log_group = None
    if log_group_id:
        log_group = get_log_group(client, log_group_id)
    elif module.params.get("compartment_id") and module.params.get("display_name"):
        log_group = find_log_group(client, module.params["compartment_id"], module.params["display_name"])

    if state == "absent":
        if log_group is None:
            module.exit_json(changed=False)
        if module.check_mode:
            module.exit_json(changed=True)
        delete_log_group(module, client, log_group)
        module.exit_json(changed=True)
        return

    # state == present
    if log_group is None:
        if not module.params.get("compartment_id") or not module.params.get("display_name"):
            module.fail_json(msg="compartment_id and display_name are required to create a log group.")
        if module.check_mode:
            module.exit_json(changed=True)
        log_group = create_log_group(module, client)
        module.exit_json(changed=True, resource=to_dict(log_group))
        return

    if needs_update(module, log_group):
        if module.check_mode:
            module.exit_json(changed=True)
        log_group = update_log_group(module, client, log_group)
        module.exit_json(changed=True, resource=to_dict(log_group))
        return

    module.exit_json(changed=False, resource=to_dict(log_group))


def main():
    run_module()


if __name__ == "__main__":
    main()
