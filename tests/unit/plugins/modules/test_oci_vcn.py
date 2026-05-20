"""Unit tests for oracle.oci.oci_vcn module."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from unittest.mock import MagicMock, patch

import pytest


MODULE_PATH = "ansible_collections.oracle.oci.plugins.modules.oci_vcn"
AUTH_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_auth"
RESOURCE_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_resource"
WAIT_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_wait"


def _build_vcn(
    display_name='test-vcn',
    cidr_blocks=['10.0.0.0/16'],
    dns_label='testvcn',
):
    """Return a mock OCI vcn object."""
    vcn = MagicMock()
    vcn.display_name = 'test-vcn'
    vcn.cidr_blocks = ['10.0.0.0/16']
    vcn.dns_label = 'testvcn'
    vcn.id = "ocid1.test.oc1..testresource"
    vcn.compartment_id = "ocid1.compartment.oc1..test"
    vcn.lifecycle_state = "AVAILABLE"
    vcn.freeform_tags = {}
    vcn.defined_tags = {}
    return vcn


@pytest.fixture
def vcn_create_args(module_args):
    """Module args for creating a vcn."""
    module_args.update({
        "compartment_id": 'ocid1.compartment.oc1..test',
        "cidr_blocks": ['10.0.0.0/16'],
        "display_name": 'test-vcn',
        "dns_label": 'testvcn',
    })
    return module_args


class TestOciVcnCreate:
    """Test vcn creation."""

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_create_vcn(self, mock_create_client, vcn_create_args):
        """Creating a vcn calls create_vcn."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        created = _build_vcn()
        mock_response = MagicMock()
        mock_response.data = created
        mock_client.create_vcn.return_value = mock_response

        module = MagicMock()
        module.params = vcn_create_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_vcn import OciVcn
        obj = OciVcn(module)
        result = obj.create_resource()

        mock_client.create_vcn.assert_called_once()


class TestOciVcnDelete:
    """Test vcn deletion."""

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_delete_vcn(self, mock_create_client, module_args):
        """Deleting a vcn calls delete_vcn."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "vcn_id": "ocid1.test.oc1..testresource",
            "state": "absent",
            "cidr_blocks": None,
            "display_name": None,
            "dns_label": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_vcn import OciVcn
        resource = _build_vcn()

        obj = OciVcn(module)
        obj.delete_resource(resource)

        mock_client.delete_vcn.assert_called_once()

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_delete_vcn_already_gone(self, mock_create_client, module_args):
        """When vcn does not exist, get_resource returns None."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        import oci.exceptions
        mock_client.get_vcn.side_effect = oci.exceptions.ServiceError(
            status=404, code="NotAuthorizedOrNotFound", message="not found", headers={},
        )

        module_args.update({
            "vcn_id": "ocid1.test.oc1..testresource",
            "state": "absent",
            "cidr_blocks": None,
            "display_name": None,
            "dns_label": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_vcn import OciVcn
        obj = OciVcn(module)
        result = obj.get_resource()
        assert result is None


class TestOciVcnUpdate:
    """Test vcn update."""

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_update_vcn(self, mock_create_client, module_args):
        """Updating a vcn calls update_vcn."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "vcn_id": "ocid1.test.oc1..testresource",
            "state": "absent",
            "cidr_blocks": None,
            "display_name": None,
            "dns_label": None,
            "display_name": "updated-vcn",
        })

        updated = _build_vcn(display_name="updated-vcn")
        mock_response = MagicMock()
        mock_response.data = updated
        mock_client.update_vcn.return_value = mock_response

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_vcn import OciVcn
        resource = _build_vcn()

        obj = OciVcn(module)
        result = obj.update_resource(resource)

        mock_client.update_vcn.assert_called_once()


class TestOciVcnIdempotent:
    """Test idempotent behavior when no change is needed."""

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_no_change_needed(self, mock_create_client, module_args):
        """When current state matches desired state, needs_update returns False."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "display_name": 'test-vcn',
            "cidr_blocks": ['10.0.0.0/16'],
            "dns_label": 'testvcn',
            "compartment_id": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_vcn import OciVcn
        resource = _build_vcn()

        obj = OciVcn(module)
        assert not obj.needs_update(resource)
