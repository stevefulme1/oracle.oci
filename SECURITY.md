# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.1.x   | Yes       |
| 1.0.x   | Yes       |
| < 1.0   | No        |

## Reporting a Vulnerability

If you discover a security vulnerability in this collection, please report
it responsibly. **Do not open a public GitHub issue.**

### How to Report

1. Email the maintainers at **sfulmer@redhat.com** with:
   - A description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

2. You will receive an acknowledgment within **48 hours**.

3. We will work with you to understand the issue, develop a fix, and
   coordinate disclosure.

### What to Expect

- **Acknowledgment**: Within 48 hours of report.
- **Assessment**: Within 5 business days we will confirm the vulnerability
  and its severity.
- **Fix**: A patch will be developed and tested privately.
- **Disclosure**: A new release will be published with the fix, and a
  security advisory will be issued via GitHub.

## Security Best Practices for Users

When using this collection:

- **Never commit OCI credentials** (API keys, config files, tokens) to
  version control.
- Use `no_log: true` on tasks that handle sensitive data.
- Prefer **instance principal** or **resource principal** authentication
  over API key files when running on OCI compute instances.
- Keep the `oci` Python SDK updated to receive security patches.
- Use Ansible Vault to encrypt sensitive variables in playbooks.
- Review IAM policies to grant only the minimum permissions required.

## Sensitive Parameters

The following module parameters are marked `no_log` in the argument spec
and will not appear in Ansible logs:

- `admin_password` (database modules)
- `cluster_admin_password` (`oci_big_data_service`)
- `credentials` (`oci_postgresql_db_system`)
- `connection_credentials` (`oci_external_database`)
- `password` (`oci_goldengate_connection`)
- `ogg_data` (`oci_goldengate_deployment`)
- `pdb_admin_password` (`oci_pluggable_database`)
- `private_key_pem` (`oci_certificate`)
- `api_user_key_pass_phrase` (common auth parameter)
