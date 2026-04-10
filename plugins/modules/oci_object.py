#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Object Storage Objects."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import os

DOCUMENTATION = r"""
---
module: oci_object
short_description: Manage OCI Object Storage Objects
description:
    - Upload, download, and delete objects in Oracle Cloud Infrastructure Object Storage.
    - Uses the ObjectStorageClient from the OCI Python SDK.
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
            - The name of the bucket containing the object.
        type: str
        required: true
    object_name:
        description:
            - The name of the object in the bucket.
        type: str
        required: true
    src:
        description:
            - Local file path to upload to Object Storage.
            - Required when state is present.
        type: path
    dest:
        description:
            - Local file path where the object will be downloaded.
            - When specified with state=present, the object is downloaded instead of uploaded.
        type: path
    content_type:
        description:
            - The content type of the object being uploaded.
        type: str
        default: application/octet-stream
    force:
        description:
            - Whether to overwrite an existing object or local file.
        type: bool
        default: false
    state:
        description:
            - The desired state of the object.
            - Use C(present) to upload or download, C(absent) to delete.
        type: str
        default: present
        choices: [present, absent]
extends_documentation_fragment:
    - oracle.oci.oci_common
"""

EXAMPLES = r"""
- name: Upload a file to Object Storage
  oracle.oci.oci_object:
    namespace_name: "mynamespace"
    bucket_name: "my-bucket"
    object_name: "data/myfile.txt"
    src: "/tmp/myfile.txt"
    content_type: "text/plain"
    state: present

- name: Download an object to local file
  oracle.oci.oci_object:
    namespace_name: "mynamespace"
    bucket_name: "my-bucket"
    object_name: "data/myfile.txt"
    dest: "/tmp/downloaded.txt"
    state: present

- name: Delete an object
  oracle.oci.oci_object:
    namespace_name: "mynamespace"
    bucket_name: "my-bucket"
    object_name: "data/myfile.txt"
    state: absent
"""

RETURN = r"""
resource:
    description: Details of the object.
    returned: on success
    type: dict
    sample:
        namespace_name: "mynamespace"
        bucket_name: "my-bucket"
        object_name: "data/myfile.txt"
        content_type: "text/plain"
        size: 1024
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.oracle.oci.plugins.module_utils.oci_common import OCI_COMMON_ARGS
from ansible_collections.oracle.oci.plugins.module_utils.oci_auth import create_service_client
from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import call_with_retry

try:
    import oci
    from oci.object_storage import ObjectStorageClient
    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False


def get_object_head(client, namespace_name, bucket_name, object_name):
    """Check if an object exists and return its metadata."""
    try:
        response = call_with_retry(
            client.head_object,
            namespace_name,
            bucket_name,
            object_name,
        )
        return response.headers
    except oci.exceptions.ServiceError as e:
        if e.status == 404:
            return None
        raise


def upload_object(module, client):
    """Upload a local file to Object Storage."""
    namespace_name = module.params["namespace_name"]
    bucket_name = module.params["bucket_name"]
    object_name = module.params["object_name"]
    src = module.params["src"]
    content_type = module.params.get("content_type", "application/octet-stream")
    force = module.params.get("force", False)

    if not src:
        module.fail_json(msg="Parameter 'src' is required when uploading (state=present without 'dest').")

    if not os.path.isfile(src):
        module.fail_json(msg=f"Source file not found: {src}")

    existing = get_object_head(client, namespace_name, bucket_name, object_name)
    if existing and not force:
        module.exit_json(
            changed=False,
            resource=dict(
                namespace_name=namespace_name,
                bucket_name=bucket_name,
                object_name=object_name,
            ),
            msg="Object already exists. Use force=true to overwrite.",
        )
        return

    if module.check_mode:
        module.exit_json(changed=True)
        return

    with open(src, "rb") as f:
        call_with_retry(
            client.put_object,
            namespace_name,
            bucket_name,
            object_name,
            f,
            content_type=content_type,
        )

    module.exit_json(
        changed=True,
        resource=dict(
            namespace_name=namespace_name,
            bucket_name=bucket_name,
            object_name=object_name,
            content_type=content_type,
        ),
    )


def download_object(module, client):
    """Download an object from Object Storage to a local file."""
    namespace_name = module.params["namespace_name"]
    bucket_name = module.params["bucket_name"]
    object_name = module.params["object_name"]
    dest = module.params["dest"]
    force = module.params.get("force", False)

    if os.path.exists(dest) and not force:
        module.exit_json(
            changed=False,
            resource=dict(
                namespace_name=namespace_name,
                bucket_name=bucket_name,
                object_name=object_name,
                dest=dest,
            ),
            msg="Destination file already exists. Use force=true to overwrite.",
        )
        return

    existing = get_object_head(client, namespace_name, bucket_name, object_name)
    if not existing:
        module.fail_json(msg=f"Object '{object_name}' not found in bucket '{bucket_name}'.")

    if module.check_mode:
        module.exit_json(changed=True)
        return

    response = call_with_retry(
        client.get_object,
        namespace_name,
        bucket_name,
        object_name,
    )

    dest_dir = os.path.dirname(dest)
    if dest_dir and not os.path.isdir(dest_dir):
        os.makedirs(dest_dir, exist_ok=True)

    with open(dest, "wb") as f:
        for chunk in response.data.raw.stream(1024 * 1024):
            f.write(chunk)

    module.exit_json(
        changed=True,
        resource=dict(
            namespace_name=namespace_name,
            bucket_name=bucket_name,
            object_name=object_name,
            dest=dest,
        ),
    )


def delete_object(module, client):
    """Delete an object from Object Storage."""
    namespace_name = module.params["namespace_name"]
    bucket_name = module.params["bucket_name"]
    object_name = module.params["object_name"]

    existing = get_object_head(client, namespace_name, bucket_name, object_name)
    if not existing:
        module.exit_json(changed=False)
        return

    if module.check_mode:
        module.exit_json(changed=True)
        return

    call_with_retry(
        client.delete_object,
        namespace_name,
        bucket_name,
        object_name,
    )
    module.exit_json(changed=True)


def main():
    module_args = dict(
        namespace_name=dict(type="str", required=True),
        bucket_name=dict(type="str", required=True),
        object_name=dict(type="str", required=True),
        src=dict(type="path"),
        dest=dict(type="path"),
        content_type=dict(type="str", default="application/octet-stream"),
        force=dict(type="bool", default=False),
        state=dict(type="str", default="present", choices=["present", "absent"]),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        mutually_exclusive=[("src", "dest")],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, ObjectStorageClient)
    state = module.params["state"]

    if state == "absent":
        delete_object(module, client)
    elif module.params.get("dest"):
        download_object(module, client)
    else:
        upload_object(module, client)


if __name__ == "__main__":
    main()
