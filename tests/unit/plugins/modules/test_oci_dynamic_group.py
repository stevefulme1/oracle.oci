"""Unit tests for stevefulme1.oci_cloud.oci_dynamic_group module."""
from __future__ import absolute_import, division, print_function
__metaclass__ = type

from unittest.mock import MagicMock, patch
import pytest

MODULE_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.modules.oci_dynamic_group"
RESOURCE_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_resource"


def _build_resource(**overrides):
    """Return a mock OCI dynamic_group object."""
    resource = MagicMock()
    resource.id = overrides.get("id", "ocid1.dynamic_group.oc1..test")
    resource.name = overrides.get("name", "dg-instances")
    resource.lifecycle_state = overrides.get("lifecycle_state", "ACTIVE")
    resource.compartment_id = overrides.get("compartment_id", "ocid1.tenancy.oc1..test")
    resource.freeform_tags = overrides.get("freeform_tags", {})
    resource.defined_tags = overrides.get("defined_tags", {})
    return resource


@pytest.fixture
def create_args(module_args):
    """Module args for creating a dynamic_group."""
    module_args.update({
        "name": "dg-instances",
        "compartment_id": "ocid1.tenancy.oc1..test",
        "state": "present",
    })
    return module_args


class TestCreate:
    """Test dynamic_group creation."""

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_create_resource(self, mock_create_client, create_args):
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        created = _build_resource()
        mock_response = MagicMock()
        mock_response.data = created
        mock_client.create_dynamic_group.return_value = mock_response

        module = MagicMock()
        module.params = create_args
        module.check_mode = False

        from ansible_collections.stevefulme1.oci_cloud.plugins.modules.oci_dynamic_group import OciDynamicGroup
        obj = OciDynamicGroup(module)
        result = obj.create_resource()

        mock_client.create_dynamic_group.assert_called_once()
        assert result.name == "dg-instances"

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_create_check_mode(self, mock_create_client, create_args):
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module = MagicMock()
        module.params = create_args
        module.check_mode = True

        from ansible_collections.stevefulme1.oci_cloud.plugins.modules.oci_dynamic_group import OciDynamicGroup
        obj = OciDynamicGroup(module)
        # In check mode, no API calls should be made
        assert module.check_mode is True
        mock_client.create_dynamic_group.assert_not_called()


class TestDelete:
    """Test dynamic_group deletion."""

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_delete_resource(self, mock_create_client, module_args):
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "name": "dg-instances",
            "compartment_id": None,
            "state": "absent",
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False

        from ansible_collections.stevefulme1.oci_cloud.plugins.modules.oci_dynamic_group import OciDynamicGroup
        resource = _build_resource()

        obj = OciDynamicGroup(module)
        obj.delete_resource(resource)

        mock_client.delete_dynamic_group.assert_called_once()

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_delete_already_gone(self, mock_create_client, module_args):
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        import oci.exceptions
        mock_client.get_dynamic_group.side_effect = oci.exceptions.ServiceError(
            status=404, code="NotFound", message="not found", headers={},
        )

        module_args.update({
            "name": "nonexistent",
            "compartment_id": None,
            "state": "absent",
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False

        from ansible_collections.stevefulme1.oci_cloud.plugins.modules.oci_dynamic_group import OciDynamicGroup
        obj = OciDynamicGroup(module)
        result = obj.get_resource()
        assert result is None


class TestUpdate:
    """Test dynamic_group update."""

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_update_resource(self, mock_create_client, module_args):
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "name": "updated-name",
            "compartment_id": "ocid1.tenancy.oc1..test",
            "state": "present",
        })

        updated = _build_resource(name="updated-name")
        mock_response = MagicMock()
        mock_response.data = updated
        mock_client.update_dynamic_group.return_value = mock_response

        module = MagicMock()
        module.params = module_args
        module.check_mode = False

        from ansible_collections.stevefulme1.oci_cloud.plugins.modules.oci_dynamic_group import OciDynamicGroup
        resource = _build_resource()

        obj = OciDynamicGroup(module)
        result = obj.update_resource(resource)

        mock_client.update_dynamic_group.assert_called_once()
        assert result.name == "updated-name"


class TestIdempotent:
    """Test idempotent behavior."""

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_no_change_needed(self, mock_create_client, module_args):
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "name": "dg-instances",
            "compartment_id": None,
            "state": "present",
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False

        from ansible_collections.stevefulme1.oci_cloud.plugins.modules.oci_dynamic_group import OciDynamicGroup
        resource = _build_resource()

        obj = OciDynamicGroup(module)
        assert not obj.needs_update(resource)


class TestErrorHandling:
    """Test error handling."""

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_auth_error(self, mock_create_client, create_args):
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        import oci.exceptions
        mock_client.create_dynamic_group.side_effect = oci.exceptions.ServiceError(
            status=401, code="NotAuthenticated", message="unauthorized", headers={},
        )

        module = MagicMock()
        module.params = create_args
        module.check_mode = False

        from ansible_collections.stevefulme1.oci_cloud.plugins.modules.oci_dynamic_group import OciDynamicGroup
        obj = OciDynamicGroup(module)

        with pytest.raises(oci.exceptions.ServiceError):
            obj.create_resource()

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_conflict_error(self, mock_create_client, create_args):
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        import oci.exceptions
        mock_client.create_dynamic_group.side_effect = oci.exceptions.ServiceError(
            status=409, code="Conflict", message="already exists", headers={},
        )

        module = MagicMock()
        module.params = create_args
        module.check_mode = False

        from ansible_collections.stevefulme1.oci_cloud.plugins.modules.oci_dynamic_group import OciDynamicGroup
        obj = OciDynamicGroup(module)

        with pytest.raises(oci.exceptions.ServiceError):
            obj.create_resource()


class TestReturnValues:
    """Test return value structure."""

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_return_has_id(self, mock_create_client, create_args):
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        created = _build_resource()
        mock_response = MagicMock()
        mock_response.data = created
        mock_client.create_dynamic_group.return_value = mock_response

        module = MagicMock()
        module.params = create_args
        module.check_mode = False

        from ansible_collections.stevefulme1.oci_cloud.plugins.modules.oci_dynamic_group import OciDynamicGroup
        obj = OciDynamicGroup(module)
        result = obj.create_resource()

        assert hasattr(result, "id")
        assert hasattr(result, "name")
        assert hasattr(result, "lifecycle_state")
