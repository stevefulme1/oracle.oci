# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI File Storage Export Sets."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_export_set
short_description: Manage OCI File Storage Export Sets
description:
  - Update and read export sets in OCI File Storage.
  - Export sets are created automatically with mount targets and cannot be created or deleted directly.
version_added: "1.0.0"
author: Oracle (@oracle)
options:
  export_set_id:
    description:
      - The OCID of the export set.
      - Required for all operations.
    type: str
    required: true
  display_name:
    description:
      - A user-friendly name for the export set.
    type: str
  max_fs_stat_bytes:
    description:
      - Controls the maximum tbytes, fbytes, and abytes values reported by NFS FSSTAT.
    type: int
  max_fs_stat_files:
    description:
      - Controls the maximum tfiles, ffiles, and afiles values reported by NFS FSSTAT.
    type: int
  state:
    description:
      - The desired state of the export set. Only present is supported.
    type: str
    default: present
    choices: [present]
extends_documentation_fragment:
  - stevefulme1.oci_cloud.oci_common
"""

EXAMPLES = r"""
- name: Update an export set
  stevefulme1.oci_cloud.oci_export_set:
    export_set_id: "ocid1.exportset.oc1..example"
    display_name: "my-export-set"
    max_fs_stat_bytes: 8589934592
    max_fs_stat_files: 100000
    state: present

- name: Update export set display name
  stevefulme1.oci_cloud.oci_export_set:
    export_set_id: "ocid1.exportset.oc1..example"
    display_name: "renamed-export-set"
    state: present
"""

RETURN = r"""
resource:
  description: The export set details.
  returned: on success
  type: dict
  contains:
    id:
      description: The OCID of the export set.
      type: str
    display_name:
      description: The display name of the export set.
      type: str
    compartment_id:
      description: The OCID of the compartment.
      type: str
    max_fs_stat_bytes:
      description: Maximum tbytes reported by NFS FSSTAT.
      type: int
    max_fs_stat_files:
      description: Maximum tfiles reported by NFS FSSTAT.
      type: int
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
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_wait import call_with_retry

try:
    import oci
    from oci.file_storage import FileStorageClient
    from oci.file_storage.models import UpdateExportSetDetails
    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False


def get_export_set(client, export_set_id):
    """Get an export set by OCID, return None if not found."""
    try:
        response = call_with_retry(client.get_export_set, export_set_id)
        export_set = response.data
        if export_set.lifecycle_state in ("DELETED", "TERMINATED"):
            return None
        return export_set
    except oci.exceptions.ServiceError as e:
        if e.status == 404:
            return None
        raise


def update_export_set(module, client, export_set):
    """Update an existing export set."""
    kwargs = {}
    if module.params.get("display_name") is not None:
        kwargs["display_name"] = module.params["display_name"]
    if module.params.get("max_fs_stat_bytes") is not None:
        kwargs["max_fs_stat_bytes"] = module.params["max_fs_stat_bytes"]
    if module.params.get("max_fs_stat_files") is not None:
        kwargs["max_fs_stat_files"] = module.params["max_fs_stat_files"]

    if not kwargs:
        return export_set

    details = UpdateExportSetDetails(**kwargs)
    response = call_with_retry(
        client.update_export_set,
        export_set.id,
        details,
    )
    return response.data


def needs_update(module, export_set):
    """Check if the export set needs updating."""
    for attr in ("display_name", "max_fs_stat_bytes", "max_fs_stat_files"):
        desired = module.params.get(attr)
        if desired is not None and getattr(export_set, attr, None) != desired:
            return True
    return False


def run_module():
    """Main module execution."""
    module_args = dict(
        export_set_id=dict(type="str", required=True),
        display_name=dict(type="str"),
        max_fs_stat_bytes=dict(type="int"),
        max_fs_stat_files=dict(type="int"),
        state=dict(type="str", default="present", choices=["present"]),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, FileStorageClient)
    export_set_id = module.params["export_set_id"]

    export_set = get_export_set(client, export_set_id)
    if export_set is None:
        module.fail_json(msg="Export set not found: %s" % export_set_id)

    if needs_update(module, export_set):
        if module.check_mode:
            module.exit_json(changed=True)
        export_set = update_export_set(module, client, export_set)
        module.exit_json(changed=True, resource=to_dict(export_set))
        return

    module.exit_json(changed=False, resource=to_dict(export_set))


def main():
    run_module()


if __name__ == "__main__":
    main()
