# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Analytics Instances."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_analytics_instance
short_description: Manage Analytics Instances in OCI
description:
    - Create, update, and delete Analytics Instances in Oracle Cloud Infrastructure.
    - This module uses the OCI Python SDK C(oci.analytics.AnalyticsClient).
version_added: "1.0.0"
author:
    - Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment to contain the analytics instance.
            - Required when creating a new instance.
        type: str
    analytics_instance_id:
        description:
            - The OCID of an existing analytics instance.
            - Required for update and delete operations.
        type: str
    name:
        description:
            - The name of the analytics instance.
            - Required when creating a new instance.
        type: str
    description:
        description:
            - A description of the analytics instance.
        type: str
    capacity:
        description:
            - The capacity of the analytics instance.
            - Dictionary with capacity_type and capacity_value.
        type: dict
    license_type:
        description:
            - The license type for the instance.
        type: str
        choices:
            - LICENSE_INCLUDED
            - BRING_YOUR_OWN_LICENSE
        default: LICENSE_INCLUDED
    feature_set:
        description:
            - The feature set of the analytics instance.
        type: str
        choices:
            - SELF_SERVICE_ANALYTICS
            - ENTERPRISE_ANALYTICS
        default: ENTERPRISE_ANALYTICS
    network_endpoint_details:
        description:
            - Network endpoint details for the instance.
        type: dict
    state:
        description:
            - The desired state of the analytics instance.
        type: str
        choices:
            - present
            - absent
        default: present
    wait:
        description:
            - Whether to wait for the resource to reach the desired state.
        type: bool
        default: true
    wait_timeout:
        description:
            - Maximum time in seconds to wait for the resource to reach the desired state.
        type: int
        default: 1200
extends_documentation_fragment:
    - stevefulme1.oci_cloud.oci_common
requirements:
    - "python >= 3.8"
    - "oci >= 2.90.0"
"""

EXAMPLES = r"""
- name: Create an Analytics instance
  stevefulme1.oci_cloud.oci_analytics_instance:
    compartment_id: "ocid1.compartment.oc1..example"
    name: "my-analytics"
    capacity:
      capacity_type: "OLPU_COUNT"
      capacity_value: 2
    license_type: LICENSE_INCLUDED
    feature_set: ENTERPRISE_ANALYTICS
    state: present

- name: Delete an Analytics instance
  stevefulme1.oci_cloud.oci_analytics_instance:
    analytics_instance_id: "ocid1.analyticsinstance.oc1..example"
    state: absent
"""

RETURN = r"""
analytics_instance:
    description: Details of the Analytics instance.
    returned: On success when state is present.
    type: dict
    sample:
        id: "ocid1.analyticsinstance.oc1..example"
        name: "my-analytics"
        lifecycle_state: "ACTIVE"
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from oci.analytics import AnalyticsClient
    from oci.analytics.models import (
        CreateAnalyticsInstanceDetails,
        UpdateAnalyticsInstanceDetails,
    )
    from oci.exceptions import ServiceError

    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False

from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_common import (
    OCI_COMMON_ARGS,
    DEAD_STATES,
    READY_STATES,
)
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_auth import create_service_client
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_wait import (
    call_with_retry,
    wait_for_resource,
)


def get_module_args():
    module_args = dict(
        compartment_id=dict(type="str"),
        analytics_instance_id=dict(type="str"),
        name=dict(type="str"),
        description=dict(type="str"),
        capacity=dict(type="dict"),
        license_type=dict(
            type="str",
            choices=["LICENSE_INCLUDED", "BRING_YOUR_OWN_LICENSE"],
            default="LICENSE_INCLUDED",
        ),
        feature_set=dict(
            type="str",
            choices=["SELF_SERVICE_ANALYTICS", "ENTERPRISE_ANALYTICS"],
            default="ENTERPRISE_ANALYTICS",
        ),
        network_endpoint_details=dict(type="dict"),
        state=dict(type="str", choices=["present", "absent"], default="present"),
    )
    module_args.update(OCI_COMMON_ARGS)
    return module_args


