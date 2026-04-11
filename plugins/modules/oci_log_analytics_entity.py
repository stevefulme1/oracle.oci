# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Log Analytics Entities."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_log_analytics_entity
short_description: Manage OCI Log Analytics Entities
description:
  - Create, update, and delete log analytics entities in OCI.
  - Entities represent infrastructure resources whose logs are analyzed.
version_added: "1.0.0"
author: Oracle (@oracle)
options:
  namespace_name:
    description:
      - The Log Analytics namespace.
    type: str
    required: true
  compartment_id:
    description:
      - The OCID of the compartment.
      - Required when creating.
    type: str
  log_analytics_entity_id:
    description:
      - The OCID of the log analytics entity.
      - Required for update and delete operations.
    type: str
  name:
    description:
      - The name of the entity.
      - Required when creating.
    type: str
  entity_type_name:
    description:
      - The entity type name (e.g., Host, Database).
      - Required when creating.
    type: str
  management_agent_id:
    description:
      - The OCID of the management agent associated with the entity.
    type: str
  cloud_resource_id:
    description:
      - The OCID of the cloud resource associated with the entity.
    type: str
  freeform_tags:
    description:
      - Free-form tags for this resource.
    type: dict
  defined_tags:
    description:
      - Defined tags for this resource.
    type: dict
  state:
    description:
      - The desired state of the entity.
    type: str
    default: present
    choices: [present, absent]
extends_documentation_fragment:
  - oracle.oci.oci_common
"""

EXAMPLES = r"""
- name: Create a log analytics entity
  oracle.oci.oci_log_analytics_entity:
    namespace_name: "mynamespace"
    compartment_id: "ocid1.compartment.oc1..example"
    name: "my-host-entity"
    entity_type_name: "Host (Linux)"
    management_agent_id: "ocid1.managementagent.oc1..example"
    state: present

- name: Update entity name
  oracle.oci.oci_log_analytics_entity:
    namespace_name: "mynamespace"
    log_analytics_entity_id: "ocid1.loganalyticsentity.oc1..example"
    name: "renamed-entity"
    state: present

- name: Delete a log analytics entity
  oracle.oci.oci_log_analytics_entity:
    namespace_name: "mynamespace"
    log_analytics_entity_id: "ocid1.loganalyticsentity.oc1..example"
    state: absent
"""

RETURN = r"""
resource:
  description: The log analytics entity details.
  returned: on success
  type: dict
  contains:
    id:
      description: The OCID of the entity.
      type: str
    name:
      description: The name of the entity.
      type: str
    compartment_id:
      description: The OCID of the compartment.
      type: str
    entity_type_name:
      description: The entity type name.
      type: str
    management_agent_id:
      description: The OCID of the management agent.
      type: str
    lifecycle_state:
      description: The current lifecycle state.
      type: str
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.oracle.oci.plugins.module_utils.oci_common import OCI_COMMON_ARGS
from ansible_collections.oracle.oci.plugins.module_utils.oci_auth import create_service_client
from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import call_with_retry

try:
    import oci
    from oci.log_analytics import LogAnalyticsClient
    from oci.log_analytics.models import (
        CreateLogAnalyticsEntityDetails,
        UpdateLogAnalyticsEntityDetails,
    )
    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False


def to_dict(resource):
    """Convert an OCI SDK resource to a serializable dict."""
    if resource is None:
        return {}
    result = {}
    for key, value in resource.__dict__.items():
        if key.startswith("_"):
            continue
        if hasattr(value, "__dict__") and not isinstance(value, (str, int, float, bool, list, dict)):
            result[key] = to_dict(value)
        elif isinstance(value, list):
            result[key] = [to_dict(i) if hasattr(i, "__dict__") else i for i in value]
        else:
            result[key] = value
    return result


def get_entity(client, namespace_name, entity_id):
    """Get a log analytics entity by OCID, return None if not found."""
    try:
        response = call_with_retry(
            client.get_log_analytics_entity,
            namespace_name,
            entity_id,
        )
        entity = response.data
        if entity.lifecycle_state in ("DELETED", "TERMINATED"):
            return None
        return entity
    except oci.exceptions.ServiceError as e:
        if e.status == 404:
            return None
        raise


