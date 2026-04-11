# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI File Storage Snapshots."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_snapshot
short_description: Manage OCI File Storage Snapshots
description:
  - Create, update, and delete snapshots for OCI File Storage file systems.
  - Snapshots provide point-in-time copies of file systems.
version_added: "1.0.0"
author: Oracle (@oracle)
options:
  file_system_id:
    description:
      - The OCID of the file system to create the snapshot for.
      - Required when creating a snapshot.
    type: str
  snapshot_id:
    description:
      - The OCID of the snapshot.
      - Required for update and delete operations.
    type: str
  name:
    description:
      - The name of the snapshot.
      - Required when creating a snapshot.
    type: str
  expiration_time:
    description:
      - The time when the snapshot will be automatically deleted (RFC 3339 format).
    type: str
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
      - The desired state of the snapshot.
    type: str
    default: present
    choices: [present, absent]
extends_documentation_fragment:
  - oracle.oci.oci_common
"""

EXAMPLES = r"""
- name: Create a snapshot
  oracle.oci.oci_snapshot:
    file_system_id: "ocid1.filesystem.oc1..example"
    name: "daily-snapshot-2026-04-10"
    state: present

- name: Create a snapshot with expiration
  oracle.oci.oci_snapshot:
    file_system_id: "ocid1.filesystem.oc1..example"
    name: "temp-snapshot"
    expiration_time: "2026-05-10T00:00:00Z"
    state: present

- name: Delete a snapshot
  oracle.oci.oci_snapshot:
    snapshot_id: "ocid1.snapshot.oc1..example"
    state: absent
"""

RETURN = r"""
resource:
  description: The snapshot details.
  returned: on success
  type: dict
  contains:
    id:
      description: The OCID of the snapshot.
      type: str
    file_system_id:
      description: The OCID of the file system.
      type: str
    name:
      description: The name of the snapshot.
      type: str
    lifecycle_state:
      description: The current lifecycle state.
      type: str
    time_created:
      description: The date and time the snapshot was created.
      type: str
    expiration_time:
      description: The time when the snapshot will expire.
      type: str
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.oracle.oci.plugins.module_utils.oci_common import OCI_COMMON_ARGS
from ansible_collections.oracle.oci.plugins.module_utils.oci_auth import create_service_client
from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import (
    call_with_retry,
    wait_for_resource,
)

try:
    import oci
    from oci.file_storage import FileStorageClient
    from oci.file_storage.models import (
        CreateSnapshotDetails,
        UpdateSnapshotDetails,
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


def get_snapshot(client, snapshot_id):
    """Get a snapshot by OCID, return None if not found."""
    try:
        response = call_with_retry(client.get_snapshot, snapshot_id)
        snapshot = response.data
        if snapshot.lifecycle_state in ("DELETED", "TERMINATED"):
            return None
        return snapshot
    except oci.exceptions.ServiceError as e:
        if e.status == 404:
            return None
        raise


def find_snapshot(client, file_system_id, name):
    """Find a snapshot by file system and name."""
    if not file_system_id or not name:
        return None
    snapshots = call_with_retry(
        client.list_snapshots,
        file_system_id,
    ).data
    for s in snapshots:
        if s.name == name and s.lifecycle_state not in ("DELETED", "TERMINATED"):
            return get_snapshot(client, s.id)
    return None


def create_snapshot(module, client):
    """Create a new snapshot."""
    freeform_tags = module.params.get("freeform_tags") or {}
    defined_tags = module.params.get("defined_tags") or {}

    details = CreateSnapshotDetails(
        file_system_id=module.params["file_system_id"],
        name=module.params["name"],
        expiration_time=module.params.get("expiration_time"),
        freeform_tags=freeform_tags,
        defined_tags=defined_tags,
    )
    response = call_with_retry(client.create_snapshot, details)
    snapshot = response.data

    if module.params.get("wait", True):
        snapshot = wait_for_resource(
            module,
            client.get_snapshot,
            snapshot.id,
            target_states={"ACTIVE"},
        )
    return snapshot


def update_snapshot(module, client, snapshot):
    """Update an existing snapshot."""
    kwargs = {}
    if module.params.get("expiration_time") is not None:
        kwargs["expiration_time"] = module.params["expiration_time"]
    if module.params.get("freeform_tags") is not None:
        kwargs["freeform_tags"] = module.params["freeform_tags"]
    if module.params.get("defined_tags") is not None:
        kwargs["defined_tags"] = module.params["defined_tags"]

    if not kwargs:
        return snapshot

    details = UpdateSnapshotDetails(**kwargs)
    response = call_with_retry(client.update_snapshot, snapshot.id, details)
    return response.data


def delete_snapshot(module, client, snapshot):
    """Delete a snapshot."""
    call_with_retry(client.delete_snapshot, snapshot.id)


def needs_update(module, snapshot):
    """Check if the snapshot needs updating."""
    if module.params.get("expiration_time") is not None:
        if str(getattr(snapshot, "expiration_time", None)) != module.params["expiration_time"]:
            return True
    if module.params.get("freeform_tags") is not None:
        if getattr(snapshot, "freeform_tags", None) != module.params["freeform_tags"]:
            return True
    if module.params.get("defined_tags") is not None:
        if getattr(snapshot, "defined_tags", None) != module.params["defined_tags"]:
            return True
    return False


def run_module():
    """Main module execution."""
    module_args = dict(
        file_system_id=dict(type="str"),
        snapshot_id=dict(type="str"),
        name=dict(type="str"),
        expiration_time=dict(type="str"),
        state=dict(type="str", default="present", choices=["present", "absent"]),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            ("state", "present", ("file_system_id", "name"), True),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, FileStorageClient)
    state = module.params.get("state", "present")
    snapshot_id = module.params.get("snapshot_id")

    # Get existing resource
    snapshot = None
    if snapshot_id:
        snapshot = get_snapshot(client, snapshot_id)
    elif module.params.get("file_system_id") and module.params.get("name"):
        snapshot = find_snapshot(client, module.params["file_system_id"], module.params["name"])

    if state == "absent":
        if snapshot is None:
            module.exit_json(changed=False)
        if module.check_mode:
            module.exit_json(changed=True)
        delete_snapshot(module, client, snapshot)
        module.exit_json(changed=True)
        return

    # state == present
    if snapshot is None:
        if not module.params.get("file_system_id") or not module.params.get("name"):
            module.fail_json(msg="file_system_id and name are required to create a snapshot.")
        if module.check_mode:
            module.exit_json(changed=True)
        snapshot = create_snapshot(module, client)
        module.exit_json(changed=True, resource=to_dict(snapshot))
        return

    if needs_update(module, snapshot):
        if module.check_mode:
            module.exit_json(changed=True)
        snapshot = update_snapshot(module, client, snapshot)
        module.exit_json(changed=True, resource=to_dict(snapshot))
        return

    module.exit_json(changed=False, resource=to_dict(snapshot))


def main():
    run_module()


if __name__ == "__main__":
    main()
