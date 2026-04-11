# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI GoldenGate Deployments."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_goldengate_deployment
short_description: Manage GoldenGate Deployments in OCI
description:
    - Create, update, and delete GoldenGate Deployments in Oracle Cloud Infrastructure.
    - Oracle Cloud Infrastructure GoldenGate is a real-time data integration and
      replication service.
    - This module uses the OCI Python SDK C(oci.golden_gate.GoldenGateClient).
version_added: "1.0.0"
author:
    - Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment to contain the GoldenGate deployment.
            - Required when creating a new deployment.
        type: str
    deployment_id:
        description:
            - The OCID of an existing GoldenGate deployment.
            - Required for update and delete operations.
        type: str
    display_name:
        description:
            - The user-friendly name for the GoldenGate deployment.
            - Required when creating a new deployment.
        type: str
    license_model:
        description:
            - The Oracle license model for the deployment.
            - Required when creating a new deployment.
        type: str
        choices:
            - LICENSE_INCLUDED
            - BRING_YOUR_OWN_LICENSE
    subnet_id:
        description:
            - The OCID of the subnet for the deployment.
            - Required when creating a new deployment.
        type: str
    cpu_core_count:
        description:
            - The Minimum number of OCPUs to be made available for this deployment.
            - Required when creating a new deployment.
        type: int
    is_auto_scaling_enabled:
        description:
            - Whether auto scaling is enabled for the deployment's CPU core count.
        type: bool
        default: false
    deployment_type:
        description:
            - The type of the GoldenGate deployment.
            - Required when creating a new deployment.
        type: str
        choices:
            - OGG
            - DATABASE_ORACLE
            - BIGDATA
            - DATABASE_MICROSOFT_SQLSERVER
            - DATABASE_MYSQL
            - DATABASE_POSTGRESQL
    ogg_data:
        description:
            - OGG deployment data. Contains admin credentials and other OGG-specific settings.
        type: dict
        suboptions:
            admin_username:
                description:
                    - The GoldenGate deployment console username.
                type: str
            admin_password:
                description:
                    - The password for the GoldenGate deployment console.
                type: str
            deployment_name:
                description:
                    - The name given to the GoldenGate service deployment.
                type: str
            certificate:
                description:
                    - A PEM-encoded SSL certificate.
                type: str
    state:
        description:
            - The desired state of the GoldenGate deployment.
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
    - oracle.oci.oci_common
requirements:
    - "python >= 3.8"
    - "oci >= 2.90.0"
"""

EXAMPLES = r"""
- name: Create a GoldenGate deployment
  oracle.oci.oci_goldengate_deployment:
    compartment_id: "ocid1.compartment.oc1..example"
    display_name: "My GoldenGate Deployment"
    license_model: LICENSE_INCLUDED
    subnet_id: "ocid1.subnet.oc1..example"
    cpu_core_count: 1
    is_auto_scaling_enabled: false
    deployment_type: OGG
    ogg_data:
      admin_username: "oggadmin"
      admin_password: "ExamplePassword123#"
      deployment_name: "myogg"
    state: present

- name: Update a GoldenGate deployment
  oracle.oci.oci_goldengate_deployment:
    deployment_id: "ocid1.goldengatedeployment.oc1..example"
    display_name: "Updated GoldenGate Deployment"
    cpu_core_count: 2
    is_auto_scaling_enabled: true
    state: present

- name: Delete a GoldenGate deployment
  oracle.oci.oci_goldengate_deployment:
    deployment_id: "ocid1.goldengatedeployment.oc1..example"
    state: absent
"""

RETURN = r"""
goldengate_deployment:
    description: Details of the GoldenGate deployment.
    returned: On success when state is present.
    type: dict
    sample:
        id: "ocid1.goldengatedeployment.oc1..example"
        compartment_id: "ocid1.compartment.oc1..example"
        display_name: "My GoldenGate Deployment"
        lifecycle_state: "ACTIVE"
        license_model: "LICENSE_INCLUDED"
        cpu_core_count: 1
        is_auto_scaling_enabled: false
        deployment_type: "OGG"
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from oci.golden_gate import GoldenGateClient
    from oci.golden_gate.models import (
        CreateDeploymentDetails,
        UpdateDeploymentDetails,
        CreateOggDeploymentDetails,
        UpdateOggDeploymentDetails,
    )
    from oci.exceptions import ServiceError

    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False

from ansible_collections.oracle.oci.plugins.module_utils.oci_common import (
    OCI_COMMON_ARGS,
    DEAD_STATES,
    READY_STATES,
)
from ansible_collections.oracle.oci.plugins.module_utils.oci_auth import create_service_client
from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import (
    call_with_retry,
    wait_for_resource,
)


def get_module_args():
    """Build argument spec for this module."""
    module_args = dict(
        compartment_id=dict(type="str"),
        deployment_id=dict(type="str"),
        display_name=dict(type="str"),
        license_model=dict(
            type="str",
            choices=["LICENSE_INCLUDED", "BRING_YOUR_OWN_LICENSE"],
        ),
        subnet_id=dict(type="str"),
        cpu_core_count=dict(type="int"),
        is_auto_scaling_enabled=dict(type="bool", default=False),
        deployment_type=dict(
            type="str",
            choices=[
                "OGG",
                "DATABASE_ORACLE",
                "BIGDATA",
                "DATABASE_MICROSOFT_SQLSERVER",
                "DATABASE_MYSQL",
                "DATABASE_POSTGRESQL",
            ],
        ),
        ogg_data=dict(type="dict", no_log=True),
        state=dict(type="str", choices=["present", "absent"], default="present"),
    )
    module_args.update(OCI_COMMON_ARGS)
    return module_args


