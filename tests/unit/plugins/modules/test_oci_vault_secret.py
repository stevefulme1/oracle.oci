"""Unit tests for oracle.oci.oci_vault_secret module."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from unittest.mock import MagicMock, patch

import pytest


MODULE_PATH = "ansible_collections.oracle.oci.plugins.modules.oci_vault_secret"
AUTH_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_auth"
RESOURCE_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_resource"
WAIT_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_wait"


def _build_secret(
    secret_name="test-secret",
    description="Test secret",
):
    """Return a mock OCI vault secret object."""
    secret = MagicMock()
    secret.secret_name = secret_name
    secret.description = description
    secret.id = "ocid1.vaultsecret.oc1..testresource"
    secret.compartment_id = "ocid1.compartment.oc1..test"
    secret.vault_id = "ocid1.vault.oc1..test"
    secret.key_id = "ocid1.key.oc1..test"
    secret.lifecycle_state = "ACTIVE"
    secret.freeform_tags = {}
    secret.defined_tags = {}
    return secret


@pytest.fixture
def secret_create_args(module_args):
    """Module args for creating a secret."""
    module_args.update({
        "compartment_id": "ocid1.compartment.oc1..test",
        "vault_id": "ocid1.vault.oc1..test",
        "key_id": "ocid1.key.oc1..test",
        "secret_name": "test-secret",
        "description": "Test secret",
        "secret_content": {"content_type": "BASE64", "content": "c2VjcmV0dmFsdWU="},
        "secret_id": None,
    })
    return module_args


class TestOciVaultSecretCreate:
    """Test vault secret creation."""

    @patch(f"{AUTH_PATH}.create_service_client")
    def test_create_secret(self, mock_create_client, secret_create_args):
        """Creating a secret calls create_secret."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        created = _build_secret()
        mock_response = MagicMock()
        mock_response.data = created
        mock_client.create_secret.return_value = mock_response

        module = MagicMock()
        module.params = secret_create_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_vault_secret import create_secret
        result = create_secret(module, mock_client)

        mock_client.create_secret.assert_called_once()


class TestOciVaultSecretDelete:
    """Test vault secret deletion."""

    @patch(f"{AUTH_PATH}.create_service_client")
    def test_delete_secret(self, mock_create_client, module_args):
        """Deleting a secret calls schedule_secret_deletion."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "state": "absent",
            "secret_id": "ocid1.vaultsecret.oc1..testresource",
            "compartment_id": None,
            "vault_id": None,
            "key_id": None,
            "secret_name": None,
            "description": None,
            "secret_content": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        resource = _build_secret()

        from ansible_collections.oracle.oci.plugins.modules.oci_vault_secret import delete_secret
        delete_secret(module, mock_client, resource)

        mock_client.schedule_secret_deletion.assert_called_once()

    @patch(f"{AUTH_PATH}.create_service_client")
    def test_delete_secret_already_gone(self, mock_create_client, module_args):
        """When secret does not exist, get_secret returns None."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        import oci.exceptions
        mock_client.get_secret.side_effect = oci.exceptions.ServiceError(
            status=404, code="NotAuthorizedOrNotFound", message="not found", headers={},
        )

        from ansible_collections.oracle.oci.plugins.modules.oci_vault_secret import get_secret
        result = get_secret(mock_client, "ocid1.vaultsecret.oc1..nonexistent")
        assert result is None


class TestOciVaultSecretUpdate:
    """Test vault secret update."""

    @patch(f"{AUTH_PATH}.create_service_client")
    def test_update_secret(self, mock_create_client, module_args):
        """Updating a secret calls update_secret."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "state": "present",
            "secret_id": "ocid1.vaultsecret.oc1..testresource",
            "description": "Updated description",
            "secret_content": {"content_type": "BASE64", "content": "bmV3c2VjcmV0"},
            "compartment_id": None,
            "vault_id": None,
            "key_id": None,
            "secret_name": None,
        })

        updated = _build_secret(description="Updated description")
        mock_response = MagicMock()
        mock_response.data = updated
        mock_client.update_secret.return_value = mock_response

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        resource = _build_secret()

        from ansible_collections.oracle.oci.plugins.modules.oci_vault_secret import update_secret
        result = update_secret(module, mock_client, resource)

        mock_client.update_secret.assert_called_once()


class TestOciVaultSecretIdempotent:
    """Test idempotent behavior when no change is needed."""

    @patch(f"{AUTH_PATH}.create_service_client")
    def test_no_change_needed(self, mock_create_client, module_args):
        """When current state matches desired state, needs_update returns False."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "secret_name": "test-secret",
            "description": "Test secret",
            "secret_content": None,
            "compartment_id": None,
            "vault_id": None,
            "key_id": None,
            "secret_id": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        resource = _build_secret()

        from ansible_collections.oracle.oci.plugins.modules.oci_vault_secret import needs_update
        assert not needs_update(module.params, resource)
