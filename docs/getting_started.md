# Getting Started with stevefulme1.oci_cloud

This guide walks you through installing the `stevefulme1.oci_cloud` Ansible collection and
running your first playbook against Oracle Cloud Infrastructure.

## Prerequisites

| Requirement | Minimum Version |
|-------------|-----------------|
| Python      | 3.9+            |
| Ansible     | 2.14+ (ansible-core) |
| OCI Python SDK | 2.90+        |

Install the OCI Python SDK:

```bash
pip install oci
```

## Installation

Install the collection from Ansible Galaxy:

```bash
ansible-galaxy collection install stevefulme1.oci_cloud
```

Or install from a local tarball:

```bash
ansible-galaxy collection install oracle-oci-1.0.0.tar.gz
```

To pin a version in a `requirements.yml`:

```yaml
---
collections:
  - name: stevefulme1.oci_cloud
    version: ">=1.0.0"
```

Then install with:

```bash
ansible-galaxy collection install -r requirements.yml
```

## Authentication Setup

The collection supports several authentication methods. The simplest is an
API key stored in a config file.

### Option 1 -- OCI Config File (recommended for workstations)

Create `~/.oci/config`:

```ini
[DEFAULT]
user=ocid1.user.oc1..aaaaaaaaexample
fingerprint=aa:bb:cc:dd:ee:ff:00:11:22:33:44:55:66:77:88:99
tenancy=ocid1.tenancy.oc1..aaaaaaaaexample
region=us-ashburn-1
key_file=~/.oci/oci_api_key.pem
```

No extra Ansible configuration is needed -- the modules pick up this file
automatically.

### Option 2 -- Environment Variables

```bash
export OCI_USER_ID="ocid1.user.oc1..aaaaaaaaexample"
export OCI_USER_FINGERPRINT="aa:bb:cc:dd:ee:ff:00:11:22:33:44:55:66:77:88:99"
export OCI_TENANCY="ocid1.tenancy.oc1..aaaaaaaaexample"
export OCI_REGION="us-ashburn-1"
export OCI_USER_KEY_FILE="~/.oci/oci_api_key.pem"
```

### Option 3 -- Instance Principal (within OCI)

When running on a compute instance inside OCI, pass `auth_type`:

```yaml
- stevefulme1.oci_cloud.oci_vcn:
    auth_type: instance_principal
    compartment_id: "{{ compartment_id }}"
    display_name: my-vcn
    cidr_blocks:
      - "10.0.0.0/16"
```

See [authentication.md](authentication.md) for all supported methods.

## Your First Playbook -- Create a VCN

Save the following as `create_vcn.yml`:

```yaml
---
- name: Create a Virtual Cloud Network
  hosts: localhost
  connection: local
  gather_facts: false

  vars:
    compartment_id: "ocid1.compartment.oc1..aaaaaaaaexample"
    vcn_name: "my-first-vcn"
    vcn_cidr: "10.0.0.0/16"
    region: "us-ashburn-1"

  tasks:
    - name: Create VCN
      stevefulme1.oci_cloud.oci_vcn:
        compartment_id: "{{ compartment_id }}"
        display_name: "{{ vcn_name }}"
        cidr_blocks:
          - "{{ vcn_cidr }}"
        dns_label: "myfirstvcn"
        region: "{{ region }}"
        state: present
      register: vcn_result

    - name: Show VCN details
      ansible.builtin.debug:
        var: vcn_result
```

Run it:

```bash
ansible-playbook create_vcn.yml
```

## Next Steps

- [Authentication Guide](authentication.md) -- all auth methods in detail
- [Inventory Plugin Guide](inventory_plugin.md) -- dynamic inventory for OCI
- [Example Playbooks](../examples/) -- compute, networking, database, OKE, and more
