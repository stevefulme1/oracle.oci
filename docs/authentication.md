# Authentication Guide

The `stevefulme1.oci_cloud` collection supports five authentication methods. Every module
accepts the `auth_type` parameter to select the method. When omitted, the
default is `api_key`.

## 1. API Key Authentication (config file)

This is the default method. The OCI Python SDK reads credentials from
`~/.oci/config`.

### Setup

Generate an API signing key pair:

```bash
mkdir -p ~/.oci
openssl genrsa -out ~/.oci/oci_api_key.pem 2048
chmod 600 ~/.oci/oci_api_key.pem
openssl rsa -pubout -in ~/.oci/oci_api_key.pem -out ~/.oci/oci_api_key_public.pem
```

Upload the public key in the OCI Console under **Identity > Users > API Keys**.

Create `~/.oci/config`:

```ini
[DEFAULT]
user=ocid1.user.oc1..aaaaaaaaexample
fingerprint=aa:bb:cc:dd:ee:ff:00:11:22:33:44:55:66:77:88:99
tenancy=ocid1.tenancy.oc1..aaaaaaaaexample
region=us-ashburn-1
key_file=~/.oci/oci_api_key.pem
```

### Usage

```yaml
- name: Create a VCN using API key auth (default)
  stevefulme1.oci_cloud.oci_vcn:
    compartment_id: "{{ compartment_id }}"
    display_name: demo-vcn
    cidr_blocks:
      - "10.0.0.0/16"
    state: present
```

### Using a Non-Default Profile

```yaml
- name: Create a VCN using a named profile
  stevefulme1.oci_cloud.oci_vcn:
    auth_type: api_key
    config_file_location: ~/.oci/config
    config_profile_name: PROD
    compartment_id: "{{ compartment_id }}"
    display_name: prod-vcn
    cidr_blocks:
      - "10.0.0.0/16"
    state: present
```

## 2. Environment Variable Authentication

Set the following environment variables instead of (or to override) the config
file:

```bash
export OCI_USER_ID="ocid1.user.oc1..aaaaaaaaexample"
export OCI_USER_FINGERPRINT="aa:bb:cc:dd:ee:ff:00:11:22:33:44:55:66:77:88:99"
export OCI_TENANCY="ocid1.tenancy.oc1..aaaaaaaaexample"
export OCI_REGION="us-ashburn-1"
export OCI_USER_KEY_FILE="/home/user/.oci/oci_api_key.pem"
```

### Usage

```yaml
- name: Create a VCN using env-var credentials
  stevefulme1.oci_cloud.oci_vcn:
    auth_type: api_key          # env vars are picked up automatically
    compartment_id: "{{ compartment_id }}"
    display_name: env-vcn
    cidr_blocks:
      - "10.0.0.0/16"
    state: present
```

Environment variables take precedence over values in the config file.

## 3. Instance Principal Authentication

Use this method when running playbooks **on an OCI compute instance**. The
instance must belong to a dynamic group with the appropriate IAM policies.

### IAM Setup

1. Create a dynamic group matching your instances:

   ```
   ALL {instance.compartment.id = 'ocid1.compartment.oc1..aaaaaaaaexample'}
   ```

2. Create a policy granting the dynamic group permissions:

   ```
   Allow dynamic-group my-ansible-instances to manage all-resources in compartment my-compartment
   ```

### Usage

```yaml
- name: Create a VCN using instance principal
  stevefulme1.oci_cloud.oci_vcn:
    auth_type: instance_principal
    compartment_id: "{{ compartment_id }}"
    display_name: ip-vcn
    cidr_blocks:
      - "10.0.0.0/16"
    state: present
```

No config file or environment variables are required. The SDK obtains a
short-lived token from the instance metadata service.

## 4. Resource Principal Authentication

Use this method when running inside **OCI Functions** or other services that
support resource principals.

### IAM Setup

Create a policy granting the function's dynamic group permissions:

```
Allow dynamic-group my-functions to manage all-resources in compartment my-compartment
```

### Usage

```yaml
- name: Create a VCN using resource principal
  stevefulme1.oci_cloud.oci_vcn:
    auth_type: resource_principal
    compartment_id: "{{ compartment_id }}"
    display_name: rp-vcn
    cidr_blocks:
      - "10.0.0.0/16"
    state: present
```

## 5. Session Token Authentication

Use the OCI CLI to create a browser-based login session, then reference the
resulting token. This is useful for MFA-protected tenancies.

### Setup

```bash
oci session authenticate --region us-ashburn-1
```

This opens a browser, authenticates the user, and writes a token to the
config file under a `[DEFAULT]` (or named) profile with `security_token_file`.

The resulting config section looks like:

```ini
[DEFAULT]
fingerprint=aa:bb:cc:dd:ee:ff:00:11:22:33:44:55:66:77:88:99
key_file=/home/user/.oci/sessions/DEFAULT/oci_api_key.pem
tenancy=ocid1.tenancy.oc1..aaaaaaaaexample
region=us-ashburn-1
security_token_file=/home/user/.oci/sessions/DEFAULT/token
```

### Usage

```yaml
- name: Create a VCN using session token auth
  stevefulme1.oci_cloud.oci_vcn:
    auth_type: security_token
    config_file_location: ~/.oci/config
    config_profile_name: DEFAULT
    compartment_id: "{{ compartment_id }}"
    display_name: session-vcn
    cidr_blocks:
      - "10.0.0.0/16"
    state: present
```

Session tokens expire (typically after one hour). Refresh with:

```bash
oci session refresh --profile DEFAULT
```

## Auth Type Summary

| `auth_type` Value    | Where to Use                  | Credentials Source          |
|----------------------|-------------------------------|-----------------------------|
| `api_key` (default)  | Workstation / CI              | Config file or env vars     |
| `instance_principal` | OCI Compute instance          | Instance metadata service   |
| `resource_principal` | OCI Functions / Cloud Shell   | Resource metadata service   |
| `security_token`     | Workstation with MFA          | Session token file          |

## Passing Auth Parameters as Playbook Variables

For maximum flexibility, define auth settings as variables:

```yaml
---
- name: Auth via variables
  hosts: localhost
  connection: local
  gather_facts: false

  vars:
    oci_auth_type: api_key
    oci_config_file: ~/.oci/config
    oci_config_profile: DEFAULT
    compartment_id: "ocid1.compartment.oc1..aaaaaaaaexample"

  tasks:
    - name: Create VCN
      stevefulme1.oci_cloud.oci_vcn:
        auth_type: "{{ oci_auth_type }}"
        config_file_location: "{{ oci_config_file }}"
        config_profile_name: "{{ oci_config_profile }}"
        compartment_id: "{{ compartment_id }}"
        display_name: var-vcn
        cidr_blocks:
          - "10.0.0.0/16"
        state: present
```

Override at runtime:

```bash
ansible-playbook site.yml -e oci_auth_type=instance_principal
```
