"""Unit tests for oracle.oci.oci_nsg module."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from unittest.mock import MagicMock, patch

import pytest


MODULE_PATH = "ansible_collections.oracle.oci.plugins.modules.oci_nsg"
AUTH_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_auth"
RESOURCE_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_resource"
WAIT_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_wait"


def _build_nsg(
    display_name='test-nsg',
):
    """Return a mock OCI nsg object."""
    nsg = MagicMock()
    nsg.display_name = 'test-nsg'
    nsg.id = "ocid1.test.oc1..testresource"
    nsg.compartment_id = "ocid1.compartment.oc1..test"
    nsg.lifecycle_state = "AVAILABLE"
    nsg.freeform_tags = {}
    nsg.defined_tags = {}
    return nsg


@pytest.fixture
def nsg_create_args(module_args):
    """Module args for creating a nsg."""
    module_args.update({
        "compartment_id": 'ocid1.compartment.oc1..test',
        "vcn_id": 'ocid1.vcn.oc1..test',
        "display_name": 'test-nsg',
    })
    return module_args


class TestOciNsgCreate:
    """Test nsg creation."""

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_create_nsg(self, mock_create_client, nsg_create_args):
        """Creating a nsg calls create_network_security_group."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        created = _build_nsg()
        mock_response = MagicMock()
        mock_response.data = created
        mock_client.create_network_security_group.return_value = mock_response

        module = MagicMock()
        module.params = nsg_create_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_nsg import OciNsg
        obj = OciNsg(module)
        result = obj.create_resource()

        mock_client.create_network_security_group.assert_called_once()


class TestOciNsgDelete:
    """Test nsg deletion."""

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_delete_nsg(self, mock_create_client, module_args):
        """Deleting a nsg calls delete_network_security_group."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "nsg_id": "ocid1.test.oc1..testresource",
            "state": "absent",
            "vcn_id": None,
            "display_name": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_nsg import OciNsg
        resource = _build_nsg()

        obj = OciNsg(module)
        obj.delete_resource(resource)

        mock_client.delete_network_security_group.assert_called_once()

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_delete_nsg_already_gone(self, mock_create_client, module_args):
        """When nsg does not exist, get_resource returns None."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        import oci.exceptions
        mock_client.get_network_security_group.side_effect = oci.exceptions.ServiceError(
            status=404, code="NotAuthorizedOrNotFound", message="not found", headers={},
        )

        module_args.update({
            "nsg_id": "ocid1.test.oc1..testresource",
            "state": "absent",
            "vcn_id": None,
            "display_name": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_nsg import OciNsg
        obj = OciNsg(module)
        result = obj.get_resource()
        assert result is None


class TestOciNsgUpdate:
    """Test nsg update."""

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_update_nsg(self, mock_create_client, module_args):
        """Updating a nsg calls update_network_security_group."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "nsg_id": "ocid1.test.oc1..testresource",
            "state": "absent",
            "vcn_id": None,
            "display_name": None,
            "display_name": "updated-nsg",
        })

        updated = _build_nsg(display_name="updated-nsg")
        mock_response = MagicMock()
        mock_response.data = updated
        mock_client.update_network_security_group.return_value = mock_response

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_nsg import OciNsg
        resource = _build_nsg()

        obj = OciNsg(module)
        result = obj.update_resource(resource)

        mock_client.update_network_security_group.assert_called_once()


class TestOciNsgIdempotent:
    """Test idempotent behavior when no change is needed."""

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_no_change_needed(self, mock_create_client, module_args):
        """When current state matches desired state, needs_update returns False."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "display_name": 'test-nsg',
            "vcn_id": None,
            "compartment_id": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_nsg import OciNsg
        resource = _build_nsg()

        obj = OciNsg(module)
        assert not obj.needs_update(resource)
