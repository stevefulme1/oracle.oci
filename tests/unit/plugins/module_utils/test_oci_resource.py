"""Unit tests for oracle.oci.plugins.module_utils.oci_resource."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from unittest.mock import MagicMock, patch, call

import pytest


RESOURCE_PATH = "ansible_collections.oracle.oci.plugins.module_utils.oci_resource"


def _mock_resource(**kwargs):
    """Return a mock OCI resource with given attributes."""
    resource = MagicMock()
    defaults = {
        "id": "ocid1.resource.oc1..test",
        "display_name": "test-resource",
        "lifecycle_state": "AVAILABLE",
        "compartment_id": "ocid1.compartment.oc1..test",
        "freeform_tags": {},
        "defined_tags": {},
    }
    defaults.update(kwargs)
    for key, value in defaults.items():
        setattr(resource, key, value)
    return resource


class _ConcreteResource:
    """Minimal OciResourceBase subclass for testing."""

    client_class = MagicMock

    def __init__(self, module, existing=None, created=None, updated=None):
        self._existing = existing
        self._created = created
        self._updated = updated
        # Inline init to avoid real client creation
        self.module = module
        self.client = MagicMock()
        self.check_mode = module.check_mode
        self._updatable = []
        self._deleted = False

    def get_resource(self):
        return self._existing

    def create_resource(self):
        return self._created

    def update_resource(self, resource):
        return self._updated

    def delete_resource(self, resource):
        self._deleted = True

    def to_dict(self, resource):
        if resource is None:
            return {}
        return {"id": getattr(resource, "id", "unknown")}

    def needs_update(self, resource):
        from ansible_collections.oracle.oci.plugins.module_utils.oci_resource import OciResourceBase
        return OciResourceBase.needs_update(self, resource)

    def _updatable_attributes(self):
        return self._updatable

    def get_tags(self):
        return (
            self.module.params.get("freeform_tags"),
            self.module.params.get("defined_tags"),
        )

    def tags_changed(self, resource):
        from ansible_collections.oracle.oci.plugins.module_utils.oci_resource import OciResourceBase
        return OciResourceBase.tags_changed(self, resource)

    def run(self):
        from ansible_collections.oracle.oci.plugins.module_utils.oci_resource import OciResourceBase
        return OciResourceBase.run(self)


class TestOciResourceBaseRunPresent:
    """Test OciResourceBase.run() with state=present."""

    def test_create_when_not_exists(self, module_args):
        """When resource does not exist, run() creates it."""
        module_args["state"] = "present"
        module = MagicMock()
        module.params = module_args
        module.check_mode = False

        created = _mock_resource(id="ocid1.resource.oc1..new")
        handler = _ConcreteResource(module, existing=None, created=created)
        handler.run()

        module.exit_json.assert_called_once()
        call_kwargs = module.exit_json.call_args[1]
        assert call_kwargs["changed"] is True
        assert call_kwargs["resource"]["id"] == "ocid1.resource.oc1..new"

    def test_no_op_when_exists_no_update(self, module_args):
        """When resource exists and no update needed, run() returns unchanged."""
        module_args["state"] = "present"
        module = MagicMock()
        module.params = module_args
        module.check_mode = False

        existing = _mock_resource()
        handler = _ConcreteResource(module, existing=existing)
        handler.run()

        module.exit_json.assert_called_once()
        call_kwargs = module.exit_json.call_args[1]
        assert call_kwargs["changed"] is False

    def test_update_when_needs_update(self, module_args):
        """When resource exists and needs update, run() updates it."""
        module_args["state"] = "present"
        module_args["display_name"] = "new-name"
        module = MagicMock()
        module.params = module_args
        module.check_mode = False

        existing = _mock_resource(display_name="old-name")
        updated = _mock_resource(display_name="new-name", id="ocid1.resource.oc1..updated")

        handler = _ConcreteResource(module, existing=existing, updated=updated)
        handler._updatable = ["display_name"]
        handler.run()

        module.exit_json.assert_called_once()
        call_kwargs = module.exit_json.call_args[1]
        assert call_kwargs["changed"] is True

    def test_check_mode_create(self, module_args):
        """In check_mode, create reports changed=True without calling create."""
        module_args["state"] = "present"
        module = MagicMock()
        module.params = module_args
        module.check_mode = True

        handler = _ConcreteResource(module, existing=None, created=_mock_resource())
        handler.run()

        module.exit_json.assert_called_once()
        call_kwargs = module.exit_json.call_args[1]
        assert call_kwargs["changed"] is True
        # Should not contain resource key — check_mode doesn't create
        assert "resource" not in call_kwargs

    def test_check_mode_update(self, module_args):
        """In check_mode, update reports changed=True without calling update."""
        module_args["state"] = "present"
        module_args["display_name"] = "updated"
        module = MagicMock()
        module.params = module_args
        module.check_mode = True

        existing = _mock_resource(display_name="original")
        handler = _ConcreteResource(module, existing=existing)
        handler._updatable = ["display_name"]
        handler.run()

        module.exit_json.assert_called_once()
        call_kwargs = module.exit_json.call_args[1]
        assert call_kwargs["changed"] is True
        assert "resource" not in call_kwargs


class TestOciResourceBaseRunAbsent:
    """Test OciResourceBase.run() with state=absent."""

    def test_delete_when_exists(self, module_args):
        """When resource exists, run() deletes it."""
        module_args["state"] = "absent"
        module = MagicMock()
        module.params = module_args
        module.check_mode = False

        existing = _mock_resource()
        handler = _ConcreteResource(module, existing=existing)
        handler.run()

        assert handler._deleted is True
        module.exit_json.assert_called_once()
        call_kwargs = module.exit_json.call_args[1]
        assert call_kwargs["changed"] is True

    def test_no_op_when_not_exists(self, module_args):
        """When resource does not exist, run() returns unchanged."""
        module_args["state"] = "absent"
        module = MagicMock()
        module.params = module_args
        module.check_mode = False

        handler = _ConcreteResource(module, existing=None)
        handler.run()

        assert handler._deleted is False
        module.exit_json.assert_called_once()
        call_kwargs = module.exit_json.call_args[1]
        assert call_kwargs["changed"] is False

    def test_check_mode_delete(self, module_args):
        """In check_mode, delete reports changed=True without calling delete."""
        module_args["state"] = "absent"
        module = MagicMock()
        module.params = module_args
        module.check_mode = True

        existing = _mock_resource()
        handler = _ConcreteResource(module, existing=existing)
        handler.run()

        assert handler._deleted is False
        module.exit_json.assert_called_once()
        call_kwargs = module.exit_json.call_args[1]
        assert call_kwargs["changed"] is True


class TestNeedsUpdate:
    """Test OciResourceBase.needs_update()."""

    def test_returns_true_when_differs(self, module_args):
        """needs_update returns True when an updatable attribute differs."""
        module_args["display_name"] = "desired-name"
        module = MagicMock()
        module.params = module_args
        module.check_mode = False

        resource = _mock_resource(display_name="current-name")
        handler = _ConcreteResource(module, existing=resource)
        handler._updatable = ["display_name"]

        assert handler.needs_update(resource) is True

    def test_returns_false_when_same(self, module_args):
        """needs_update returns False when all updatable attributes match."""
        module_args["display_name"] = "same-name"
        module = MagicMock()
        module.params = module_args
        module.check_mode = False

        resource = _mock_resource(display_name="same-name")
        handler = _ConcreteResource(module, existing=resource)
        handler._updatable = ["display_name"]

        assert handler.needs_update(resource) is False

    def test_skips_none_params(self, module_args):
        """needs_update ignores params that are None."""
        module_args["display_name"] = None
        module = MagicMock()
        module.params = module_args
        module.check_mode = False

        resource = _mock_resource(display_name="anything")
        handler = _ConcreteResource(module, existing=resource)
        handler._updatable = ["display_name"]

        assert handler.needs_update(resource) is False

    def test_empty_updatable_list(self, module_args):
        """needs_update returns False when no updatable attributes defined."""
        module = MagicMock()
        module.params = module_args
        module.check_mode = False

        resource = _mock_resource()
        handler = _ConcreteResource(module, existing=resource)
        handler._updatable = []

        assert handler.needs_update(resource) is False


class TestTagsChanged:
    """Test OciResourceBase.tags_changed()."""

    def test_freeform_tags_differ(self, module_args):
        """tags_changed returns True when freeform_tags differ."""
        module_args["freeform_tags"] = {"env": "prod"}
        module = MagicMock()
        module.params = module_args
        module.check_mode = False

        resource = _mock_resource(freeform_tags={"env": "dev"})
        handler = _ConcreteResource(module, existing=resource)

        assert handler.tags_changed(resource) is True

    def test_tags_same(self, module_args):
        """tags_changed returns False when tags match."""
        module_args["freeform_tags"] = {"env": "prod"}
        module_args["defined_tags"] = None
        module = MagicMock()
        module.params = module_args
        module.check_mode = False

        resource = _mock_resource(freeform_tags={"env": "prod"})
        handler = _ConcreteResource(module, existing=resource)

        assert handler.tags_changed(resource) is False

    def test_tags_none_ignored(self, module_args):
        """tags_changed returns False when desired tags are None."""
        module_args["freeform_tags"] = None
        module_args["defined_tags"] = None
        module = MagicMock()
        module.params = module_args
        module.check_mode = False

        resource = _mock_resource(freeform_tags={"env": "prod"})
        handler = _ConcreteResource(module, existing=resource)

        assert handler.tags_changed(resource) is False


class TestToDict:
    """Test OciResourceBase.to_dict()."""

    def test_converts_resource(self):
        """to_dict converts object attributes to a plain dict."""
        from ansible_collections.oracle.oci.plugins.module_utils.oci_resource import OciResourceBase

        module = MagicMock()
        module.check_mode = False

        class FakeResource:
            def __init__(self):
                self.id = "ocid1.test"
                self.name = "my-resource"
                self._private = "hidden"

        with patch(f"{RESOURCE_PATH}.create_service_client"):
            obj = OciResourceBase(module)
            result = obj.to_dict(FakeResource())

        assert result["id"] == "ocid1.test"
        assert result["name"] == "my-resource"
        assert "_private" not in result

    def test_converts_none(self):
        """to_dict returns empty dict for None input."""
        from ansible_collections.oracle.oci.plugins.module_utils.oci_resource import OciResourceBase

        module = MagicMock()
        module.check_mode = False

        with patch(f"{RESOURCE_PATH}.create_service_client"):
            obj = OciResourceBase(module)
            assert obj.to_dict(None) == {}
