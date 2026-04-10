# Dynamic Inventory Plugin Guide

The `oracle.oci.oci_inventory` plugin discovers compute instances in your OCI
tenancy and builds an Ansible inventory automatically.

## Requirements

- The OCI Python SDK (`pip install oci`)
- Valid OCI credentials (any auth method described in [authentication.md](authentication.md))

## Configuration File

The inventory plugin is activated by a YAML file whose name ends in
`.oci.yml` or `.oci.yaml`. Ansible detects the plugin from the filename.

### Minimal Example

```yaml
# inventory.oci.yml
plugin: oracle.oci.oci_inventory
regions:
  - us-ashburn-1
compartments:
  - compartment_ocid: ocid1.compartment.oc1..aaaaaaaaexample
    fetch_hosts_from_subcompartments: true
```

## Basic Usage

```bash
# List discovered hosts
ansible-inventory -i inventory.oci.yml --list

# Graph view
ansible-inventory -i inventory.oci.yml --graph

# Run ad-hoc command
ansible -i inventory.oci.yml all -m ping
```

## Authentication

The plugin supports the same `auth_type` values as the modules:

```yaml
plugin: oracle.oci.oci_inventory
auth_type: instance_principal
regions:
  - us-ashburn-1
compartments:
  - compartment_ocid: ocid1.compartment.oc1..aaaaaaaaexample
```

Or with a named profile:

```yaml
plugin: oracle.oci.oci_inventory
config_file: ~/.oci/config
config_profile: PROD
regions:
  - us-phoenix-1
```

## Filtering by Compartment

Limit discovery to specific compartments:

```yaml
plugin: oracle.oci.oci_inventory
regions:
  - us-ashburn-1
compartments:
  - compartment_ocid: ocid1.compartment.oc1..aaaaaaaaDEV
    fetch_hosts_from_subcompartments: false
  - compartment_ocid: ocid1.compartment.oc1..aaaaaaaaSTAGING
    fetch_hosts_from_subcompartments: true
```

## Filtering by Freeform Tags

Return only instances that match specific freeform tags:

```yaml
plugin: oracle.oci.oci_inventory
regions:
  - us-ashburn-1
compartments:
  - compartment_ocid: ocid1.compartment.oc1..aaaaaaaaexample
filters:
  freeform_tags:
    Environment: production
    ManagedBy: ansible
```

## Filtering by Defined Tags

```yaml
plugin: oracle.oci.oci_inventory
regions:
  - us-ashburn-1
compartments:
  - compartment_ocid: ocid1.compartment.oc1..aaaaaaaaexample
filters:
  defined_tags:
    Operations:
      Team: platform-eng
```

## Filtering by Lifecycle State

Only return running instances:

```yaml
plugin: oracle.oci.oci_inventory
regions:
  - us-ashburn-1
compartments:
  - compartment_ocid: ocid1.compartment.oc1..aaaaaaaaexample
filters:
  lifecycle_state: RUNNING
```

## Grouping Strategies

Control how hosts are grouped in the inventory:

```yaml
plugin: oracle.oci.oci_inventory
regions:
  - us-ashburn-1
  - us-phoenix-1
compartments:
  - compartment_ocid: ocid1.tenancy.oc1..aaaaaaaaexample
    fetch_hosts_from_subcompartments: true

# Built-in grouping keys
groups_from:
  - region                  # e.g., us_ashburn_1
  - compartment_name        # e.g., production
  - availability_domain     # e.g., AD_1
  - shape                   # e.g., VM_Standard_E4_Flex
  - freeform_tags           # one group per tag key/value pair
  - defined_tags            # one group per namespace/key/value
```

### Custom Group Names with Keyed Groups

```yaml
plugin: oracle.oci.oci_inventory
regions:
  - us-ashburn-1
compartments:
  - compartment_ocid: ocid1.compartment.oc1..aaaaaaaaexample

keyed_groups:
  - key: freeform_tags.Environment
    prefix: env
    separator: "_"
  - key: region
    prefix: region
    separator: "_"
```

This produces groups like `env_production`, `region_us_ashburn_1`.

## Host Variables

The plugin sets several host variables automatically:

| Variable                | Description                          |
|-------------------------|--------------------------------------|
| `ansible_host`          | Primary private IP (or public IP)    |
| `display_name`          | Instance display name                |
| `instance_id`           | OCID of the instance                 |
| `region`                | OCI region                           |
| `availability_domain`   | AD name                              |
| `shape`                 | Compute shape                        |
| `lifecycle_state`       | RUNNING, STOPPED, etc.               |
| `freeform_tags`         | Dict of freeform tags                |
| `defined_tags`          | Dict of defined tags                 |

### Preferring Public IP

```yaml
plugin: oracle.oci.oci_inventory
hostname_format: public_ip
```

Options: `private_ip` (default), `public_ip`, `display_name`.

## Caching

Enable caching to avoid repeated API calls:

```yaml
plugin: oracle.oci.oci_inventory
regions:
  - us-ashburn-1
compartments:
  - compartment_ocid: ocid1.compartment.oc1..aaaaaaaaexample

cache: true
cache_plugin: jsonfile
cache_connection: /tmp/oci_inventory_cache
cache_timeout: 3600    # seconds
```

Clear the cache manually:

```bash
rm -rf /tmp/oci_inventory_cache
```

Or force a refresh:

```bash
ansible-inventory -i inventory.oci.yml --list --flush-cache
```

## Using with ansible-playbook

```bash
# Simple invocation
ansible-playbook -i inventory.oci.yml site.yml

# Limit to a group
ansible-playbook -i inventory.oci.yml site.yml --limit env_production

# Combine with a static inventory
ansible-playbook -i inventory.oci.yml -i static_hosts.ini site.yml
```

### In ansible.cfg

```ini
[defaults]
inventory = inventory.oci.yml
```

## Complete Example

See [examples/inventory/oracle.oci.yml](../examples/inventory/oracle.oci.yml)
for a ready-to-use configuration.
