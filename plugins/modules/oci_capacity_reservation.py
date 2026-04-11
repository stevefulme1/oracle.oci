# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Compute Capacity Reservations."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_capacity_reservation
short_description: Manage OCI Compute Capacity Reservations
description:
    - Create, update, and delete compute capacity reservations in Oracle Cloud
      Infrastructure.
    - Uses the ComputeClient from the OCI Python SDK.
version_added: "1.0.0"
author: Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment to contain the capacity reservation.
            - Required when creating a new reservation.
        type: str
    capacity_reservation_id:
        description:
            - The OCID of the capacity reservation.
            - Required for update and delete operations.
        type: str
    availability_domain:
        description:
            - The availability domain for the capacity reservation.
            - Required when creating a new reservation.
        type: str
    display_name:
        description:
            - A user-friendly name for the capacity reservation.
        type: str
    instance_reservation_configs:
        description:
            - The capacity configurations for the reservation.
        type: list
        elements: dict
        suboptions:
            fault_domain:
                description:
                    - The fault domain for this reservation config.
                type: str
            instance_shape:
                description:
                    - The shape for the reserved instances.
                type: str
                required: true
            instance_shape_config:
                description:
                    - The shape configuration for the reserved instances.
                type: dict
            reserved_count:
                description:
                    - The total number of instances to reserve.
                type: int
                required: true
    state:
        description:
            - The desired state of the capacity reservation.
        type: str
        default: present
        choices: [present, absent]
extends_documentation_fragment:
    - oracle.oci.oci_common
"""

EXAMPLES = r"""
- name: Create a capacity reservation
  oracle.oci.oci_capacity_reservation:
    compartment_id: "ocid1.compartment.oc1..example"
    availability_domain: "Uocm:PHX-AD-1"
    display_name: "my-capacity-reservation"
    instance_reservation_configs:
      - instance_shape: "VM.Standard2.1"
        reserved_count: 5
    state: present

- name: Update a capacity reservation
  oracle.oci.oci_capacity_reservation:
    capacity_reservation_id: "ocid1.capacityreservation.oc1..example"
    display_name: "renamed-reservation"
    state: present

- name: Delete a capacity reservation
  oracle.oci.oci_capacity_reservation:
    capacity_reservation_id: "ocid1.capacityreservation.oc1..example"
    state: absent
"""

RETURN = r"""
resource:
    description: Details of the capacity reservation.
    returned: on success
    type: dict
    sample:
        id: "ocid1.capacityreservation.oc1..example"
        display_name: "my-capacity-reservation"
        lifecycle_state: "ACTIVE"
        availability_domain: "Uocm:PHX-AD-1"
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.oracle.oci.plugins.module_utils.oci_common import (
    OCI_COMMON_ARGS,
    DEAD_STATES,
    READY_STATES,
)
from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import (
    call_with_retry,
    wait_for_resource,
)
from ansible_collections.oracle.oci.plugins.module_utils.oci_resource import OciResourceBase

try:
    import oci
    from oci.core import ComputeClient
    from oci.core.models import (
        CreateComputeCapacityReservationDetails,
        UpdateComputeCapacityReservationDetails,
    )
    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False


class OciCapacityReservation(OciResourceBase):
    """Manage OCI Compute Capacity Reservations."""

    client_class = ComputeClient if HAS_OCI_SDK else None

    def get_resource(self):
        reservation_id = self.module.params.get("capacity_reservation_id")
        if not reservation_id:
            return None
        try:
            return call_with_retry(
                self.client.get_compute_capacity_reservation, reservation_id
            ).data
        except oci.exceptions.ServiceError as e:
            if e.status == 404:
                return None
            raise

    def create_resource(self):
        freeform_tags, defined_tags = self.get_tags()
        details = CreateComputeCapacityReservationDetails(
            compartment_id=self.module.params["compartment_id"],
            availability_domain=self.module.params["availability_domain"],
            display_name=self.module.params.get("display_name"),
            instance_reservation_configs=self.module.params.get(
                "instance_reservation_configs"
            ),
            freeform_tags=freeform_tags,
            defined_tags=defined_tags,
        )
        response = call_with_retry(
            self.client.create_compute_capacity_reservation, details
        )
        return wait_for_resource(
            self.module,
            self.client.get_compute_capacity_reservation,
            response.data.id,
            READY_STATES,
        )

    def update_resource(self, resource):
        freeform_tags, defined_tags = self.get_tags()
        details = UpdateComputeCapacityReservationDetails(
            display_name=self.module.params.get("display_name") or resource.display_name,
            instance_reservation_configs=(
                self.module.params.get("instance_reservation_configs")
            ),
            freeform_tags=freeform_tags if freeform_tags is not None else resource.freeform_tags,
            defined_tags=defined_tags if defined_tags is not None else resource.defined_tags,
        )
        call_with_retry(
            self.client.update_compute_capacity_reservation, resource.id, details
        )
        return wait_for_resource(
            self.module,
            self.client.get_compute_capacity_reservation,
            resource.id,
            READY_STATES,
        )

    def delete_resource(self, resource):
        call_with_retry(
            self.client.delete_compute_capacity_reservation, resource.id
        )
        if self.module.params.get("wait", True):
            wait_for_resource(
                self.module,
                self.client.get_compute_capacity_reservation,
                resource.id,
                DEAD_STATES | {"TERMINATED", "DELETED"},
            )

    def _updatable_attributes(self):
        return ["display_name", "instance_reservation_configs"]


def main():
    module_args = dict(
        compartment_id=dict(type="str"),
        capacity_reservation_id=dict(type="str"),
        availability_domain=dict(type="str"),
        display_name=dict(type="str"),
        instance_reservation_configs=dict(type="list", elements="dict"),
        state=dict(type="str", default="present", choices=["present", "absent"]),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            ("state", "present", ("compartment_id", "availability_domain"), True),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    resource_helper = OciCapacityReservation(module)
    resource_helper.run()


if __name__ == "__main__":
    main()
