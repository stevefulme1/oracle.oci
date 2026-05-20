"""Unit tests for oracle.oci.oci_dns_zone module."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from unittest.mock import MagicMock, patch

import pytest


MODULE_PATH = "ansible_collections.oracle.oci.plugins.modules.oci_dns_zone"
AUTH_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_auth"
RESOURCE_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_resource"
WAIT_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_wait"


def _build_dns_zone(
    name='test.example.com',
    zone_type='PRIMARY',
):
    """Return a mock OCI dns_zone object."""
    dns_zone = MagicMock()
    dns_zone.name = 'test.example.com'
    dns_zone.zone_type = 'PRIMARY'
    dns_zone.id = "ocid1.test.oc1..testresource"
    dns_zone.compartment_id = "ocid1.compartment.oc1..test"
    dns_zone.lifecycle_state = "AVAILABLE"
    dns_zone.freeform_tags = {}
    dns_zone.defined_tags = {}
    return dns_zone


@pytest.fixture
def dns_zone_create_args(module_args):
    """Module args for creating a dns_zone."""
    module_args.update({
        "compartment_id": 'ocid1.compartment.oc1..test',
        "name": 'test.example.com',
        "zone_type": 'PRIMARY',
    })
    return module_args


class TestOciDnsZoneCreate:
    """Test dns_zone creation."""

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_create_dns_zone(self, mock_create_client, dns_zone_create_args):
        """Creating a dns_zone calls create_zone."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        created = _build_dns_zone()
        mock_response = MagicMock()
        mock_response.data = created
        mock_client.create_zone.return_value = mock_response

        module = MagicMock()
        module.params = dns_zone_create_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_dns_zone import OciDnsZone
        obj = OciDnsZone(module)
        result = obj.create_resource()

        mock_client.create_zone.assert_called_once()


class TestOciDnsZoneDelete:
    """Test dns_zone deletion."""

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_delete_dns_zone(self, mock_create_client, module_args):
        """Deleting a dns_zone calls delete_zone."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "dns_zone_id": "ocid1.test.oc1..testresource",
            "state": "absent",
            "name": None,
            "zone_type": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_dns_zone import OciDnsZone
        resource = _build_dns_zone()

        obj = OciDnsZone(module)
        obj.delete_resource(resource)

        mock_client.delete_zone.assert_called_once()

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_delete_dns_zone_already_gone(self, mock_create_client, module_args):
        """When dns_zone does not exist, get_resource returns None."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        import oci.exceptions
        mock_client.get_zone.side_effect = oci.exceptions.ServiceError(
            status=404, code="NotAuthorizedOrNotFound", message="not found", headers={},
        )

        module_args.update({
            "dns_zone_id": "ocid1.test.oc1..testresource",
            "state": "absent",
            "name": None,
            "zone_type": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_dns_zone import OciDnsZone
        obj = OciDnsZone(module)
        result = obj.get_resource()
        assert result is None


class TestOciDnsZoneUpdate:
    """Test dns_zone update."""

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_update_dns_zone(self, mock_create_client, module_args):
        """Updating a dns_zone calls update_zone."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "dns_zone_id": "ocid1.test.oc1..testresource",
            "state": "absent",
            "name": None,
            "zone_type": None,
            "name": "updated-dns_zone",
        })

        updated = _build_dns_zone(name="updated-dns_zone")
        mock_response = MagicMock()
        mock_response.data = updated
        mock_client.update_zone.return_value = mock_response

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_dns_zone import OciDnsZone
        resource = _build_dns_zone()

        obj = OciDnsZone(module)
        result = obj.update_resource(resource)

        mock_client.update_zone.assert_called_once()


class TestOciDnsZoneIdempotent:
    """Test idempotent behavior when no change is needed."""

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_no_change_needed(self, mock_create_client, module_args):
        """When current state matches desired state, needs_update returns False."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "name": 'test.example.com',
            "zone_type": 'PRIMARY',
            "compartment_id": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_dns_zone import OciDnsZone
        resource = _build_dns_zone()

        obj = OciDnsZone(module)
        assert not obj.needs_update(resource)
