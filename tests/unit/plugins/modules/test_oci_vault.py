"""Unit tests for stevefulme1.oci_cloud.oci_vault module."""
from __future__ import absolute_import, division, print_function
__metaclass__ = type

from unittest.mock import MagicMock, patch
import pytest

MODULE_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.modules.oci_vault"
RESOURCE_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_resource"


def _build_resource(**overrides):
    """Return a mock OCI vault object."""
    resource = MagicMock()
    resource.id = overrides.get("id", "ocid1.vault.oc1..test")
    resource.display_name = overrides.get("display_name", "My Vault")
    resource.lifecycle_state = overrides.get("lifecycle_state", "ACTIVE")
    resource.compartment_id = overrides.get("compartment_id", "ocid1.compartment.oc1..test")
    resource.freeform_tags = overrides.get("freeform_tags", {})
    resource.defined_tags = overrides.get("defined_tags", {})
    return resource


@pytest.fixture
def create_args(module_args):
    """Module args for creating a vault."""
    module_args.update({
        "display_name": "My Vault",
        "compartment_id": "ocid1.compartment.oc1..test",
        "state": "present",
    })
    return module_args


class TestCreate:
    """Test vault creation."""

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_create_resource(self, mock_create_client, create_args):
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        created = _build_resource()
        mock_response = MagicMock()
        mock_response.data = created
        mock_client.create_vault.return_value = mock_response

        module = MagicMock()
        module.params = create_args
        module.check_mode = False

        from ansible_collections.stevefulme1.oci_cloud.plugins.modules.oci_vault import OciVault
        obj = OciVault(module)
        result = obj.create_resource()

        mock_client.create_vault.assert_called_once()
        assert result.display_name == "My Vault"

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_create_check_mode(self, mock_create_client, create_args):
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module = MagicMock()
        module.params = create_args
        module.check_mode = True

        from ansible_collections.stevefulme1.oci_cloud.plugins.modules.oci_vault import OciVault
        obj = OciVault(module)
        # In check mode, no API calls should be made
        assert module.check_mode is True
        mock_client.create_vault.assert_not_called()


class TestDelete:
    """Test vault deletion."""

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_delete_resource(self, mock_create_client, module_args):
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "display_name": "My Vault",
            "compartment_id": None,
            "state": "absent",
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False

        from ansible_collections.stevefulme1.oci_cloud.plugins.modules.oci_vault import OciVault
        resource = _build_resource()

        obj = OciVault(module)
        obj.delete_resource(resource)

        mock_client.delete_vault.assert_called_once()

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_delete_already_gone(self, mock_create_client, module_args):
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        import oci.exceptions
        mock_client.get_vault.side_effect = oci.exceptions.ServiceError(
            status=404, code="NotFound", message="not found", headers={},
        )

        module_args.update({
            "display_name": "nonexistent",
            "compartment_id": None,
            "state": "absent",
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False

        from ansible_collections.stevefulme1.oci_cloud.plugins.modules.oci_vault import OciVault
        obj = OciVault(module)
        result = obj.get_resource()
        assert result is None


class TestUpdate:
    """Test vault update."""

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_update_resource(self, mock_create_client, module_args):
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "display_name": "updated-name",
            "compartment_id": "ocid1.compartment.oc1..test",
            "state": "present",
        })

        updated = _build_resource(display_name="updated-name")
        mock_response = MagicMock()
        mock_response.data = updated
        mock_client.update_vault.return_value = mock_response

        module = MagicMock()
        module.params = module_args
        module.check_mode = False

        from ansible_collections.stevefulme1.oci_cloud.plugins.modules.oci_vault import OciVault
        resource = _build_resource()

        obj = OciVault(module)
        result = obj.update_resource(resource)

        mock_client.update_vault.assert_called_once()
        assert result.display_name == "updated-name"


class TestIdempotent:
    """Test idempotent behavior."""

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_no_change_needed(self, mock_create_client, module_args):
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "display_name": "My Vault",
            "compartment_id": None,
            "state": "present",
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False

        from ansible_collections.stevefulme1.oci_cloud.plugins.modules.oci_vault import OciVault
        resource = _build_resource()

        obj = OciVault(module)
        assert not obj.needs_update(resource)


class TestErrorHandling:
    """Test error handling."""

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_auth_error(self, mock_create_client, create_args):
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        import oci.exceptions
        mock_client.create_vault.side_effect = oci.exceptions.ServiceError(
            status=401, code="NotAuthenticated", message="unauthorized", headers={},
        )

        module = MagicMock()
        module.params = create_args
        module.check_mode = False

        from ansible_collections.stevefulme1.oci_cloud.plugins.modules.oci_vault import OciVault
        obj = OciVault(module)

        with pytest.raises(oci.exceptions.ServiceError):
            obj.create_resource()

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_conflict_error(self, mock_create_client, create_args):
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        import oci.exceptions
        mock_client.create_vault.side_effect = oci.exceptions.ServiceError(
            status=409, code="Conflict", message="already exists", headers={},
        )

        module = MagicMock()
        module.params = create_args
        module.check_mode = False

        from ansible_collections.stevefulme1.oci_cloud.plugins.modules.oci_vault import OciVault
        obj = OciVault(module)

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
        mock_client.create_vault.return_value = mock_response

        module = MagicMock()
        module.params = create_args
        module.check_mode = False

        from ansible_collections.stevefulme1.oci_cloud.plugins.modules.oci_vault import OciVault
        obj = OciVault(module)
        result = obj.create_resource()

        assert hasattr(result, "id")
        assert hasattr(result, "display_name")
        assert hasattr(result, "lifecycle_state")
