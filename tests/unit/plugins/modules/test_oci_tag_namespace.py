"""Unit tests for oracle.oci.oci_tag_namespace module."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from unittest.mock import MagicMock, patch

import pytest


MODULE_PATH = "ansible_collections.oracle.oci.plugins.modules.oci_tag_namespace"
AUTH_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_auth"
RESOURCE_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_resource"
WAIT_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_wait"


def _build_tag_namespace(
    name='test-namespace',
    description='Test tag namespace',
    is_retired=False,
):
    """Return a mock OCI tag_namespace object."""
    tag_namespace = MagicMock()
    tag_namespace.name = 'test-namespace'
    tag_namespace.description = 'Test tag namespace'
    tag_namespace.is_retired = False
    tag_namespace.id = "ocid1.test.oc1..testresource"
    tag_namespace.compartment_id = "ocid1.tenancy.oc1..test"
    tag_namespace.lifecycle_state = "ACTIVE"
    tag_namespace.freeform_tags = {}
    tag_namespace.defined_tags = {}
    return tag_namespace


@pytest.fixture
def tag_namespace_create_args(module_args):
    """Module args for creating a tag_namespace."""
    module_args.update({
        "compartment_id": 'ocid1.compartment.oc1..test',
        "name": 'test-namespace',
        "description": 'Test tag namespace',
        "is_retired": False,
        "tag_namespace_id": None,
    })
    return module_args


class TestOciTagNamespaceCreate:
    """Test tag_namespace creation."""

    @patch(f"{AUTH_PATH}.create_service_client")
    def test_create_tag_namespace(self, mock_create_client, tag_namespace_create_args):
        """Creating a tag_namespace calls create_tag_namespace."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        created = _build_tag_namespace()
        mock_response = MagicMock()
        mock_response.data = created
        mock_client.create_tag_namespace.return_value = mock_response

        module = MagicMock()
        module.params = tag_namespace_create_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_tag_namespace import create_resource
        result = create_resource(mock_client, module)

        mock_client.create_tag_namespace.assert_called_once()


class TestOciTagNamespaceDelete:
    """Test tag_namespace deletion."""

    @patch(f"{AUTH_PATH}.create_service_client")
    def test_delete_tag_namespace(self, mock_create_client, module_args):
        """Deleting a tag_namespace calls delete_tag_namespace."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "tag_namespace_id": "ocid1.test.oc1..testresource",
            "state": "absent",
            "compartment_id": None,
            "name": None,
            "description": None,
            "is_retired": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        resource = _build_tag_namespace()

        from ansible_collections.oracle.oci.plugins.modules.oci_tag_namespace import delete_resource
        delete_resource(mock_client, module, resource)

        mock_client.delete_tag_namespace.assert_called_once()

    @patch(f"{AUTH_PATH}.create_service_client")
    def test_delete_tag_namespace_already_gone(self, mock_create_client, module_args):
        """When tag_namespace does not exist, get returns None via ServiceError 404."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        import oci.exceptions
        mock_client.get_tag_namespace.side_effect = oci.exceptions.ServiceError(
            status=404, code="NotAuthorizedOrNotFound", message="not found", headers={},
        )

        module_args.update({
            "tag_namespace_id": "ocid1.test.oc1..testresource",
            "state": "absent",
            "compartment_id": None,
            "name": None,
            "description": None,
            "is_retired": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_tag_namespace import get_existing_resource
        result = get_existing_resource(mock_client, module)
        assert result is None


class TestOciTagNamespaceUpdate:
    """Test tag_namespace update."""

    @patch(f"{AUTH_PATH}.create_service_client")
    def test_update_tag_namespace(self, mock_create_client, module_args):
        """Updating a tag_namespace calls update_tag_namespace."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "tag_namespace_id": "ocid1.test.oc1..testresource",
            "state": "absent",
            "compartment_id": None,
            "name": None,
            "description": None,
            "is_retired": None,
            "description": "Updated description",
        })

        updated = _build_tag_namespace(name="updated-tag_namespace")
        mock_response = MagicMock()
        mock_response.data = updated
        mock_client.update_tag_namespace.return_value = mock_response

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        resource = _build_tag_namespace()

        from ansible_collections.oracle.oci.plugins.modules.oci_tag_namespace import update_resource
        result = update_resource(mock_client, module, resource)

        mock_client.update_tag_namespace.assert_called_once()


class TestOciTagNamespaceIdempotent:
    """Test idempotent behavior when no change is needed."""

    @patch(f"{AUTH_PATH}.create_service_client")
    def test_no_change_needed(self, mock_create_client, module_args):
        """When current state matches desired state, needs_update returns False."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "name": 'test-namespace',
            "description": 'Test tag namespace',
            "is_retired": False,
            "compartment_id": None,
            "tag_namespace_id": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        resource = _build_tag_namespace()

        from ansible_collections.oracle.oci.plugins.modules.oci_tag_namespace import needs_update
        assert not needs_update(module, resource)