def to_dict(resource):
    """Convert OCI SDK object to a serializable dict."""
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


def get_deployment(client, deployment_id):
    """Get an existing GoldenGate deployment by OCID."""
    try:
        response = call_with_retry(client.get_deployment, deployment_id)
        return response.data
    except ServiceError as e:
        if e.status == 404:
            return None
        raise


def find_deployment(client, compartment_id, display_name):
    """Find a GoldenGate deployment by compartment and display_name."""
    if not compartment_id:
        return None
    try:
        response = call_with_retry(
            client.list_deployments,
            compartment_id=compartment_id,
        )
        for dep in response.data.items:
            if dep.lifecycle_state in DEAD_STATES:
                continue
            if display_name and dep.display_name == display_name:
                return get_deployment(client, dep.id)
    except ServiceError:
        pass
    return None


def build_ogg_data(ogg_params, for_update=False):
    """Build OGG deployment details from params."""
    if not ogg_params:
        return None
    if for_update:
        return UpdateOggDeploymentDetails(
            admin_username=ogg_params.get("admin_username"),
            admin_password=ogg_params.get("admin_password"),
            certificate=ogg_params.get("certificate"),
        )
    return CreateOggDeploymentDetails(
        admin_username=ogg_params.get("admin_username"),
        admin_password=ogg_params.get("admin_password"),
        deployment_name=ogg_params.get("deployment_name"),
        certificate=ogg_params.get("certificate"),
    )


def create_deployment(module, client):
    """Create a new GoldenGate deployment."""
    params = module.params
    create_details = CreateDeploymentDetails(
        compartment_id=params["compartment_id"],
        display_name=params["display_name"],
        license_model=params["license_model"],
        subnet_id=params["subnet_id"],
        cpu_core_count=params["cpu_core_count"],
        is_auto_scaling_enabled=params.get("is_auto_scaling_enabled", False),
        deployment_type=params["deployment_type"],
        ogg_data=build_ogg_data(params.get("ogg_data")),
        freeform_tags=params.get("freeform_tags"),
        defined_tags=params.get("defined_tags"),
    )

    response = call_with_retry(client.create_deployment, create_details)
    resource = response.data

    resource = wait_for_resource(
        module,
        client.get_deployment,
        resource.id,
        target_states=READY_STATES,
    )
    return resource


def update_deployment(module, client, existing):
    """Update an existing GoldenGate deployment."""
    params = module.params
    update_details = UpdateDeploymentDetails(
        display_name=params.get("display_name"),
        license_model=params.get("license_model"),
        cpu_core_count=params.get("cpu_core_count"),
        is_auto_scaling_enabled=params.get("is_auto_scaling_enabled"),
        ogg_data=build_ogg_data(params.get("ogg_data"), for_update=True),
        freeform_tags=params.get("freeform_tags"),
        defined_tags=params.get("defined_tags"),
    )

    response = call_with_retry(
        client.update_deployment,
        existing.id,
        update_details,
    )
    resource = response.data

    resource = wait_for_resource(
        module,
        client.get_deployment,
        existing.id,
        target_states=READY_STATES,
    )
    return resource


def delete_deployment(module, client, existing):
    """Delete a GoldenGate deployment."""
    call_with_retry(client.delete_deployment, existing.id)
    wait_for_resource(
        module,
        client.get_deployment,
        existing.id,
        target_states=DEAD_STATES,
    )


def needs_update(params, existing):
    """Determine if the existing resource differs from desired state."""
    updatable = [
        "display_name",
        "license_model",
        "cpu_core_count",
        "is_auto_scaling_enabled",
    ]
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
    """Module entry point."""
    module = AnsibleModule(
        argument_spec=get_module_args(),
        supports_check_mode=True,
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, GoldenGateClient)
    params = module.params
    state = params["state"]

    # Find existing resource
    existing = None
    if params.get("deployment_id"):
        existing = get_deployment(client, params["deployment_id"])
    elif params.get("compartment_id"):
        existing = find_deployment(
            client,
            params["compartment_id"],
            params.get("display_name"),
        )

    if state == "absent":
        if existing is None:
            module.exit_json(changed=False)
        if module.check_mode:
            module.exit_json(changed=True)
        delete_deployment(module, client, existing)
        module.exit_json(changed=True)
        return

    # state == present
    if existing is None:
        for req in ("compartment_id", "display_name", "license_model",
                    "subnet_id", "cpu_core_count", "deployment_type"):
            if not params.get(req):
                module.fail_json(msg=f"Parameter '{req}' is required to create a GoldenGate deployment.")
        if module.check_mode:
            module.exit_json(changed=True)
        resource = create_deployment(module, client)
        module.exit_json(changed=True, goldengate_deployment=to_dict(resource))
        return

    if needs_update(params, existing):
        if module.check_mode:
            module.exit_json(changed=True)
        resource = update_deployment(module, client, existing)
        module.exit_json(changed=True, goldengate_deployment=to_dict(resource))
        return

    module.exit_json(changed=False, goldengate_deployment=to_dict(existing))


if __name__ == "__main__":
    main()
