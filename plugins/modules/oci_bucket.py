#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Object Storage Buckets."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_bucket
short_description: Manage OCI Object Storage Buckets
description:
    - Create, update, and delete Object Storage buckets in Oracle Cloud Infrastructure.
    - Uses the ObjectStorageClient from the OCI Python SDK.
version_added: "1.0.0"
author: Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment to contain the bucket.
            - Required when creating a new bucket.
        type: str
    namespace_name:
        description:
            - The Object Storage namespace.
            - Required for all operations.
        type: str
        required: true
    name:
        description:
            - The name of the bucket.
            - Required for all operations.
        type: str
        required: true
    public_access_type:
        description:
            - The type of public access enabled on the bucket.
        type: str
        default: NoPublicAccess
        choices: [NoPublicAccess, ObjectRead, ObjectReadWithoutList]
    storage_tier:
        description:
            - The storage tier type for the bucket.
        type: str
        default: Standard
        choices: [Standard, Archive]
    versioning:
        description:
            - Whether versioning is enabled on the bucket.
        type: str
        choices: [Enabled, Disabled]
    state:
        description:
            - The desired state of the bucket.
        type: str
        default: present
        choices: [present, absent]
extends_documentation_fragment:
    - oracle.oci.oci_common
"""

EXAMPLES = r"""
- name: Create a bucket
  oracle.oci.oci_bucket:
    compartment_id: "ocid1.compartment.oc1..example"
    namespace_name: "mynamespace"
    name: "my-bucket"
    public_access_type: NoPublicAccess
    storage_tier: Standard
    state: present

- name: Enable versioning on a bucket
  oracle.oci.oci_bucket:
    namespace_name: "mynamespace"
    name: "my-bucket"
    versioning: Enabled
    state: present

- name: Delete a bucket
  oracle.oci.oci_bucket:
    namespace_name: "mynamespace"
    name: "my-bucket"
    state: absent
"""

RETURN = r"""
resource:
    description: Details of the bucket.
    returned: on success
    type: dict
    sample:
        name: "my-bucket"
        namespace: "mynamespace"
        compartment_id: "ocid1.compartment.oc1..example"
        public_access_type: "NoPublicAccess"
        storage_tier: "Standard"
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.oracle.oci.plugins.module_utils.oci_common import OCI_COMMON_ARGS
from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import call_with_retry
from ansible_collections.oracle.oci.plugins.module_utils.oci_resource import OciResourceBase

try:
    import oci
    from oci.object_storage import ObjectStorageClient
    from oci.object_storage.models import (
        CreateBucketDetails,
        UpdateBucketDetails,
    )
    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False


class OciBucket(OciResourceBase):
    """Manage OCI Object Storage Buckets."""

    client_class = ObjectStorageClient if HAS_OCI_SDK else None

    def get_resource(self):
        namespace_name = self.module.params["namespace_name"]
        name = self.module.params["name"]
        try:
            return call_with_retry(
                self.client.get_bucket,
                namespace_name,
                name,
            ).data
        except oci.exceptions.ServiceError as e:
            if e.status == 404:
                return None
            raise

    def create_resource(self):
        freeform_tags, defined_tags = self.get_tags()
        details = CreateBucketDetails(
            compartment_id=self.module.params["compartment_id"],
            name=self.module.params["name"],
            public_access_type=self.module.params.get("public_access_type", "NoPublicAccess"),
            storage_tier=self.module.params.get("storage_tier", "Standard"),
            versioning=self.module.params.get("versioning"),
            freeform_tags=freeform_tags,
            defined_tags=defined_tags,
        )
        response = call_with_retry(
            self.client.create_bucket,
            self.module.params["namespace_name"],
            details,
        )
        return response.data

    def update_resource(self, resource):
        freeform_tags, defined_tags = self.get_tags()
        details = UpdateBucketDetails(
            public_access_type=self.module.params.get("public_access_type") or resource.public_access_type,
            versioning=self.module.params.get("versioning"),
            freeform_tags=freeform_tags if freeform_tags is not None else resource.freeform_tags,
            defined_tags=defined_tags if defined_tags is not None else resource.defined_tags,
        )
        response = call_with_retry(
            self.client.update_bucket,
            self.module.params["namespace_name"],
            self.module.params["name"],
            details,
        )
        return response.data

    def delete_resource(self, resource):
        call_with_retry(
            self.client.delete_bucket,
            self.module.params["namespace_name"],
            self.module.params["name"],
        )

    def _updatable_attributes(self):
        return ["public_access_type", "versioning"]


def main():
    module_args = dict(
        compartment_id=dict(type="str"),
        namespace_name=dict(type="str", required=True),
        name=dict(type="str", required=True),
        public_access_type=dict(
            type="str",
            default="NoPublicAccess",
            choices=["NoPublicAccess", "ObjectRead", "ObjectReadWithoutList"],
        ),
        storage_tier=dict(
            type="str",
            default="Standard",
            choices=["Standard", "Archive"],
        ),
        versioning=dict(type="str", choices=["Enabled", "Disabled"]),
        state=dict(type="str", default="present", choices=["present", "absent"]),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            ("state", "present", ("compartment_id",), True),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    resource_helper = OciBucket(module)
    resource_helper.run()


if __name__ == "__main__":
    main()
