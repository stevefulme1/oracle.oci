# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Object Storage Pre-Authenticated Requests."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_preauthenticated_request
short_description: Manage OCI Object Storage Pre-Authenticated Requests
description:
  - Create and delete pre-authenticated requests for OCI Object Storage.
  - Pre-authenticated requests provide a way to let users access a bucket
    or object without having their own credentials.
version_added: "1.0.0"
author: Oracle (@oracle)
options:
  namespace_name:
    description:
      - The Object Storage namespace.
    type: str
    required: true
  bucket_name:
    description:
      - The name of the bucket.
    type: str
    required: true
  par_id:
    description:
      - The unique identifier for the pre-authenticated request.
      - Required for delete operations.
    type: str
  name:
    description:
      - A user-specified name for the pre-authenticated request.
      - Required when creating.
    type: str
  access_type:
    description:
      - The operation that can be performed on this resource.
    type: str
    choices: [ObjectRead, ObjectWrite, AnyObjectRead, AnyObjectReadWrite]
    default: ObjectRead
  time_expires:
    description:
      - The expiration date for the pre-authenticated request (RFC 3339 format).
      - Required when creating.
    type: str
  object_name:
    description:
      - The name of the object that is being granted access to.
      - Required for ObjectRead and ObjectWrite access types.
    type: str
  state:
    description:
      - The desired state of the pre-authenticated request.
    type: str
    default: present
    choices: [present, absent]
extends_documentation_fragment:
  - stevefulme1.oci_cloud.oci_common
"""

EXAMPLES = r"""
- name: Create a pre-authenticated request for reading an object
  stevefulme1.oci_cloud.oci_preauthenticated_request:
    namespace_name: "mynamespace"
    bucket_name: "my-bucket"
    name: "my-par"
    access_type: ObjectRead
    time_expires: "2026-12-31T00:00:00Z"
    object_name: "my-file.txt"
    state: present

- name: Create a pre-authenticated request for any object read
  stevefulme1.oci_cloud.oci_preauthenticated_request:
    namespace_name: "mynamespace"
    bucket_name: "my-bucket"
    name: "bucket-par"
    access_type: AnyObjectRead
    time_expires: "2026-12-31T00:00:00Z"
    state: present

- name: Delete a pre-authenticated request
  stevefulme1.oci_cloud.oci_preauthenticated_request:
    namespace_name: "mynamespace"
    bucket_name: "my-bucket"
    par_id: "example-par-id"
    state: absent
"""

RETURN = r"""
resource:
  description: The pre-authenticated request details.
  returned: on success
  type: dict
  contains:
    id:
      description: The unique identifier for the pre-authenticated request.
      type: str
    name:
      description: The user-specified name of the pre-authenticated request.
      type: str
    access_type:
      description: The operation that can be performed on this resource.
      type: str
    time_expires:
      description: The expiration date of the pre-authenticated request.
      type: str
    access_uri:
      description: The URI to embed in the URL when using the pre-authenticated request.
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
    from oci.object_storage import ObjectStorageClient
    from oci.object_storage.models import CreatePreauthenticatedRequestDetails
    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False


def get_par(client, namespace_name, bucket_name, par_id):
    """Get a pre-authenticated request by ID, return None if not found."""
    try:
        response = call_with_retry(
            client.get_preauthenticated_request,
            namespace_name,
            bucket_name,
            par_id,
        )
        return response.data
    except oci.exceptions.ServiceError as e:
        if e.status == 404:
            return None
        raise


def find_par(client, namespace_name, bucket_name, name):
    """Find a pre-authenticated request by name."""
    if not name:
        return None
    pars = call_with_retry(
        client.list_preauthenticated_requests,
        namespace_name,
        bucket_name,
    ).data
    for p in pars:
        if p.name == name:
            return p
    return None


def create_par(module, client):
    """Create a new pre-authenticated request."""
    details = CreatePreauthenticatedRequestDetails(
        name=module.params["name"],
        access_type=module.params.get("access_type", "ObjectRead"),
        time_expires=module.params["time_expires"],
        object_name=module.params.get("object_name"),
    )
    response = call_with_retry(
        client.create_preauthenticated_request,
        module.params["namespace_name"],
        module.params["bucket_name"],
        details,
    )
    return response.data


def delete_par(module, client, par):
    """Delete a pre-authenticated request."""
    par_id = module.params.get("par_id") or par.id
    call_with_retry(
        client.delete_preauthenticated_request,
        module.params["namespace_name"],
        module.params["bucket_name"],
        par_id,
    )


def run_module():
    """Main module execution."""
    module_args = dict(
        namespace_name=dict(type="str", required=True),
        bucket_name=dict(type="str", required=True),
        par_id=dict(type="str"),
        name=dict(type="str"),
        access_type=dict(
            type="str",
            default="ObjectRead",
            choices=["ObjectRead", "ObjectWrite", "AnyObjectRead", "AnyObjectReadWrite"],
        ),
        time_expires=dict(type="str"),
        object_name=dict(type="str"),
        state=dict(type="str", default="present", choices=["present", "absent"]),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            ("state", "present", ("name", "time_expires"), True),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, ObjectStorageClient)
    state = module.params.get("state", "present")
    namespace_name = module.params["namespace_name"]
    bucket_name = module.params["bucket_name"]
    par_id = module.params.get("par_id")

    # Get existing resource
    par = None
    if par_id:
        par = get_par(client, namespace_name, bucket_name, par_id)
    elif module.params.get("name"):
        par = find_par(client, namespace_name, bucket_name, module.params["name"])

    if state == "absent":
        if par is None:
            module.exit_json(changed=False)
        if module.check_mode:
            module.exit_json(changed=True)
        delete_par(module, client, par)
        module.exit_json(changed=True)
        return

    # state == present: create only (PARs cannot be updated)
    if par is not None:
        module.exit_json(changed=False, resource=to_dict(par))
        return

    if not module.params.get("name") or not module.params.get("time_expires"):
        module.fail_json(msg="name and time_expires are required to create a pre-authenticated request.")
    if module.check_mode:
        module.exit_json(changed=True)
    par = create_par(module, client)
    module.exit_json(changed=True, resource=to_dict(par))


def main():
    run_module()


if __name__ == "__main__":
    main()
