"""Unit tests for oracle.oci.oci_internet_gateway module."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from unittest.mock import MagicMock, patch

import pytest


MODULE_PATH = "ansible_collections.oracle.oci.plugins.modules.oci_internet_gateway"
AUTH_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_auth"
RESOURCE_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_resource"
WAIT_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_wait"


def _build_internet_gateway(
    display_name='test-igw',
    is_enabled=True,
):
    """Return a mock OCI internet_gateway object."""
    internet_gateway = MagicMock()
    internet_gateway.display_name = 'test-igw'
    internet_gateway.is_enabled = True
    internet_gateway.id = "ocid1.test.oc1..testresource"
    internet_gateway.compartment_id = "ocid1.compartment.oc1..test"
    internet_gateway.lifecycle_state = "AVAILABLE"
    internet_gateway.freeform_tags = {}
    internet_gateway.defined_tags = {}
    return internet_gateway


@pytest.fixture
def internet_gateway_create_args(module_args):
    """Module args for creating a internet_gateway."""
    module_args.update({
        "compartment_id": 'ocid1.compartment.oc1..test',
        "vcn_id": 'ocid1.vcn.oc1..test',
        "display_name": 'test-igw',
        "is_enabled": True,
    })
    return module_args


class TestOciInternetGatewayCreate:
    """Test internet_gateway creation."""

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_create_internet_gateway(self, mock_create_client, internet_gateway_create_args):
        """Creating a internet_gateway calls create_internet_gateway."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        created = _build_internet_gateway()
        mock_response = MagicMock()
        mock_response.data = created
        mock_client.create_internet_gateway.return_value = mock_response

        module = MagicMock()
        module.params = internet_gateway_create_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_internet_gateway import OciInternetGateway
        obj = OciInternetGateway(module)
        result = obj.create_resource()

        mock_client.create_internet_gateway.assert_called_once()


class TestOciInternetGatewayDelete:
    """Test internet_gateway deletion."""

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_delete_internet_gateway(self, mock_create_client, module_args):
        """Deleting a internet_gateway calls delete_internet_gateway."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "ig_id": "ocid1.test.oc1..testresource",
            "state": "absent",
            "vcn_id": None,
            "display_name": None,
            "is_enabled": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_internet_gateway import OciInternetGateway
        resource = _build_internet_gateway()

        obj = OciInternetGateway(module)
        obj.delete_resource(resource)

        mock_client.delete_internet_gateway.assert_called_once()

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_delete_internet_gateway_already_gone(self, mock_create_client, module_args):
        """When internet_gateway does not exist, get_resource returns None."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        import oci.exceptions
        mock_client.get_internet_gateway.side_effect = oci.exceptions.ServiceError(
            status=404, code="NotAuthorizedOrNotFound", message="not found", headers={},
        )

        module_args.update({
            "ig_id": "ocid1.test.oc1..testresource",
            "state": "absent",
            "vcn_id": None,
            "display_name": None,
            "is_enabled": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_internet_gateway import OciInternetGateway
        obj = OciInternetGateway(module)
        result = obj.get_resource()
        assert result is None


class TestOciInternetGatewayUpdate:
    """Test internet_gateway update."""

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_update_internet_gateway(self, mock_create_client, module_args):
        """Updating a internet_gateway calls update_internet_gateway."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "ig_id": "ocid1.test.oc1..testresource",
            "state": "absent",
            "vcn_id": None,
            "display_name": None,
            "is_enabled": None,
            "display_name": "updated-internet_gateway",
        })

        updated = _build_internet_gateway(display_name="updated-internet_gateway")
        mock_response = MagicMock()
        mock_response.data = updated
        mock_client.update_internet_gateway.return_value = mock_response

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_internet_gateway import OciInternetGateway
        resource = _build_internet_gateway()

        obj = OciInternetGateway(module)
        result = obj.update_resource(resource)

        mock_client.update_internet_gateway.assert_called_once()


class TestOciInternetGatewayIdempotent:
    """Test idempotent behavior when no change is needed."""

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_no_change_needed(self, mock_create_client, module_args):
        """When current state matches desired state, needs_update returns False."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "display_name": 'test-igw',
            "is_enabled": True,
            "vcn_id": None,
            "compartment_id": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_internet_gateway import OciInternetGateway
        resource = _build_internet_gateway()

        obj = OciInternetGateway(module)
        assert not obj.needs_update(resource)
