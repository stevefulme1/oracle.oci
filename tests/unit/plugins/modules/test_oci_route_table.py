"""Unit tests for oracle.oci.oci_route_table module."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from unittest.mock import MagicMock, patch

import pytest


MODULE_PATH = "ansible_collections.oracle.oci.plugins.modules.oci_route_table"
AUTH_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_auth"
RESOURCE_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_resource"
WAIT_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_wait"


def _build_route_table(
    display_name='test-rt',
    route_rules=[],
):
    """Return a mock OCI route_table object."""
    route_table = MagicMock()
    route_table.display_name = 'test-rt'
    route_table.route_rules = []
    route_table.id = "ocid1.test.oc1..testresource"
    route_table.compartment_id = "ocid1.compartment.oc1..test"
    route_table.lifecycle_state = "AVAILABLE"
    route_table.freeform_tags = {}
    route_table.defined_tags = {}
    return route_table


@pytest.fixture
def route_table_create_args(module_args):
    """Module args for creating a route_table."""
    module_args.update({
        "compartment_id": 'ocid1.compartment.oc1..test',
        "vcn_id": 'ocid1.vcn.oc1..test',
        "display_name": 'test-rt',
        "route_rules": [],
    })
    return module_args


class TestOciRouteTableCreate:
    """Test route_table creation."""

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_create_route_table(self, mock_create_client, route_table_create_args):
        """Creating a route_table calls create_route_table."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        created = _build_route_table()
        mock_response = MagicMock()
        mock_response.data = created
        mock_client.create_route_table.return_value = mock_response

        module = MagicMock()
        module.params = route_table_create_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_route_table import OciRouteTable
        obj = OciRouteTable(module)
        result = obj.create_resource()

        mock_client.create_route_table.assert_called_once()


class TestOciRouteTableDelete:
    """Test route_table deletion."""

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_delete_route_table(self, mock_create_client, module_args):
        """Deleting a route_table calls delete_route_table."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "route_table_id": "ocid1.test.oc1..testresource",
            "state": "absent",
            "vcn_id": None,
            "display_name": None,
            "route_rules": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_route_table import OciRouteTable
        resource = _build_route_table()

        obj = OciRouteTable(module)
        obj.delete_resource(resource)

        mock_client.delete_route_table.assert_called_once()

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_delete_route_table_already_gone(self, mock_create_client, module_args):
        """When route_table does not exist, get_resource returns None."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        import oci.exceptions
        mock_client.get_route_table.side_effect = oci.exceptions.ServiceError(
            status=404, code="NotAuthorizedOrNotFound", message="not found", headers={},
        )

        module_args.update({
            "route_table_id": "ocid1.test.oc1..testresource",
            "state": "absent",
            "vcn_id": None,
            "display_name": None,
            "route_rules": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_route_table import OciRouteTable
        obj = OciRouteTable(module)
        result = obj.get_resource()
        assert result is None


class TestOciRouteTableUpdate:
    """Test route_table update."""

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_update_route_table(self, mock_create_client, module_args):
        """Updating a route_table calls update_route_table."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "route_table_id": "ocid1.test.oc1..testresource",
            "state": "absent",
            "vcn_id": None,
            "display_name": None,
            "route_rules": None,
            "display_name": "updated-route_table",
        })

        updated = _build_route_table(display_name="updated-route_table")
        mock_response = MagicMock()
        mock_response.data = updated
        mock_client.update_route_table.return_value = mock_response

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_route_table import OciRouteTable
        resource = _build_route_table()

        obj = OciRouteTable(module)
        result = obj.update_resource(resource)

        mock_client.update_route_table.assert_called_once()


class TestOciRouteTableIdempotent:
    """Test idempotent behavior when no change is needed."""

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_no_change_needed(self, mock_create_client, module_args):
        """When current state matches desired state, needs_update returns False."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "display_name": 'test-rt',
            "route_rules": [],
            "vcn_id": None,
            "compartment_id": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_route_table import OciRouteTable
        resource = _build_route_table()

        obj = OciRouteTable(module)
        assert not obj.needs_update(resource)
