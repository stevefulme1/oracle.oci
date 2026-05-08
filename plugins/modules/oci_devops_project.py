# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI DevOps Projects."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_devops_project
short_description: Manage DevOps Projects in OCI
description:
    - Create, update, and delete DevOps Projects in Oracle Cloud Infrastructure.
    - This module uses the OCI Python SDK C(oci.devops.DevopsClient).
version_added: "1.0.0"
author:
    - Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment to contain the DevOps project.
            - Required when creating a new project.
        type: str
    project_id:
        description:
            - The OCID of an existing DevOps project.
            - Required for update and delete operations.
        type: str
    name:
        description:
            - The name of the DevOps project.
            - Required when creating a new project.
        type: str
    description:
        description:
            - A description of the DevOps project.
        type: str
    notification_config:
        description:
            - Notification configuration for the project.
            - Contains a topic_id for the ONS topic.
        type: dict
    state:
        description:
            - The desired state of the DevOps project.
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
- name: Create a DevOps project
  stevefulme1.oci_cloud.oci_devops_project:
    compartment_id: "ocid1.compartment.oc1..example"
    name: "my-devops-project"
    description: "My DevOps project"
    notification_config:
      topic_id: "ocid1.onstopic.oc1..example"
    state: present

- name: Update a DevOps project
  stevefulme1.oci_cloud.oci_devops_project:
    project_id: "ocid1.devopsproject.oc1..example"
    description: "Updated description"
    state: present

- name: Delete a DevOps project
  stevefulme1.oci_cloud.oci_devops_project:
    project_id: "ocid1.devopsproject.oc1..example"
    state: absent
"""

RETURN = r"""
devops_project:
    description: Details of the DevOps project.
    returned: On success when state is present.
    type: dict
    sample:
        id: "ocid1.devopsproject.oc1..example"
        compartment_id: "ocid1.compartment.oc1..example"
        name: "my-devops-project"
        lifecycle_state: "ACTIVE"
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from oci.devops import DevopsClient
    from oci.devops.models import (
        CreateProjectDetails,
        UpdateProjectDetails,
        NotificationConfig,
    )
    from oci.exceptions import ServiceError

    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False

from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_common import (
    OCI_COMMON_ARGS,
    DEAD_STATES,
    READY_STATES,
    to_dict,
)
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_auth import create_service_client
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_wait import (
    call_with_retry,
    wait_for_resource,
)


def get_module_args():
    """Build argument spec for this module."""
    module_args = dict(
        compartment_id=dict(type="str"),
        project_id=dict(type="str"),
        name=dict(type="str"),
        description=dict(type="str"),
        notification_config=dict(type="dict"),
        state=dict(type="str", choices=["present", "absent"], default="present"),
    )
    module_args.update(OCI_COMMON_ARGS)
    return module_args


def get_resource(client, resource_id):
    """Get an existing DevOps project by OCID."""
    try:
        response = call_with_retry(client.get_project, resource_id)
        return response.data
    except ServiceError as e:
        if e.status == 404:
            return None
        raise


def find_resource(client, compartment_id, name):
    """Find a DevOps project by compartment and name."""
    if not compartment_id:
        return None
    try:
        response = call_with_retry(
            client.list_projects,
            compartment_id=compartment_id,
        )
        for item in response.data.items:
            if item.lifecycle_state in DEAD_STATES:
                continue
            if name and item.name == name:
                return item
    except ServiceError:
        pass
    return None


def create_resource(module, client):
    """Create a new DevOps project."""
    params = module.params
    kwargs = dict(
        compartment_id=params["compartment_id"],
        name=params["name"],
        description=params.get("description"),
        freeform_tags=params.get("freeform_tags"),
        defined_tags=params.get("defined_tags"),
    )
    if params.get("notification_config"):
        kwargs["notification_config"] = NotificationConfig(
            topic_id=params["notification_config"].get("topic_id"),
        )
    create_details = CreateProjectDetails(**kwargs)
    response = call_with_retry(client.create_project, create_details)
    resource = response.data
    resource = wait_for_resource(
        module, client.get_project, resource.id, target_states=READY_STATES,
    )
    return resource


def update_resource(module, client, existing):
    """Update an existing DevOps project."""
    params = module.params
    kwargs = dict(
        description=params.get("description"),
        freeform_tags=params.get("freeform_tags"),
        defined_tags=params.get("defined_tags"),
    )
    if params.get("notification_config"):
        kwargs["notification_config"] = NotificationConfig(
            topic_id=params["notification_config"].get("topic_id"),
        )
    update_details = UpdateProjectDetails(**kwargs)
    response = call_with_retry(client.update_project, existing.id, update_details)
    resource = response.data
    resource = wait_for_resource(
        module, client.get_project, resource.id, target_states=READY_STATES,
    )
    return resource


def delete_resource(module, client, existing):
    """Delete a DevOps project."""
    call_with_retry(client.delete_project, existing.id)
    wait_for_resource(
        module, client.get_project, existing.id, target_states=DEAD_STATES,
    )


def needs_update(params, existing):
    """Determine if the existing resource differs from desired state."""
    updatable = ["description"]
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
        required_if=[
            ("state", "present", ("compartment_id", "name"), True),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, DevopsClient)
    params = module.params
    state = params["state"]

    existing = None
    if params.get("project_id"):
        existing = get_resource(client, params["project_id"])
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
                module.fail_json(msg=f"Parameter '{req}' is required to create a DevOps project.")
        if module.check_mode:
            module.exit_json(changed=True)
        resource = create_resource(module, client)
        module.exit_json(changed=True, devops_project=to_dict(resource))
        return

    if needs_update(params, existing):
        if module.check_mode:
            module.exit_json(changed=True)
        resource = update_resource(module, client, existing)
        module.exit_json(changed=True, devops_project=to_dict(resource))
        return

    module.exit_json(changed=False, devops_project=to_dict(existing))


if __name__ == "__main__":
    main()
