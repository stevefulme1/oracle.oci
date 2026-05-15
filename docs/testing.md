# Testing the oracle.oci Collection

This document covers how to run unit tests, integration tests, and Molecule
scenarios for the `oracle.oci` Ansible collection.

## Prerequisites

- Python 3.12+
- `ansible-core >= 2.16`
- `pytest`, `pytest-cov`

Install all test dependencies:

```bash
pip install ansible-core>=2.16 oci pytest pytest-cov
```

## Unit Tests

Unit tests mock the OCI SDK and verify module logic without making API calls.
The `tests/unit/conftest.py` builds a synthetic `oci` package tree so the real
SDK is not required.

### Run locally

```bash
# From the collection root
pytest tests/unit/ -v --tb=short

# Run a single test file
pytest tests/unit/plugins/modules/test_oci_instance.py -v

# With coverage
pytest tests/unit/ --cov=plugins --cov-report=term-missing
```

### Using nox

```bash
nox -s tests
```

## Integration Tests

Integration tests exercise modules against a real or mocked OCI environment.
They live under `tests/integration/targets/` and follow the standard
`ansible-test integration` layout.

### Available targets

| Target               | Description                        |
|----------------------|------------------------------------|
| `oci_instance`       | Compute instance CRUD              |
| `oci_vcn`            | Virtual Cloud Network CRUD         |
| `oci_subnet`         | Subnet CRUD                        |
| `oci_security_list`  | Security list CRUD with rules      |
| `oci_bucket`         | Object Storage bucket CRUD         |

### Run with mock values (no cloud access)

Set placeholder environment variables and run:

```bash
export OCI_COMPARTMENT_ID="ocid1.compartment.oc1..mock"
export OCI_VCN_ID="ocid1.vcn.oc1..mock"
export OCI_AVAILABILITY_DOMAIN="Uocm:PHX-AD-1"
export OCI_NAMESPACE_NAME="mocknamespace"
export OCI_IMAGE_ID="ocid1.image.oc1.phx.mock"
export OCI_SUBNET_ID="ocid1.subnet.oc1.phx.mock"

ansible-test integration --python 3.12 -v --allow-unsupported
```

### Run against OCI cloud

1. Copy the template and fill in real values:

```bash
cp tests/integration/cloud-config-oci.ini.template \
   tests/integration/cloud-config-oci.ini
```

2. Export the variables and run:

```bash
source <(grep -v '^\[' tests/integration/cloud-config-oci.ini \
         | grep -v '^#' | grep '=' | sed 's/^/export /')

ansible-test integration --python 3.12 -v --allow-unsupported
```

## Setting Up OCI Always Free Tier

OCI provides an Always Free tier that includes resources sufficient for
integration testing:

1. **Sign up** at <https://cloud.oracle.com/> for a free account.
2. **Create a compartment** under the root tenancy for test resources.
3. **Generate an API signing key** in the OCI Console under your user
   settings. Download the PEM private key.
4. **Note the following OCIDs**:
   - Tenancy OCID
   - User OCID
   - Compartment OCID
   - API key fingerprint
5. **Create a VCN** with a public subnet in your test compartment.
6. **Find the Oracle Linux 9 image OCID** for your region at
   <https://docs.oracle.com/en-us/iaas/images/>.

### Always Free resources used

| Resource                  | Always Free Limit       |
|---------------------------|-------------------------|
| VM.Standard.E2.1.Micro    | 2 instances             |
| Block Volume              | 200 GB total            |
| Object Storage            | 20 GB                   |
| VCN                       | Unlimited               |
| Load Balancer (flexible)  | 1 instance              |

## GitHub Secrets for CI

The `integration-cloud` CI job requires these repository secrets:

| Secret                    | Description                              |
|---------------------------|------------------------------------------|
| `OCI_TENANCY_OCID`        | Root tenancy OCID                        |
| `OCI_USER_OCID`           | API user OCID                            |
| `OCI_FINGERPRINT`         | API key fingerprint                      |
| `OCI_PRIVATE_KEY`         | PEM private key content (not path)       |
| `OCI_COMPARTMENT_ID`      | Test compartment OCID                    |
| `OCI_AVAILABILITY_DOMAIN` | e.g. `Uocm:PHX-AD-1`                    |
| `OCI_IMAGE_ID`            | Oracle Linux 9 image OCID                |
| `OCI_SUBNET_ID`           | Subnet OCID for compute tests            |
| `OCI_VCN_ID`              | VCN OCID for networking tests            |
| `OCI_NAMESPACE_NAME`      | Object Storage namespace                 |

The cloud integration job only runs on `workflow_dispatch` (manual trigger)
to avoid unintended cloud charges.

## Molecule

Molecule provisions a real OCI compute instance and runs a convergence
playbook that exercises key modules end-to-end.

### Prerequisites

```bash
pip install molecule molecule-oci
```

### Run

```bash
# From the collection root
molecule test

# Keep the instance for debugging
molecule converge
molecule verify
molecule destroy
```

### Configuration

The Molecule scenario uses these environment variables:

- `OCI_COMPARTMENT_ID` -- compartment for the test instance
- `OCI_AVAILABILITY_DOMAIN` -- availability domain
- `OCI_IMAGE_ID` -- Oracle Linux 9 image OCID
- `OCI_SUBNET_ID` -- subnet with internet access
- `OCI_REGION` -- region (default: `us-phoenix-1`)
- `OCI_PRIVATE_KEY` -- path to API key PEM file

The scenario uses `VM.Standard.E2.1.Micro` (Always Free eligible).
