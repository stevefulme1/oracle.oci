"""Unit tests for oracle.oci.plugins.module_utils.oci_wait."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from unittest.mock import MagicMock, patch, call
import time

import pytest

import oci.exceptions


WAIT_PATH = "ansible_collections.oracle.oci.plugins.module_utils.oci_wait"


class TestWaitForResource:
    """Test wait_for_resource() polling behavior."""

    @patch(f"{WAIT_PATH}.time")
    def test_returns_when_target_state_reached(self, mock_time):
        """Returns the resource when lifecycle_state reaches target."""
        mock_time.monotonic.side_effect = [0.0, 1.0]

        resource = MagicMock()
        resource.lifecycle_state = "AVAILABLE"

        get_fn = MagicMock()
        get_fn.return_value.data = resource

        module = MagicMock()
        module.params = {"wait": True, "wait_timeout": 1200, "wait_interval": 30}

        from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import wait_for_resource
        result = wait_for_resource(module, get_fn, "ocid1.test", {"AVAILABLE"})

        assert result is resource
        get_fn.assert_called_once_with("ocid1.test")

    @patch(f"{WAIT_PATH}.time")
    def test_returns_immediately_when_wait_false(self, mock_time):
        """When wait=False, returns the first get result without polling."""
        resource = MagicMock()
        resource.lifecycle_state = "PROVISIONING"

        get_fn = MagicMock()
        get_fn.return_value.data = resource

        module = MagicMock()
        module.params = {"wait": False, "wait_timeout": 1200, "wait_interval": 30}

        from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import wait_for_resource
        result = wait_for_resource(module, get_fn, "ocid1.test", {"AVAILABLE"})

        assert result is resource

    @patch(f"{WAIT_PATH}.time")
    def test_polls_until_target_state(self, mock_time):
        """Polls multiple times until target state is reached."""
        mock_time.monotonic.side_effect = [0.0, 10.0, 20.0, 30.0]
        mock_time.sleep = MagicMock()

        provisioning = MagicMock()
        provisioning.lifecycle_state = "PROVISIONING"

        available = MagicMock()
        available.lifecycle_state = "AVAILABLE"

        get_fn = MagicMock()
        get_fn.return_value.data = provisioning
        # Second call returns available
        get_fn.side_effect = [
            MagicMock(data=provisioning),
            MagicMock(data=available),
        ]

        module = MagicMock()
        module.params = {"wait": True, "wait_timeout": 1200, "wait_interval": 30}

        from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import wait_for_resource
        result = wait_for_resource(module, get_fn, "ocid1.test", {"AVAILABLE"})

        assert result.lifecycle_state == "AVAILABLE"
        assert get_fn.call_count == 2

    @patch(f"{WAIT_PATH}.time")
    def test_fails_on_failure_state(self, mock_time):
        """Calls fail_json when resource enters a failure state."""
        mock_time.monotonic.side_effect = [0.0, 1.0]

        failed = MagicMock()
        failed.lifecycle_state = "FAILED"

        get_fn = MagicMock()
        get_fn.return_value.data = failed

        module = MagicMock()
        module.params = {"wait": True, "wait_timeout": 1200, "wait_interval": 30}
        module.fail_json.side_effect = SystemExit(1)

        from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import wait_for_resource
        with pytest.raises(SystemExit):
            wait_for_resource(module, get_fn, "ocid1.test", {"AVAILABLE"})

        module.fail_json.assert_called_once()
        assert "failure state" in module.fail_json.call_args[1]["msg"]

    @patch(f"{WAIT_PATH}.time")
    def test_timeout(self, mock_time):
        """Calls fail_json when timeout is exceeded."""
        mock_time.monotonic.side_effect = [0.0, 1300.0]
        mock_time.sleep = MagicMock()

        provisioning = MagicMock()
        provisioning.lifecycle_state = "PROVISIONING"

        get_fn = MagicMock()
        get_fn.return_value.data = provisioning

        module = MagicMock()
        module.params = {"wait": True, "wait_timeout": 1200, "wait_interval": 30}
        module.fail_json.side_effect = SystemExit(1)

        from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import wait_for_resource
        with pytest.raises(SystemExit):
            wait_for_resource(module, get_fn, "ocid1.test", {"AVAILABLE"})

        module.fail_json.assert_called_once()
        assert "Timed out" in module.fail_json.call_args[1]["msg"]

    @patch(f"{WAIT_PATH}.time")
    def test_404_returns_none_for_terminated_target(self, mock_time):
        """404 ServiceError returns None when TERMINATED is a target state."""
        mock_time.monotonic.side_effect = [0.0]

        get_fn = MagicMock()
        get_fn.side_effect = oci.exceptions.ServiceError(
            status=404, code="NotFound", message="not found", headers={},
        )

        module = MagicMock()
        module.params = {"wait": True, "wait_timeout": 1200, "wait_interval": 30}

        from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import wait_for_resource
        result = wait_for_resource(module, get_fn, "ocid1.test", {"TERMINATED"})

        assert result is None

    @patch(f"{WAIT_PATH}.time")
    def test_404_returns_none_for_deleted_target(self, mock_time):
        """404 ServiceError returns None when DELETED is a target state."""
        mock_time.monotonic.side_effect = [0.0]

        get_fn = MagicMock()
        get_fn.side_effect = oci.exceptions.ServiceError(
            status=404, code="NotFound", message="not found", headers={},
        )

        module = MagicMock()
        module.params = {"wait": True, "wait_timeout": 1200, "wait_interval": 30}

        from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import wait_for_resource
        result = wait_for_resource(module, get_fn, "ocid1.test", {"DELETED"})

        assert result is None


class TestWaitForWorkRequest:
    """Test wait_for_work_request() behavior."""

    @patch(f"{WAIT_PATH}.time")
    def test_returns_on_succeeded(self, mock_time):
        """Returns work request when status is SUCCEEDED."""
        mock_time.monotonic.side_effect = [0.0, 1.0]

        wr = MagicMock()
        wr.status = "SUCCEEDED"

        client = MagicMock()
        client.get_work_request.return_value.data = wr

        module = MagicMock()
        module.params = {"wait_timeout": 1200, "wait_interval": 30}

        from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import wait_for_work_request
        result = wait_for_work_request(module, client, "wr-id-123")

        assert result is wr

    @patch(f"{WAIT_PATH}.time")
    def test_returns_on_completed(self, mock_time):
        """Returns work request when status is COMPLETED."""
        mock_time.monotonic.side_effect = [0.0, 1.0]

        wr = MagicMock()
        wr.status = "COMPLETED"

        client = MagicMock()
        client.get_work_request.return_value.data = wr

        module = MagicMock()
        module.params = {"wait_timeout": 1200, "wait_interval": 30}

        from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import wait_for_work_request
        result = wait_for_work_request(module, client, "wr-id-123")

        assert result is wr

    @patch(f"{WAIT_PATH}.time")
    def test_fails_on_failed(self, mock_time):
        """Calls fail_json when work request FAILED."""
        mock_time.monotonic.side_effect = [0.0, 1.0]

        wr = MagicMock()
        wr.status = "FAILED"

        client = MagicMock()
        client.get_work_request.return_value.data = wr

        module = MagicMock()
        module.params = {"wait_timeout": 1200, "wait_interval": 30}
        module.fail_json.side_effect = SystemExit(1)

        from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import wait_for_work_request
        with pytest.raises(SystemExit):
            wait_for_work_request(module, client, "wr-id-123")

        module.fail_json.assert_called_once()

    @patch(f"{WAIT_PATH}.time")
    def test_fails_on_canceled(self, mock_time):
        """Calls fail_json when work request CANCELED."""
        mock_time.monotonic.side_effect = [0.0, 1.0]

        wr = MagicMock()
        wr.status = "CANCELED"

        client = MagicMock()
        client.get_work_request.return_value.data = wr

        module = MagicMock()
        module.params = {"wait_timeout": 1200, "wait_interval": 30}
        module.fail_json.side_effect = SystemExit(1)

        from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import wait_for_work_request
        with pytest.raises(SystemExit):
            wait_for_work_request(module, client, "wr-id-123")

        module.fail_json.assert_called_once()

    @patch(f"{WAIT_PATH}.time")
    def test_timeout_work_request(self, mock_time):
        """Calls fail_json on timeout."""
        mock_time.monotonic.side_effect = [0.0, 1300.0]
        mock_time.sleep = MagicMock()

        wr = MagicMock()
        wr.status = "IN_PROGRESS"

        client = MagicMock()
        client.get_work_request.return_value.data = wr

        module = MagicMock()
        module.params = {"wait_timeout": 1200, "wait_interval": 30}
        module.fail_json.side_effect = SystemExit(1)

        from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import wait_for_work_request
        with pytest.raises(SystemExit):
            wait_for_work_request(module, client, "wr-id-123")

        module.fail_json.assert_called_once()
        assert "Timed out" in module.fail_json.call_args[1]["msg"]


class TestCallWithRetry:
    """Test call_with_retry() exponential backoff."""

    @patch(f"{WAIT_PATH}.time")
    def test_success_no_retry(self, mock_time):
        """Successful call returns immediately without retry."""
        fn = MagicMock(return_value="result")

        from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import call_with_retry
        result = call_with_retry(fn, "arg1", key="val")

        assert result == "result"
        fn.assert_called_once_with("arg1", key="val")

    @patch(f"{WAIT_PATH}.time")
    def test_retries_on_429(self, mock_time):
        """Retries on 429 (rate limit) and succeeds."""
        mock_time.sleep = MagicMock()

        fn = MagicMock()
        fn.side_effect = [
            oci.exceptions.ServiceError(status=429, code="TooMany", message="rate limited", headers={}),
            "success",
        ]

        from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import call_with_retry
        result = call_with_retry(fn, max_retries=3)

        assert result == "success"
        assert fn.call_count == 2

    @patch(f"{WAIT_PATH}.time")
    def test_retries_on_503(self, mock_time):
        """Retries on 503 (service unavailable)."""
        mock_time.sleep = MagicMock()

        fn = MagicMock()
        fn.side_effect = [
            oci.exceptions.ServiceError(status=503, code="ServiceUnavailable", message="unavailable", headers={}),
            "ok",
        ]

        from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import call_with_retry
        result = call_with_retry(fn, max_retries=3)

        assert result == "ok"

    @patch(f"{WAIT_PATH}.time")
    def test_raises_on_non_retryable(self, mock_time):
        """Raises immediately on non-retryable status codes."""
        fn = MagicMock()
        fn.side_effect = oci.exceptions.ServiceError(
            status=400, code="BadRequest", message="bad request", headers={},
        )

        from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import call_with_retry
        with pytest.raises(oci.exceptions.ServiceError) as exc_info:
            call_with_retry(fn, max_retries=3)

        assert exc_info.value.status == 400
        assert fn.call_count == 1

    @patch(f"{WAIT_PATH}.time")
    def test_exhausts_retries(self, mock_time):
        """Raises after exhausting all retries."""
        mock_time.sleep = MagicMock()

        fn = MagicMock()
        fn.side_effect = oci.exceptions.ServiceError(
            status=500, code="InternalError", message="server error", headers={},
        )

        from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import call_with_retry
        with pytest.raises(oci.exceptions.ServiceError):
            call_with_retry(fn, max_retries=2)

        assert fn.call_count == 3  # initial + 2 retries
