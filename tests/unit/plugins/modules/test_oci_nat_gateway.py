"""Unit tests for oracle.oci.oci_nat_gateway module."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from unittest.mock import MagicMock, patch

import pytest


MODULE_PATH = "ansible_collections.oracle.oci.plugins.modules.oci_nat_gateway"
AUTH_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_auth"
RESOURCE_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_resource"
WAIT_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_wait"


def _build_nat_gateway(
    display_name='test-nat-gw',
    block_traffic=False,
):
    """Return a mock OCI nat_gateway object."""
    nat_gateway = MagicMock()
    nat_gateway.display_name = 'test-nat-gw'
    nat_gateway.block_traffic = False
    nat_gateway.id = "ocid1.test.oc1..testresource"
    nat_gateway.compartment_id = "ocid1.compartment.oc1..test"
    nat_gateway.lifecycle_state = "AVAILABLE"
    nat_gateway.freeform_tags = {}
    nat_gateway.defined_tags = {}
    return nat_gateway


@pytest.fixture
def nat_gateway_create_args(module_args):
    """Module args for creating a nat_gateway."""
    module_args.update({
        "compartment_id": 'ocid1.compartment.oc1..test',
        "vcn_id": 'ocid1.vcn.oc1..test',
        "display_name": 'test-nat-gw',
        "block_traffic": False,
    })
    return module_args


class TestOciNatGatewayCreate:
    """Test nat_gateway creation."""

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_create_nat_gateway(self, mock_create_client, nat_gateway_create_args):
        """Creating a nat_gateway calls create_nat_gateway."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        created = _build_nat_gateway()
        mock_response = MagicMock()
        mock_response.data = created
        mock_client.create_nat_gateway.return_value = mock_response

        module = MagicMock()
        module.params = nat_gateway_create_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_nat_gateway import OciNatGateway
        obj = OciNatGateway(module)
        result = obj.create_resource()

        mock_client.create_nat_gateway.assert_called_once()


class TestOciNatGatewayDelete:
    """Test nat_gateway deletion."""

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_delete_nat_gateway(self, mock_create_client, module_args):
        """Deleting a nat_gateway calls delete_nat_gateway."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "nat_gateway_id": "ocid1.test.oc1..testresource",
            "state": "absent",
            "vcn_id": None,
            "display_name": None,
            "block_traffic": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_nat_gateway import OciNatGateway
        resource = _build_nat_gateway()

        obj = OciNatGateway(module)
        obj.delete_resource(resource)

        mock_client.delete_nat_gateway.assert_called_once()

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_delete_nat_gateway_already_gone(self, mock_create_client, module_args):
        """When nat_gateway does not exist, get_resource returns None."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        import oci.exceptions
        mock_client.get_nat_gateway.side_effect = oci.exceptions.ServiceError(
            status=404, code="NotAuthorizedOrNotFound", message="not found", headers={},
        )

        module_args.update({
            "nat_gateway_id": "ocid1.test.oc1..testresource",
            "state": "absent",
            "vcn_id": None,
            "display_name": None,
            "block_traffic": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_nat_gateway import OciNatGateway
        obj = OciNatGateway(module)
        result = obj.get_resource()
        assert result is None


class TestOciNatGatewayUpdate:
    """Test nat_gateway update."""

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_update_nat_gateway(self, mock_create_client, module_args):
        """Updating a nat_gateway calls update_nat_gateway."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "nat_gateway_id": "ocid1.test.oc1..testresource",
            "state": "absent",
            "vcn_id": None,
            "display_name": None,
            "block_traffic": None,
            "display_name": "updated-nat_gateway",
        })

        updated = _build_nat_gateway(display_name="updated-nat_gateway")
        mock_response = MagicMock()
        mock_response.data = updated
        mock_client.update_nat_gateway.return_value = mock_response

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_nat_gateway import OciNatGateway
        resource = _build_nat_gateway()

        obj = OciNatGateway(module)
        result = obj.update_resource(resource)

        mock_client.update_nat_gateway.assert_called_once()


class TestOciNatGatewayIdempotent:
    """Test idempotent behavior when no change is needed."""

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_no_change_needed(self, mock_create_client, module_args):
        """When current state matches desired state, needs_update returns False."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "display_name": 'test-nat-gw',
            "block_traffic": False,
            "vcn_id": None,
            "compartment_id": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_nat_gateway import OciNatGateway
        resource = _build_nat_gateway()

        obj = OciNatGateway(module)
        assert not obj.needs_update(resource)
