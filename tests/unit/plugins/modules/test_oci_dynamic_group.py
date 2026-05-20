"""Unit tests for oracle.oci.oci_dynamic_group module."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from unittest.mock import MagicMock, patch

import pytest


MODULE_PATH = "ansible_collections.oracle.oci.plugins.modules.oci_dynamic_group"
AUTH_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_auth"
RESOURCE_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_resource"
WAIT_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_wait"


def _build_dynamic_group(
    name='test-dynamic-group',
    description='Test dynamic group',
    matching_rule="Any {instance.compartment.id = 'ocid1.compartment.oc1..test'}",
):
    """Return a mock OCI dynamic_group object."""
    dynamic_group = MagicMock()
    dynamic_group.name = 'test-dynamic-group'
    dynamic_group.description = 'Test dynamic group'
    dynamic_group.matching_rule = "Any {instance.compartment.id = 'ocid1.compartment.oc1..test'}"
    dynamic_group.id = "ocid1.test.oc1..testresource"
    dynamic_group.compartment_id = "ocid1.tenancy.oc1..test"
    dynamic_group.lifecycle_state = "ACTIVE"
    dynamic_group.freeform_tags = {}
    dynamic_group.defined_tags = {}
    return dynamic_group


@pytest.fixture
def dynamic_group_create_args(module_args):
    """Module args for creating a dynamic_group."""
    module_args.update({
        "compartment_id": 'ocid1.tenancy.oc1..test',
        "name": 'test-dynamic-group',
        "description": 'Test dynamic group',
        "matching_rule": "Any {instance.compartment.id = 'ocid1.compartment.oc1..test'}",
        "dynamic_group_id": None,
    })
    return module_args


class TestOciDynamicGroupCreate:
    """Test dynamic_group creation."""

    @patch(f"{AUTH_PATH}.create_service_client")
    def test_create_dynamic_group(self, mock_create_client, dynamic_group_create_args):
        """Creating a dynamic_group calls create_dynamic_group."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        created = _build_dynamic_group()
        mock_response = MagicMock()
        mock_response.data = created
        mock_client.create_dynamic_group.return_value = mock_response

        module = MagicMock()
        module.params = dynamic_group_create_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_dynamic_group import create_resource
        result = create_resource(mock_client, module)

        mock_client.create_dynamic_group.assert_called_once()


class TestOciDynamicGroupDelete:
    """Test dynamic_group deletion."""

    @patch(f"{AUTH_PATH}.create_service_client")
    def test_delete_dynamic_group(self, mock_create_client, module_args):
        """Deleting a dynamic_group calls delete_dynamic_group."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "dynamic_group_id": "ocid1.test.oc1..testresource",
            "state": "absent",
            "compartment_id": None,
            "name": None,
            "description": None,
            "matching_rule": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        resource = _build_dynamic_group()

        from ansible_collections.oracle.oci.plugins.modules.oci_dynamic_group import delete_resource
        delete_resource(mock_client, module, resource)

        mock_client.delete_dynamic_group.assert_called_once()

    @patch(f"{AUTH_PATH}.create_service_client")
    def test_delete_dynamic_group_already_gone(self, mock_create_client, module_args):
        """When dynamic_group does not exist, get returns None via ServiceError 404."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        import oci.exceptions
        mock_client.get_dynamic_group.side_effect = oci.exceptions.ServiceError(
            status=404, code="NotAuthorizedOrNotFound", message="not found", headers={},
        )

        module_args.update({
            "dynamic_group_id": "ocid1.test.oc1..testresource",
            "state": "absent",
            "compartment_id": None,
            "name": None,
            "description": None,
            "matching_rule": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_dynamic_group import get_existing_resource
        result = get_existing_resource(mock_client, module)
        assert result is None


class TestOciDynamicGroupUpdate:
    """Test dynamic_group update."""

    @patch(f"{AUTH_PATH}.create_service_client")
    def test_update_dynamic_group(self, mock_create_client, module_args):
        """Updating a dynamic_group calls update_dynamic_group."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "dynamic_group_id": "ocid1.test.oc1..testresource",
            "state": "absent",
            "compartment_id": None,
            "name": None,
            "description": None,
            "matching_rule": None,
            "description": "Updated description",
        })

        updated = _build_dynamic_group(name="updated-dynamic_group")
        mock_response = MagicMock()
        mock_response.data = updated
        mock_client.update_dynamic_group.return_value = mock_response

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        resource = _build_dynamic_group()

        from ansible_collections.oracle.oci.plugins.modules.oci_dynamic_group import update_resource
        result = update_resource(mock_client, module, resource)

        mock_client.update_dynamic_group.assert_called_once()


class TestOciDynamicGroupIdempotent:
    """Test idempotent behavior when no change is needed."""

    @patch(f"{AUTH_PATH}.create_service_client")
    def test_no_change_needed(self, mock_create_client, module_args):
        """When current state matches desired state, needs_update returns False."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "name": 'test-dynamic-group',
            "description": 'Test dynamic group',
            "matching_rule": "Any {instance.compartment.id = 'ocid1.compartment.oc1..test'}",
            "compartment_id": None,
            "dynamic_group_id": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        resource = _build_dynamic_group()

        from ansible_collections.oracle.oci.plugins.modules.oci_dynamic_group import needs_update
        assert not needs_update(module, resource)
