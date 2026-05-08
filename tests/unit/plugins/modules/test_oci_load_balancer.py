"""Unit tests for oracle.oci.oci_load_balancer module."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from unittest.mock import MagicMock, patch

import pytest


MODULE_PATH = "ansible_collections.oracle.oci.plugins.modules.oci_load_balancer"
AUTH_PATH = "ansible_collections.oracle.oci.plugins.module_utils.oci_auth"
RESOURCE_PATH = "ansible_collections.oracle.oci.plugins.module_utils.oci_resource"
WAIT_PATH = "ansible_collections.oracle.oci.plugins.module_utils.oci_wait"


def _build_load_balancer(
    load_balancer_id="ocid1.loadbalancer.oc1..test1",
    display_name="test-lb",
    lifecycle_state="ACTIVE",
    shape_name="flexible",
    compartment_id="ocid1.compartment.oc1..test",
    subnet_ids=None,
    is_private=False,
    ip_addresses=None,
):
    """Return a mock OCI load balancer object."""
    lb = MagicMock()
    lb.id = load_balancer_id
    lb.display_name = display_name
    lb.lifecycle_state = lifecycle_state
    lb.shape_name = shape_name
    lb.compartment_id = compartment_id
    lb.subnet_ids = subnet_ids or ["ocid1.subnet.oc1.phx.test1"]
    lb.is_private = is_private
    lb.ip_addresses = ip_addresses or []
    lb.freeform_tags = {}
    lb.defined_tags = {}
    return lb


@pytest.fixture
def lb_create_args(module_args):
    """Module args for creating a load balancer."""
    module_args.update({
        "compartment_id": "ocid1.compartment.oc1..test",
        "display_name": "test-lb",
        "shape_name": "flexible",
        "subnet_ids": ["ocid1.subnet.oc1.phx.test1"],
        "is_private": False,
        "load_balancer_id": None,
    })
    return module_args


class TestOciLoadBalancerCreate:
    """Test load balancer creation."""

    @patch(f"{WAIT_PATH}.wait_for_work_request")
    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_create_load_balancer(self, mock_create_client, mock_wait_wr, lb_create_args):
        """Creating a load balancer calls create_load_balancer."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        mock_response = MagicMock()
        mock_response.headers = {"opc-work-request-id": "wr-123"}
        mock_client.create_load_balancer.return_value = mock_response

        active_lb = _build_load_balancer(lifecycle_state="ACTIVE")
        mock_client.list_load_balancers.return_value = MagicMock(data=[active_lb])

        module = MagicMock()
        module.params = lb_create_args
        module.check_mode = False

        from ansible_collections.oracle.oci.plugins.modules.oci_load_balancer import OciLoadBalancer
        oci_lb = OciLoadBalancer(module)
        result = oci_lb.create_resource()

        mock_client.create_load_balancer.assert_called_once()
        create_details = mock_client.create_load_balancer.call_args[0][0]
        assert create_details.compartment_id == "ocid1.compartment.oc1..test"
        assert create_details.display_name == "test-lb"
        assert create_details.shape_name == "flexible"
        assert create_details.subnet_ids == ["ocid1.subnet.oc1.phx.test1"]
        assert result.lifecycle_state == "ACTIVE"

    @patch(f"{WAIT_PATH}.wait_for_work_request")
    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_create_private_load_balancer(self, mock_create_client, mock_wait_wr, lb_create_args):
        """Private flag is passed through to create details."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        lb_create_args["is_private"] = True

        mock_response = MagicMock()
        mock_response.headers = {"opc-work-request-id": "wr-456"}
        mock_client.create_load_balancer.return_value = mock_response

        private_lb = _build_load_balancer(is_private=True)
        mock_client.list_load_balancers.return_value = MagicMock(data=[private_lb])

        module = MagicMock()
        module.params = lb_create_args
        module.check_mode = False

        from ansible_collections.oracle.oci.plugins.modules.oci_load_balancer import OciLoadBalancer
        oci_lb = OciLoadBalancer(module)
        oci_lb.create_resource()

        create_details = mock_client.create_load_balancer.call_args[0][0]
        assert create_details.is_private is True


class TestOciLoadBalancerDelete:
    """Test load balancer deletion."""

    @patch(f"{WAIT_PATH}.wait_for_work_request")
    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_delete_load_balancer(self, mock_create_client, mock_wait_wr, module_args):
        """Deleting a load balancer calls delete_load_balancer."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        mock_response = MagicMock()
        mock_response.headers = {"opc-work-request-id": "wr-del-123"}
        mock_client.delete_load_balancer.return_value = mock_response

        module_args.update({
            "load_balancer_id": "ocid1.loadbalancer.oc1..test1",
            "state": "absent",
            "compartment_id": None,
            "display_name": None,
            "shape_name": None,
            "subnet_ids": None,
            "is_private": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False

        from ansible_collections.oracle.oci.plugins.modules.oci_load_balancer import OciLoadBalancer
        resource = _build_load_balancer()

        oci_lb = OciLoadBalancer(module)
        oci_lb.delete_resource(resource)

        mock_client.delete_load_balancer.assert_called_once_with(resource.id)

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_delete_load_balancer_already_gone(self, mock_create_client, module_args):
        """When load balancer does not exist, get_resource returns None."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        import oci.exceptions
        mock_client.get_load_balancer.side_effect = oci.exceptions.ServiceError(
            status=404, code="NotFound", message="not found", headers={},
        )

        module_args.update({
            "load_balancer_id": "ocid1.loadbalancer.oc1..doesnotexist",
            "state": "absent",
            "compartment_id": None,
            "display_name": None,
            "shape_name": None,
            "subnet_ids": None,
            "is_private": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False

        from ansible_collections.oracle.oci.plugins.modules.oci_load_balancer import OciLoadBalancer
        oci_lb = OciLoadBalancer(module)
        result = oci_lb.get_resource()
        assert result is None


class TestOciLoadBalancerUpdate:
    """Test load balancer update."""

    @patch(f"{WAIT_PATH}.wait_for_work_request")
    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_update_display_name(self, mock_create_client, mock_wait_wr, module_args):
        """Updating display_name calls update_load_balancer."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "load_balancer_id": "ocid1.loadbalancer.oc1..test1",
            "display_name": "renamed-lb",
            "compartment_id": None,
            "shape_name": None,
            "subnet_ids": None,
            "is_private": None,
        })

        mock_response = MagicMock()
        mock_response.headers = {"opc-work-request-id": "wr-upd-123"}
        mock_client.update_load_balancer.return_value = mock_response

        updated_lb = _build_load_balancer(display_name="renamed-lb")
        mock_client.get_load_balancer.return_value = MagicMock(data=updated_lb)

        module = MagicMock()
        module.params = module_args
        module.check_mode = False

        from ansible_collections.oracle.oci.plugins.modules.oci_load_balancer import OciLoadBalancer
        resource = _build_load_balancer(display_name="old-name")

        oci_lb = OciLoadBalancer(module)
        result = oci_lb.update_resource(resource)

        mock_client.update_load_balancer.assert_called_once()
        assert mock_client.update_load_balancer.call_args[0][0] == resource.id


class TestOciLoadBalancerIdempotent:
    """Test idempotent behavior when no change is needed."""

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_no_change_needed(self, mock_create_client, module_args):
        """When current state matches desired state, needs_update returns False."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "load_balancer_id": "ocid1.loadbalancer.oc1..test1",
            "display_name": "test-lb",
            "compartment_id": None,
            "shape_name": None,
            "subnet_ids": None,
            "is_private": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False

        from ansible_collections.oracle.oci.plugins.modules.oci_load_balancer import OciLoadBalancer
        resource = _build_load_balancer(display_name="test-lb")

        oci_lb = OciLoadBalancer(module)
        assert not oci_lb.needs_update(resource)

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_change_needed_when_display_name_differs(self, mock_create_client, module_args):
        """When display_name differs from desired, needs_update returns True."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "load_balancer_id": "ocid1.loadbalancer.oc1..test1",
            "display_name": "new-name",
            "compartment_id": None,
            "shape_name": None,
            "subnet_ids": None,
            "is_private": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False

        from ansible_collections.oracle.oci.plugins.modules.oci_load_balancer import OciLoadBalancer
        resource = _build_load_balancer(display_name="old-name")

        oci_lb = OciLoadBalancer(module)
        assert oci_lb.needs_update(resource)
