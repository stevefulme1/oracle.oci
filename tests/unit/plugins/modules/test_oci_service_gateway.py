"""Unit tests for oracle.oci.oci_service_gateway module."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from unittest.mock import MagicMock, patch

import pytest


MODULE_PATH = "ansible_collections.oracle.oci.plugins.modules.oci_service_gateway"
AUTH_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_auth"
RESOURCE_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_resource"
WAIT_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_wait"


def _build_service_gateway(
    display_name='test-sgw',
    services=[],
):
    """Return a mock OCI service_gateway object."""
    service_gateway = MagicMock()
    service_gateway.display_name = 'test-sgw'
    service_gateway.services = []
    service_gateway.id = "ocid1.test.oc1..testresource"
    service_gateway.compartment_id = "ocid1.compartment.oc1..test"
    service_gateway.lifecycle_state = "AVAILABLE"
    service_gateway.freeform_tags = {}
    service_gateway.defined_tags = {}
    return service_gateway


@pytest.fixture
def service_gateway_create_args(module_args):
    """Module args for creating a service_gateway."""
    module_args.update({
        "compartment_id": 'ocid1.compartment.oc1..test',
        "vcn_id": 'ocid1.vcn.oc1..test',
        "display_name": 'test-sgw',
        "services": [],
    })
    return module_args


class TestOciServiceGatewayCreate:
    """Test service_gateway creation."""

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_create_service_gateway(self, mock_create_client, service_gateway_create_args):
        """Creating a service_gateway calls create_service_gateway."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        created = _build_service_gateway()
        mock_response = MagicMock()
        mock_response.data = created
        mock_client.create_service_gateway.return_value = mock_response

        module = MagicMock()
        module.params = service_gateway_create_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_service_gateway import OciServiceGateway
        obj = OciServiceGateway(module)
        result = obj.create_resource()

        mock_client.create_service_gateway.assert_called_once()


class TestOciServiceGatewayDelete:
    """Test service_gateway deletion."""

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_delete_service_gateway(self, mock_create_client, module_args):
        """Deleting a service_gateway calls delete_service_gateway."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "service_gateway_id": "ocid1.test.oc1..testresource",
            "state": "absent",
            "vcn_id": None,
            "display_name": None,
            "services": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_service_gateway import OciServiceGateway
        resource = _build_service_gateway()

        obj = OciServiceGateway(module)
        obj.delete_resource(resource)

        mock_client.delete_service_gateway.assert_called_once()

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_delete_service_gateway_already_gone(self, mock_create_client, module_args):
        """When service_gateway does not exist, get_resource returns None."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        import oci.exceptions
        mock_client.get_service_gateway.side_effect = oci.exceptions.ServiceError(
            status=404, code="NotAuthorizedOrNotFound", message="not found", headers={},
        )

        module_args.update({
            "service_gateway_id": "ocid1.test.oc1..testresource",
            "state": "absent",
            "vcn_id": None,
            "display_name": None,
            "services": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_service_gateway import OciServiceGateway
        obj = OciServiceGateway(module)
        result = obj.get_resource()
        assert result is None


class TestOciServiceGatewayUpdate:
    """Test service_gateway update."""

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_update_service_gateway(self, mock_create_client, module_args):
        """Updating a service_gateway calls update_service_gateway."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "service_gateway_id": "ocid1.test.oc1..testresource",
            "state": "absent",
            "vcn_id": None,
            "display_name": None,
            "services": None,
            "display_name": "updated-service_gateway",
        })

        updated = _build_service_gateway(display_name="updated-service_gateway")
        mock_response = MagicMock()
        mock_response.data = updated
        mock_client.update_service_gateway.return_value = mock_response

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_service_gateway import OciServiceGateway
        resource = _build_service_gateway()

        obj = OciServiceGateway(module)
        result = obj.update_resource(resource)

        mock_client.update_service_gateway.assert_called_once()


class TestOciServiceGatewayIdempotent:
    """Test idempotent behavior when no change is needed."""

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_no_change_needed(self, mock_create_client, module_args):
        """When current state matches desired state, needs_update returns False."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "display_name": 'test-sgw',
            "services": [],
            "vcn_id": None,
            "compartment_id": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_service_gateway import OciServiceGateway
        resource = _build_service_gateway()

        obj = OciServiceGateway(module)
        assert not obj.needs_update(resource)