def find_entity(client, namespace_name, compartment_id, name):
    """Find an entity by compartment and name."""
    if not compartment_id or not name:
        return None
    entities = call_with_retry(
        client.list_log_analytics_entities,
        namespace_name,
        compartment_id,
        name=name,
    ).data.items
    for e in entities:
        if e.name == name and e.lifecycle_state not in ("DELETED", "TERMINATED"):
            return get_entity(client, namespace_name, e.id)
    return None


def create_entity(module, client):
    """Create a new log analytics entity."""
    freeform_tags = module.params.get("freeform_tags") or {}
    defined_tags = module.params.get("defined_tags") or {}

    details = CreateLogAnalyticsEntityDetails(
        compartment_id=module.params["compartment_id"],
        name=module.params["name"],
        entity_type_name=module.params["entity_type_name"],
        management_agent_id=module.params.get("management_agent_id"),
        cloud_resource_id=module.params.get("cloud_resource_id"),
        freeform_tags=freeform_tags,
        defined_tags=defined_tags,
    )
    response = call_with_retry(
        client.create_log_analytics_entity,
        module.params["namespace_name"],
        details,
    )
    return response.data


def update_entity(module, client, entity):
    """Update an existing log analytics entity."""
    kwargs = {}
    for attr in ("name", "management_agent_id", "cloud_resource_id"):
        value = module.params.get(attr)
        if value is not None:
            kwargs[attr] = value
    if module.params.get("freeform_tags") is not None:
        kwargs["freeform_tags"] = module.params["freeform_tags"]
    if module.params.get("defined_tags") is not None:
        kwargs["defined_tags"] = module.params["defined_tags"]

    if not kwargs:
        return entity

    details = UpdateLogAnalyticsEntityDetails(**kwargs)
    response = call_with_retry(
        client.update_log_analytics_entity,
        module.params["namespace_name"],
        entity.id,
        details,
    )
    return response.data


def delete_entity(module, client, entity):
    """Delete a log analytics entity."""
    call_with_retry(
        client.delete_log_analytics_entity,
        module.params["namespace_name"],
        entity.id,
    )


def needs_update(module, entity):
    """Check if the entity needs updating."""
    for attr in ("name", "management_agent_id", "cloud_resource_id"):
        desired = module.params.get(attr)
        if desired is not None and getattr(entity, attr, None) != desired:
            return True
    if module.params.get("freeform_tags") is not None:
        if getattr(entity, "freeform_tags", None) != module.params["freeform_tags"]:
            return True
    if module.params.get("defined_tags") is not None:
        if getattr(entity, "defined_tags", None) != module.params["defined_tags"]:
            return True
    return False


def run_module():
    """Main module execution."""
    module_args = dict(
        namespace_name=dict(type="str", required=True),
        compartment_id=dict(type="str"),
        log_analytics_entity_id=dict(type="str"),
        name=dict(type="str"),
        entity_type_name=dict(type="str"),
        management_agent_id=dict(type="str"),
        cloud_resource_id=dict(type="str"),
        state=dict(type="str", default="present", choices=["present", "absent"]),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            ("state", "present", ("compartment_id", "name", "entity_type_name"), True),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, LogAnalyticsClient)
    state = module.params.get("state", "present")
    namespace_name = module.params["namespace_name"]
    entity_id = module.params.get("log_analytics_entity_id")

    # Get existing resource
    entity = None
    if entity_id:
        entity = get_entity(client, namespace_name, entity_id)
    elif module.params.get("compartment_id") and module.params.get("name"):
        entity = find_entity(client, namespace_name, module.params["compartment_id"], module.params["name"])

    if state == "absent":
        if entity is None:
            module.exit_json(changed=False)
        if module.check_mode:
            module.exit_json(changed=True)
        delete_entity(module, client, entity)
        module.exit_json(changed=True)
        return

    # state == present
    if entity is None:
        if not module.params.get("compartment_id") or not module.params.get("name"):
            module.fail_json(msg="compartment_id, name, and entity_type_name are required to create an entity.")
        if module.check_mode:
            module.exit_json(changed=True)
        entity = create_entity(module, client)
        module.exit_json(changed=True, resource=to_dict(entity))
        return

    if needs_update(module, entity):
        if module.check_mode:
            module.exit_json(changed=True)
        entity = update_entity(module, client, entity)
        module.exit_json(changed=True, resource=to_dict(entity))
        return

    module.exit_json(changed=False, resource=to_dict(entity))


def main():
    run_module()


if __name__ == "__main__":
    main()
