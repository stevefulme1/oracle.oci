# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for retrieving OCI compute instance facts."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_instance_facts
short_description: Retrieve facts about OCI compute instances
description:
  - Retrieve details about one or more compute instances in Oracle Cloud Infrastructure.
  - Use I(instance_id) to get a single instance, or I(compartment_id) to list instances.
  - This is a read-only module that does not modify any resources.
  - Uses the OCI Compute service via C(oci.core.ComputeClient).
version_added: "1.0.0"
author:
  - Oracle (@oracle)
options:
  compartment_id:
    description:
      - The OCID of the compartment to list instances from.
      - Required when listing instances.
    type: str
  instance_id:
    description:
      - The OCID of a specific instance to retrieve.
      - When specified, returns a single instance instead of a list.
    type: str
  availability_domain:
    description:
      - Filter instances by availability domain.
      - Only used when listing instances with I(compartment_id).
    type: str
  display_name:
    description:
      - Filter instances by display name.
      - Only used when listing instances with I(compartment_id).
    type: str
  lifecycle_state:
    description:
      - Filter instances by lifecycle state.
      - Only used when listing instances with I(compartment_id).
    type: str
    choices:
      - MOVING
      - PROVISIONING
      - RUNNING
      - STARTING
      - STOPPING
      - STOPPED
      - CREATING_IMAGE
      - TERMINATING
      - TERMINATED
extends_documentation_fragment:
  - stevefulme1.oci_cloud.oci_common
"""

EXAMPLES = r"""
- name: List all instances in a compartment
  stevefulme1.oci_cloud.oci_instance_facts:
    compartment_id: "ocid1.compartment.oc1..example"
  register: result

- name: Get a specific instance by ID
  stevefulme1.oci_cloud.oci_instance_facts:
    instance_id: "ocid1.instance.oc1.phx.example"
  register: result

- name: List running instances in a specific availability domain
  stevefulme1.oci_cloud.oci_instance_facts:
    compartment_id: "ocid1.compartment.oc1..example"
    availability_domain: "Uocm:PHX-AD-1"
    lifecycle_state: "RUNNING"
  register: result

- name: List instances filtered by display name
  stevefulme1.oci_cloud.oci_instance_facts:
    compartment_id: "ocid1.compartment.oc1..example"
    display_name: "my-instance"
  register: result
"""

RETURN = r"""
instances:
  description: List of instance details.
  returned: on success
  type: list
  elements: dict
  sample:
    - id: "ocid1.instance.oc1.phx.example"
      display_name: "my-instance"
      lifecycle_state: "RUNNING"
      shape: "VM.Standard.E4.Flex"
      availability_domain: "Uocm:PHX-AD-1"
      compartment_id: "ocid1.compartment.oc1..example"
      region: "us-phoenix-1"
      time_created: "2024-01-15T10:30:00.000Z"
      image_id: "ocid1.image.oc1.phx.example"
      metadata: {}
      shape_config:
        ocpus: 2.0
        memory_in_gbs: 32.0
      freeform_tags: {}
      defined_tags: {}
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_common import (
    OCI_COMMON_ARGS,
)
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_auth import create_service_client

try:
    import oci
    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False


def to_dict(resource):
    """Convert an OCI SDK resource object to a serializable dict."""
    if resource is None:
        return {}
    if hasattr(resource, "__dict__"):
        result = {}
        for key, value in resource.__dict__.items():
            if key.startswith("_"):
                continue
            if hasattr(value, "__dict__") and not isinstance(value, (str, int, float, bool, list, dict)):
                result[key] = to_dict(value)
            elif isinstance(value, list):
                result[key] = [
                    to_dict(item) if hasattr(item, "__dict__") else item
                    for item in value
                ]
            else:
                result[key] = value
        return result
    return resource


def list_instances(client, module):
    """List instances in a compartment with optional filters."""
    compartment_id = module.params["compartment_id"]
    kwargs = dict(compartment_id=compartment_id)

    if module.params.get("availability_domain"):
        kwargs["availability_domain"] = module.params["availability_domain"]
    if module.params.get("display_name"):
        kwargs["display_name"] = module.params["display_name"]
    if module.params.get("lifecycle_state"):
        kwargs["lifecycle_state"] = module.params["lifecycle_state"]

    instances = []
    response = client.list_instances(**kwargs)
    instances.extend(response.data)

    while response.has_next_page:
        response = client.list_instances(**kwargs, page=response.next_page)
        instances.extend(response.data)

    return [to_dict(inst) for inst in instances]


def get_instance(client, module):
    """Get a single instance by ID."""
    instance_id = module.params["instance_id"]
    try:
        response = client.get_instance(instance_id)
        return [to_dict(response.data)]
    except oci.exceptions.ServiceError as e:
        if e.status == 404:
            return []
        raise


def main():
    module_args = dict(
        compartment_id=dict(type="str"),
        instance_id=dict(type="str"),
        availability_domain=dict(type="str"),
        display_name=dict(type="str"),
        lifecycle_state=dict(
            type="str",
            choices=[
                "MOVING",
                "PROVISIONING",
                "RUNNING",
                "STARTING",
                "STOPPING",
                "STOPPED",
                "CREATING_IMAGE",
                "TERMINATING",
                "TERMINATED",
            ],
        ),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_one_of=[
            ("compartment_id", "instance_id"),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, oci.core.ComputeClient)

    if module.params.get("instance_id"):
        instances = get_instance(client, module)
    else:
        instances = list_instances(client, module)

    module.exit_json(changed=False, instances=instances)


if __name__ == "__main__":
    main()
