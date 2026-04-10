#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI custom images."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_image
short_description: Manage OCI custom images
description:
  - Create, update, and delete custom images in Oracle Cloud Infrastructure.
  - Images can be created from an existing compute instance.
  - Uses the OCI Compute service via C(oci.core.ComputeClient).
version_added: "1.0.0"
author:
  - Oracle (@oracle)
options:
  compartment_id:
    description:
      - The OCID of the compartment to create the image in.
      - Required when creating a new image.
    type: str
  instance_id:
    description:
      - The OCID of the instance to create the image from.
      - Required when creating a new image from an instance.
    type: str
  display_name:
    description:
      - A user-friendly name for the image. Does not have to be unique.
    type: str
  image_id:
    description:
      - The OCID of the image. Required for update and delete operations.
    type: str
  state:
    description:
      - The desired state of the image.
    type: str
    choices: [present, absent]
    default: present
extends_documentation_fragment:
  - oracle.oci.oci_common
"""

EXAMPLES = r"""
- name: Create a custom image from an instance
  oracle.oci.oci_image:
    compartment_id: "ocid1.compartment.oc1..example"
    instance_id: "ocid1.instance.oc1.phx.example"
    display_name: "my-custom-image"
    state: present

- name: Update image display name
  oracle.oci.oci_image:
    image_id: "ocid1.image.oc1.phx.example"
    display_name: "renamed-image"
    state: present

- name: Delete a custom image
  oracle.oci.oci_image:
    image_id: "ocid1.image.oc1.phx.example"
    state: absent
"""

RETURN = r"""
resource:
  description: The image details.
  returned: on success
  type: dict
  sample:
    id: "ocid1.image.oc1.phx.example"
    display_name: "my-custom-image"
    lifecycle_state: "AVAILABLE"
    compartment_id: "ocid1.compartment.oc1..example"
    operating_system: "Oracle Linux"
    size_in_mbs: 47694
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.oracle.oci.plugins.module_utils.oci_common import (
    OCI_COMMON_ARGS,
    LIFECYCLE_AVAILABLE,
    LIFECYCLE_DELETED,
    LIFECYCLE_FAILED,
)
from ansible_collections.oracle.oci.plugins.module_utils.oci_resource import OciResourceBase
from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import (
    call_with_retry,
    wait_for_resource,
)

try:
    import oci
    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False


class OciImage(OciResourceBase):
    """Manage OCI custom images."""

    def __init__(self, module):
        self.client_class = oci.core.ComputeClient
        super().__init__(module)

    def get_resource(self):
        image_id = self.module.params.get("image_id")
        if not image_id:
            return None
        try:
            response = self.client.get_image(image_id)
            resource = response.data
            if resource.lifecycle_state == LIFECYCLE_DELETED:
                return None
            return resource
        except oci.exceptions.ServiceError as e:
            if e.status == 404:
                return None
            raise

    def create_resource(self):
        params = self.module.params
        kwargs = dict(
            compartment_id=params["compartment_id"],
            instance_id=params["instance_id"],
        )

        if params.get("display_name"):
            kwargs["display_name"] = params["display_name"]

        freeform_tags, defined_tags = self.get_tags()
        if freeform_tags:
            kwargs["freeform_tags"] = freeform_tags
        if defined_tags:
            kwargs["defined_tags"] = defined_tags

        create_details = oci.core.models.CreateImageDetails(**kwargs)
        response = call_with_retry(self.client.create_image, create_details)
        image = response.data

        if self.module.params.get("wait", True):
            image = wait_for_resource(
                self.module,
                self.client.get_image,
                image.id,
                target_states={LIFECYCLE_AVAILABLE},
                failure_states={LIFECYCLE_FAILED, LIFECYCLE_DELETED},
            )
        return image

    def update_resource(self, resource):
        params = self.module.params
        kwargs = {}

        if params.get("display_name"):
            kwargs["display_name"] = params["display_name"]

        freeform_tags, defined_tags = self.get_tags()
        if freeform_tags is not None:
            kwargs["freeform_tags"] = freeform_tags
        if defined_tags is not None:
            kwargs["defined_tags"] = defined_tags

        update_details = oci.core.models.UpdateImageDetails(**kwargs)
        response = call_with_retry(
            self.client.update_image, resource.id, update_details,
        )
        return response.data

    def delete_resource(self, resource):
        call_with_retry(self.client.delete_image, resource.id)
        if self.module.params.get("wait", True):
            wait_for_resource(
                self.module,
                self.client.get_image,
                resource.id,
                target_states={LIFECYCLE_DELETED},
            )

    def _updatable_attributes(self):
        return ["display_name"]


def main():
    module_args = dict(
        compartment_id=dict(type="str"),
        instance_id=dict(type="str"),
        display_name=dict(type="str"),
        image_id=dict(type="str"),
        state=dict(type="str", default="present", choices=["present", "absent"]),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            ("state", "present", ("compartment_id", "instance_id"), True),
            ("state", "absent", ("image_id",)),
        ],
    )

    oci_image = OciImage(module)
    oci_image.run()


if __name__ == "__main__":
    main()