def to_dict(resource):
    if resource is None:
        return {}
    if hasattr(resource, "__dict__"):
        result = {}
        for key, value in resource.__dict__.items():
            if key.startswith("_"):
                continue
            if isinstance(value, list):
                result[key] = [to_dict(i) if hasattr(i, "__dict__") else i for i in value]
            elif hasattr(value, "__dict__") and not isinstance(value, (str, int, float, bool, dict)):
                result[key] = to_dict(value)
            else:
                result[key] = value
        return result
    return resource


def get_resource(client, resource_id):
    try:
        response = call_with_retry(client.get_analytics_instance, resource_id)
        return response.data
    except ServiceError as e:
        if e.status == 404:
            return None
        raise


def find_resource(client, compartment_id, name):
    if not compartment_id:
        return None
    try:
        response = call_with_retry(
            client.list_analytics_instances, compartment_id=compartment_id,
        )
        for item in response.data:
            if item.lifecycle_state in DEAD_STATES:
                continue
            if name and item.name == name:
                return item
    except ServiceError:
        pass
    return None


def create_resource(module, client):
    params = module.params
    create_details = CreateAnalyticsInstanceDetails(
        compartment_id=params["compartment_id"],
        name=params["name"],
        description=params.get("description"),
        capacity=params.get("capacity"),
        license_type=params.get("license_type"),
        feature_set=params.get("feature_set"),
        network_endpoint_details=params.get("network_endpoint_details"),
        freeform_tags=params.get("freeform_tags"),
        defined_tags=params.get("defined_tags"),
    )
    response = call_with_retry(client.create_analytics_instance, create_details)
    resource = response.data
    resource = wait_for_resource(
        module, client.get_analytics_instance, resource.id, target_states=READY_STATES,
    )
    return resource


def update_resource(module, client, existing):
    params = module.params
    update_details = UpdateAnalyticsInstanceDetails(
        description=params.get("description"),
        license_type=params.get("license_type"),
        freeform_tags=params.get("freeform_tags"),
        defined_tags=params.get("defined_tags"),
    )
    response = call_with_retry(
        client.update_analytics_instance, existing.id, update_details,
    )
    resource = response.data
    resource = wait_for_resource(
        module, client.get_analytics_instance, resource.id, target_states=READY_STATES,
    )
    return resource


def delete_resource(module, client, existing):
    call_with_retry(client.delete_analytics_instance, existing.id)
    wait_for_resource(
        module, client.get_analytics_instance, existing.id, target_states=DEAD_STATES,
    )


def needs_update(params, existing):
    updatable = ["description", "license_type"]
    for attr in updatable:
        desired = params.get(attr)
        if desired is None:
            continue
        current = getattr(existing, attr, None)
        if current != desired:
            return True
    if params.get("freeform_tags") is not None:
        if getattr(existing, "freeform_tags", None) != params["freeform_tags"]:
            return True
    if params.get("defined_tags") is not None:
        if getattr(existing, "defined_tags", None) != params["defined_tags"]:
            return True
    return False


def main():
    module = AnsibleModule(
        argument_spec=get_module_args(),
        supports_check_mode=True,
        required_if=[
            ("state", "present", ("compartment_id", "name"), True),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, AnalyticsClient)
    params = module.params
    state = params["state"]

    existing = None
    if params.get("analytics_instance_id"):
        existing = get_resource(client, params["analytics_instance_id"])
    elif params.get("compartment_id"):
        existing = find_resource(client, params["compartment_id"], params.get("name"))

    if state == "absent":
        if existing is None:
            module.exit_json(changed=False)
        if module.check_mode:
            module.exit_json(changed=True)
        delete_resource(module, client, existing)
        module.exit_json(changed=True)
        return

    if existing is None:
        for req in ("compartment_id", "name"):
            if not params.get(req):
                module.fail_json(msg=f"Parameter '{req}' is required to create an Analytics instance.")
        if module.check_mode:
            module.exit_json(changed=True)
        resource = create_resource(module, client)
        module.exit_json(changed=True, analytics_instance=to_dict(resource))
        return

    if needs_update(params, existing):
        if module.check_mode:
            module.exit_json(changed=True)
        resource = update_resource(module, client, existing)
        module.exit_json(changed=True, analytics_instance=to_dict(resource))
        return

    module.exit_json(changed=False, analytics_instance=to_dict(existing))


if __name__ == "__main__":
    main()
