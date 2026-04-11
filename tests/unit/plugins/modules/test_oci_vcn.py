"""Unit tests for oracle.oci.oci_vcn module."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from unittest.mock import MagicMock, patch

import pytest


MODULE_PATH = "ansible_collections.oracle.oci.plugins.modules.oci_vcn"
AUTH_PATH = "ansible_collections.oracle.oci.plugins.module_utils.oci_auth"
RESOURCE_PATH = "ansible_collections.oracle.oci.plugins.module_utils.oci_resource"
WAIT_PATH = "ansible_collections.oracle.oci.plugins.module_utils.oci_wait"


def _build_vcn(
    vcn_id="ocid1.vcn.oc1..test1",
    compartment_id="ocid1.compartment.oc1..test",
    display_name="test-vcn",
    cidr_blocks=None,
    lifecycle_state="AVAILABLE",
    dns_label="testvcn",
):
    """Return a mock OCI VCN object."""
    vcn = MagicMock()
    vcn.id = vcn_id
    vcn.compartment_id = compartment_id
    vcn.display_name = display_name
    vcn.cidr_blocks = cidr_blocks or ["10.0.0.0/16"]
    vcn.lifecycle_state = lifecycle_state
    vcn.dns_label = dns_label
    vcn.freeform_tags = {}
    vcn.defined_tags = {}
    return vcn


@pytest.fixture
def vcn_create_args(module_args):
    """Module args for creating a VCN."""
    module_args.update({
        "compartment_id": "ocid1.compartment.oc1..test",
        "cidr_blocks": ["10.0.0.0/16"],
        "display_name": "test-vcn",
        "dns_label": "testvcn",
        "vcn_id": None,
    })
    return module_args


class TestOciVcnCreate:
    """Test VCN creation."""

    @patch(f"{WAIT_PATH}.wait_for_resource")
    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_create_vcn(self, mock_create_client, mock_wait, vcn_create_args):
        """Creating a VCN calls create_vcn and waits for AVAILABLE."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        provisioning_vcn = _build_vcn(lifecycle_state="PROVISIONING")
        mock_response = MagicMock()
        mock_response.data = provisioning_vcn
        mock_client.create_vcn.return_value = mock_response

        available_vcn = _build_vcn(lifecycle_state="AVAILABLE")
        mock_wait.return_value = available_vcn

        module = MagicMock()
        module.params = vcn_create_args
        module.check_mode = False

        from ansible_collections.oracle.oci.plugins.modules.oci_vcn import OciVcn
        oci_vcn = OciVcn(module)
        result = oci_vcn.create_resource()

        mock_client.create_vcn.assert_called_once()
        create_details = mock_client.create_vcn.call_args[0][0]
        assert create_details.compartment_id == "ocid1.compartment.oc1..test"
        assert create_details.cidr_blocks == ["10.0.0.0/16"]
        assert create_details.display_name == "test-vcn"
        assert result.lifecycle_state == "AVAILABLE"

    @patch(f"{WAIT_PATH}.wait_for_resource")
    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_create_vcn_with_dns_label(self, mock_create_client, mock_wait, vcn_create_args):
        """DNS label is passed through to CreateVcnDetails."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        mock_response = MagicMock()
        mock_response.data = _build_vcn(lifecycle_state="PROVISIONING")
        mock_client.create_vcn.return_value = mock_response
        mock_wait.return_value = _build_vcn()

        module = MagicMock()
        module.params = vcn_create_args
        module.check_mode = False

        from ansible_collections.oracle.oci.plugins.modules.oci_vcn import OciVcn
        oci_vcn = OciVcn(module)
        oci_vcn.create_resource()

        create_details = mock_client.create_vcn.call_args[0][0]
        assert create_details.dns_label == "testvcn"


class TestOciVcnDelete:
    """Test VCN deletion."""

    @patch(f"{WAIT_PATH}.wait_for_resource")
    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_delete_vcn(self, mock_create_client, mock_wait, module_args):
        """Deleting a VCN calls delete_vcn."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "vcn_id": "ocid1.vcn.oc1..test1",
            "state": "absent",
            "compartment_id": None,
            "cidr_blocks": None,
            "display_name": None,
            "dns_label": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False

        from ansible_collections.oracle.oci.plugins.modules.oci_vcn import OciVcn
        resource = _build_vcn()

        oci_vcn = OciVcn(module)
        oci_vcn.delete_resource(resource)

        mock_client.delete_vcn.assert_called_once_with(resource.id)

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_delete_vcn_already_gone(self, mock_create_client, module_args):
        """When VCN does not exist, get_resource returns None."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        import oci.exceptions
        mock_client.get_vcn.side_effect = oci.exceptions.ServiceError(
            status=404, code="NotFound", message="not found", headers={},
        )

        module_args.update({
            "vcn_id": "ocid1.vcn.oc1..doesnotexist",
            "state": "absent",
            "compartment_id": None,
            "cidr_blocks": None,
            "display_name": None,
            "dns_label": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False

        from ansible_collections.oracle.oci.plugins.modules.oci_vcn import OciVcn
        oci_vcn = OciVcn(module)
        result = oci_vcn.get_resource()
        assert result is None


class TestOciVcnUpdate:
    """Test VCN update."""

    @patch(f"{WAIT_PATH}.wait_for_resource")
    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_update_display_name(self, mock_create_client, mock_wait, module_args):
        """Updating display_name calls update_vcn."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "vcn_id": "ocid1.vcn.oc1..test1",
            "display_name": "renamed-vcn",
            "compartment_id": None,
            "cidr_blocks": None,
            "dns_label": None,
        })

        updated_vcn = _build_vcn(display_name="renamed-vcn")
        mock_wait.return_value = updated_vcn

        module = MagicMock()
        module.params = module_args
        module.check_mode = False

        from ansible_collections.oracle.oci.plugins.modules.oci_vcn import OciVcn
        resource = _build_vcn(display_name="old-name")

        oci_vcn = OciVcn(module)
        result = oci_vcn.update_resource(resource)

        mock_client.update_vcn.assert_called_once()
        assert mock_client.update_vcn.call_args[0][0] == resource.id
        assert result.display_name == "renamed-vcn"

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_no_update_when_display_name_matches(self, mock_create_client, module_args):
        """needs_update returns False when display_name matches."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "vcn_id": "ocid1.vcn.oc1..test1",
            "display_name": "same-name",
            "compartment_id": None,
            "cidr_blocks": None,
            "dns_label": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False

        from ansible_collections.oracle.oci.plugins.modules.oci_vcn import OciVcn
        resource = _build_vcn(display_name="same-name")

        oci_vcn = OciVcn(module)
        assert not oci_vcn.needs_update(resource)
