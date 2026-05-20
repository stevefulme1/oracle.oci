"""Unit tests for oracle.oci.oci_identity_domain module."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from unittest.mock import MagicMock, patch

import pytest


MODULE_PATH = "ansible_collections.oracle.oci.plugins.modules.oci_identity_domain"
AUTH_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_auth"
RESOURCE_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_resource"
WAIT_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_wait"


def _build_domain(
    display_name="test-domain",
    description="Test domain",
):
    """Return a mock OCI identity domain object."""
    domain = MagicMock()
    domain.display_name = display_name
    domain.description = description
    domain.id = "ocid1.domain.oc1..testresource"
    domain.compartment_id = "ocid1.compartment.oc1..test"
    domain.lifecycle_state = "ACTIVE"
    domain.freeform_tags = {}
    domain.defined_tags = {}
    return domain


@pytest.fixture
def domain_create_args(module_args):
    """Module args for creating a domain."""
    module_args.update({
        "compartment_id": "ocid1.compartment.oc1..test",
        "display_name": "test-domain",
        "description": "Test domain",
        "home_region": "us-phoenix-1",
        "license_type": "free",
        "is_hidden_on_login": None,
        "domain_id": None,
    })
    return module_args


class TestOciIdentityDomainCreate:
    """Test identity domain creation."""

    @patch(f"{AUTH_PATH}.create_service_client")
    def test_create_domain(self, mock_create_client, domain_create_args):
        """Creating a domain calls create_domain."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        created = _build_domain()
        mock_response = MagicMock()
        mock_response.data = created
        mock_client.create_domain.return_value = mock_response

        module = MagicMock()
        module.params = domain_create_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_identity_domain import create_resource
        result = create_resource(module, mock_client)

        mock_client.create_domain.assert_called_once()


class TestOciIdentityDomainDelete:
    """Test identity domain deletion."""

    @patch(f"{AUTH_PATH}.create_service_client")
    def test_delete_domain(self, mock_create_client, module_args):
        """Deleting a domain calls delete_domain."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "domain_id": "ocid1.domain.oc1..testresource",
            "state": "absent",
            "compartment_id": None,
            "display_name": None,
            "description": None,
            "home_region": None,
            "license_type": None,
            "is_hidden_on_login": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        resource = _build_domain()

        from ansible_collections.oracle.oci.plugins.modules.oci_identity_domain import delete_resource
        delete_resource(module, mock_client, resource)

        mock_client.delete_domain.assert_called_once()

    @patch(f"{AUTH_PATH}.create_service_client")
    def test_delete_domain_already_gone(self, mock_create_client, module_args):
        """When domain does not exist, get_resource returns None."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        import oci.exceptions
        mock_client.get_domain.side_effect = oci.exceptions.ServiceError(
            status=404, code="NotAuthorizedOrNotFound", message="not found", headers={},
        )

        module_args.update({
            "domain_id": "ocid1.domain.oc1..nonexistent",
            "state": "absent",
            "compartment_id": None,
            "display_name": None,
            "description": None,
            "home_region": None,
            "license_type": None,
            "is_hidden_on_login": None,
        })

        from ansible_collections.oracle.oci.plugins.modules.oci_identity_domain import get_resource
        result = get_resource(mock_client, "ocid1.domain.oc1..nonexistent")
        assert result is None


class TestOciIdentityDomainUpdate:
    """Test identity domain update."""

    @patch(f"{AUTH_PATH}.create_service_client")
    def test_update_domain(self, mock_create_client, module_args):
        """Updating a domain calls update_domain."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "domain_id": "ocid1.domain.oc1..testresource",
            "display_name": "updated-domain",
            "description": None,
            "compartment_id": None,
            "home_region": None,
            "license_type": None,
            "is_hidden_on_login": None,
        })

        updated = _build_domain(display_name="updated-domain")
        mock_response = MagicMock()
        mock_response.data = updated
        mock_client.update_domain.return_value = mock_response

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        resource = _build_domain()

        from ansible_collections.oracle.oci.plugins.modules.oci_identity_domain import update_resource
        result = update_resource(module, mock_client, resource)

        mock_client.update_domain.assert_called_once()


class TestOciIdentityDomainIdempotent:
    """Test idempotent behavior when no change is needed."""

    @patch(f"{AUTH_PATH}.create_service_client")
    def test_no_change_needed(self, mock_create_client, module_args):
        """When current state matches desired state, needs_update returns False."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "display_name": "test-domain",
            "description": "Test domain",
            "compartment_id": None,
            "home_region": None,
            "license_type": None,
            "is_hidden_on_login": None,
            "domain_id": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        resource = _build_domain()

        from ansible_collections.oracle.oci.plugins.modules.oci_identity_domain import needs_update
        assert not needs_update(module, resource)
