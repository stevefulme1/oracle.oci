# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Marketplace Accepted Agreements."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_marketplace_accepted_agreement
short_description: Manage Marketplace Accepted Agreements in OCI
description:
    - Create, update, and delete Marketplace Accepted Agreements in Oracle Cloud Infrastructure.
    - This module uses the OCI Python SDK C(oci.marketplace.MarketplaceClient).
version_added: "2.0.0"
author:
    - Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment to contain the accepted agreement.
            - Required when creating a new accepted agreement.
        type: str
    accepted_agreement_id:
        description:
            - The OCID of an existing accepted agreement.
            - Required for update and delete operations.
        type: str
    listing_id:
        description:
            - The OCID of the marketplace listing.
            - Required when creating a new accepted agreement.
        type: str
    package_version:
        description:
            - The package version of the listing.
            - Required when creating a new accepted agreement.
        type: str
    agreement_id:
        description:
            - The OCID of the agreement.
            - Required when creating a new accepted agreement.
        type: str
    signature:
        description:
            - The signature of the agreement.
            - Required when creating a new accepted agreement.
        type: str
    display_name:
        description:
            - The display name of the accepted agreement.
        type: str
    state:
        description:
            - The desired state of the accepted agreement.
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
- name: Create a marketplace accepted agreement
  stevefulme1.oci_cloud.oci_marketplace_accepted_agreement:
    compartment_id: "ocid1.compartment.oc1..example"
    listing_id: "ocid1.listing.oc1..example"
    package_version: "1.0.0"
    agreement_id: "ocid1.agreement.oc1..example"
    signature: "agreement-signature"
    display_name: "my-accepted-agreement"
    state: present

- name: Delete a marketplace accepted agreement
  stevefulme1.oci_cloud.oci_marketplace_accepted_agreement:
    accepted_agreement_id: "ocid1.acceptedagreement.oc1..example"
    state: absent
"""

RETURN = r"""
accepted_agreement:
    description: Details of the accepted agreement.
    returned: On success when state is present.
    type: dict
    sample:
        id: "ocid1.acceptedagreement.oc1..example"
        display_name: "my-accepted-agreement"
        lifecycle_state: "ACTIVE"
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from oci.marketplace import MarketplaceClient
    from oci.marketplace.models import (
        CreateAcceptedAgreementDetails,
        UpdateAcceptedAgreementDetails,
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
        accepted_agreement_id=dict(type="str"),
        listing_id=dict(type="str"),
        package_version=dict(type="str"),
        agreement_id=dict(type="str"),
        signature=dict(type="str"),
        display_name=dict(type="str"),
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
        response = call_with_retry(client.get_accepted_agreement, resource_id)
        return response.data
    except ServiceError as e:
        if e.status == 404:
            return None
        raise


def find_resource(client, compartment_id, display_name):
    if not compartment_id:
        return None
    try:
        response = call_with_retry(
            client.list_accepted_agreements, compartment_id=compartment_id,
        )
        for item in response.data.items:
            if item.lifecycle_state in DEAD_STATES:
                continue
            if display_name and item.display_name == display_name:
                return item
    except ServiceError:
        pass
    return None


def create_resource(module, client):
    params = module.params
    create_details = CreateAcceptedAgreementDetails(
        compartment_id=params["compartment_id"],
        listing_id=params["listing_id"],
        package_version=params["package_version"],
        agreement_id=params["agreement_id"],
        signature=params["signature"],
        display_name=params.get("display_name"),
        freeform_tags=params.get("freeform_tags"),
        defined_tags=params.get("defined_tags"),
    )
    response = call_with_retry(client.create_accepted_agreement, create_details)
    resource = response.data
    resource = wait_for_resource(
        module, client.get_accepted_agreement, resource.id, target_states=READY_STATES,
    )
    return resource


def update_resource(module, client, existing):
    params = module.params
    update_details = UpdateAcceptedAgreementDetails(
        display_name=params.get("display_name"),
        freeform_tags=params.get("freeform_tags"),
        defined_tags=params.get("defined_tags"),
    )
    response = call_with_retry(client.update_accepted_agreement, existing.id, update_details)
    resource = response.data
    resource = wait_for_resource(
        module, client.get_accepted_agreement, resource.id, target_states=READY_STATES,
    )
    return resource


def delete_resource(module, client, existing):
    call_with_retry(client.delete_accepted_agreement, existing.id)
    wait_for_resource(
        module, client.get_accepted_agreement, existing.id, target_states=DEAD_STATES,
    )


def needs_update(params, existing):
    updatable = ["display_name"]
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
            ("state", "present", ("compartment_id", "listing_id", "package_version", "agreement_id", "signature"),
             True),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, MarketplaceClient)
    params = module.params
    state = params["state"]

    existing = None
    if params.get("accepted_agreement_id"):
        existing = get_resource(client, params["accepted_agreement_id"])
    elif params.get("compartment_id"):
        existing = find_resource(client, params["compartment_id"], params.get("display_name"))

    if state == "absent":
        if existing is None:
            module.exit_json(changed=False)
        if module.check_mode:
            module.exit_json(changed=True)
        delete_resource(module, client, existing)
        module.exit_json(changed=True)
        return

    if existing is None:
        for req in ("compartment_id", "listing_id", "package_version", "agreement_id", "signature"):
            if not params.get(req):
                module.fail_json(msg=f"Parameter '{req}' is required to create an accepted agreement.")
        if module.check_mode:
            module.exit_json(changed=True)
        resource = create_resource(module, client)
        module.exit_json(changed=True, accepted_agreement=to_dict(resource))
        return

    if needs_update(params, existing):
        if module.check_mode:
            module.exit_json(changed=True)
        resource = update_resource(module, client, existing)
        module.exit_json(changed=True, accepted_agreement=to_dict(resource))
        return

    module.exit_json(changed=False, accepted_agreement=to_dict(existing))


if __name__ == "__main__":
    main()
