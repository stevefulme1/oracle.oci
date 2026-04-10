"""Base resource helper for OCI Ansible modules."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ansible_collections.oracle.oci.plugins.module_utils.oci_auth import create_service_client
from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import (
    call_with_retry,
    wait_for_resource,
)

if TYPE_CHECKING:
    from ansible.module_utils.basic import AnsibleModule


class OciResourceBase:
    """Base class for OCI resource management modules.

    Subclasses must implement:
        - client_class: the OCI SDK client class
        - get_resource(): retrieve current resource state
        - create_resource(): create a new resource
        - update_resource(): update an existing resource
        - delete_resource(): delete a resource
        - to_dict(): convert OCI resource object to dict
    """

    client_class = None

    def __init__(self, module: AnsibleModule):
        self.module = module
        self.client = create_service_client(module, self.client_class)
        self.check_mode = module.check_mode

    def get_resource(self):
        """Return the current resource or None if not found."""
        raise NotImplementedError

    def create_resource(self):
        """Create the resource and return it."""
        raise NotImplementedError

    def update_resource(self, resource):
        """Update the resource and return it."""
        raise NotImplementedError

    def delete_resource(self, resource):
        """Delete the resource."""
        raise NotImplementedError

    def to_dict(self, resource) -> dict:
        """Convert an OCI SDK resource object to a serializable dict."""
        if resource is None:
            return {}
        if hasattr(resource, "__dict__"):
            result = {}
            for key, value in resource.__dict__.items():
                if key.startswith("_"):
                    continue
                if hasattr(value, "__dict__") and not isinstance(value, (str, int, float, bool, list, dict)):
                    result[key] = self.to_dict(value)
                elif isinstance(value, list):
                    result[key] = [
                        self.to_dict(item) if hasattr(item, "__dict__") else item
                        for item in value
                    ]
                else:
                    result[key] = value
            return result
        return resource

    def needs_update(self, resource) -> bool:
        """Check if resource attributes differ from desired state."""
        for key in self._updatable_attributes():
            desired = self.module.params.get(key)
            if desired is None:
                continue
            current = getattr(resource, key, None)
            if current != desired:
                return True
        return False

    def _updatable_attributes(self) -> list[str]:
        """Return list of attribute names that can be updated."""
        return []

    def get_tags(self) -> tuple[dict | None, dict | None]:
        """Return (freeform_tags, defined_tags) from module params."""
        return (
            self.module.params.get("freeform_tags"),
            self.module.params.get("defined_tags"),
        )

    def tags_changed(self, resource) -> bool:
        """Check if tags differ from current resource."""
        freeform, defined = self.get_tags()
        if freeform is not None and getattr(resource, "freeform_tags", None) != freeform:
            return True
        if defined is not None and getattr(resource, "defined_tags", None) != defined:
            return True
        return False

    def run(self) -> None:
        """Main entry point — determine action and execute."""
        state = self.module.params.get("state", "present")
        resource = self.get_resource()

        if state == "absent":
            if resource is None:
                self.module.exit_json(changed=False)
                return
            if self.check_mode:
                self.module.exit_json(changed=True)
                return
            self.delete_resource(resource)
            self.module.exit_json(changed=True)
            return

        # state == present
        if resource is None:
            if self.check_mode:
                self.module.exit_json(changed=True)
                return
            resource = self.create_resource()
            self.module.exit_json(changed=True, resource=self.to_dict(resource))
            return

        if self.needs_update(resource) or self.tags_changed(resource):
            if self.check_mode:
                self.module.exit_json(changed=True)
                return
            resource = self.update_resource(resource)
            self.module.exit_json(changed=True, resource=self.to_dict(resource))
            return

        self.module.exit_json(changed=False, resource=self.to_dict(resource))
