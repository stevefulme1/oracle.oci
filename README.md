# Oracle Cloud Infrastructure (OCI) Ansible Collection

Ansible Collection for managing Oracle Cloud Infrastructure resources.

## Requirements

- Python >= 3.9
- `oci` Python SDK >= 2.90.0
- Ansible >= 2.15.0

## Authentication

Configure OCI credentials via:

1. **Config file** (default): `~/.oci/config`
2. **Environment variables**: `OCI_USER_ID`, `OCI_TENANCY_ID`, `OCI_REGION`, `OCI_FINGERPRINT`, `OCI_KEY_FILE`
3. **Instance principal**: Set `auth_type: instance_principal`
4. **Resource principal**: Set `auth_type: resource_principal`

## Modules

### Compute & OKE
- `oracle.oci.oci_instance` - Manage compute instances
- `oracle.oci.oci_image` - Manage custom images
- `oracle.oci.oci_instance_pool` - Manage instance pools
- `oracle.oci.oci_boot_volume` - Manage boot volumes
- `oracle.oci.oci_oke_cluster` - Manage OKE clusters
- `oracle.oci.oci_oke_node_pool` - Manage OKE node pools
- `oracle.oci.oci_container_instance` - Manage container instances

### Networking
- `oracle.oci.oci_vcn` - Manage Virtual Cloud Networks
- `oracle.oci.oci_subnet` - Manage subnets
- `oracle.oci.oci_route_table` - Manage route tables
- `oracle.oci.oci_security_list` - Manage security lists
- `oracle.oci.oci_nsg` - Manage Network Security Groups
- `oracle.oci.oci_internet_gateway` - Manage internet gateways
- `oracle.oci.oci_nat_gateway` - Manage NAT gateways
- `oracle.oci.oci_service_gateway` - Manage service gateways
- `oracle.oci.oci_drg` - Manage Dynamic Routing Gateways
- `oracle.oci.oci_load_balancer` - Manage load balancers
- `oracle.oci.oci_dns_zone` - Manage DNS zones

### Database
- `oracle.oci.oci_autonomous_database` - Manage Autonomous Databases
- `oracle.oci.oci_db_system` - Manage DB Systems
- `oracle.oci.oci_db_backup` - Manage database backups
- `oracle.oci.oci_data_guard` - Manage Data Guard associations

### IAM
- `oracle.oci.oci_compartment` - Manage compartments
- `oracle.oci.oci_user` - Manage users
- `oracle.oci.oci_group` - Manage groups
- `oracle.oci.oci_dynamic_group` - Manage dynamic groups
- `oracle.oci.oci_policy` - Manage IAM policies
- `oracle.oci.oci_api_key` - Manage API keys
- `oracle.oci.oci_tag_namespace` - Manage tag namespaces
- `oracle.oci.oci_tag` - Manage tags

### Storage
- `oracle.oci.oci_volume` - Manage block volumes
- `oracle.oci.oci_volume_backup` - Manage volume backups
- `oracle.oci.oci_bucket` - Manage Object Storage buckets
- `oracle.oci.oci_object` - Manage Object Storage objects
- `oracle.oci.oci_file_system` - Manage file systems
- `oracle.oci.oci_mount_target` - Manage mount targets
- `oracle.oci.oci_export` - Manage file system exports

### Security & Observability
- `oracle.oci.oci_vault` - Manage vaults
- `oracle.oci.oci_key` - Manage encryption keys
- `oracle.oci.oci_cloud_guard` - Manage Cloud Guard
- `oracle.oci.oci_alarm` - Manage monitoring alarms
- `oracle.oci.oci_log_group` - Manage log groups
- `oracle.oci.oci_notification_topic` - Manage notification topics
- `oracle.oci.oci_events_rule` - Manage event rules

### Dynamic Inventory
- `oracle.oci.oci_inventory` - Dynamic inventory plugin

## License

GNU General Public License v3.0+
