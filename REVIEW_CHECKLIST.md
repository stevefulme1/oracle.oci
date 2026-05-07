# Pull Request Review Checklist

Use this checklist when reviewing pull requests for the `stevefulme1.oci_cloud`
Ansible collection.

## General

- [ ] PR title follows conventional commit format (`feat:`, `fix:`, `docs:`, etc.)
- [ ] PR description clearly explains the change and its motivation
- [ ] No unrelated changes included in the PR

## Code Quality

- [ ] flake8 passes (`--max-line-length=120 --ignore=E402,W503`)
- [ ] yamllint passes
- [ ] ansible-lint passes with `--strict`
- [ ] No shebangs in module files
- [ ] Imports are placed after DOCUMENTATION/EXAMPLES/RETURN blocks
- [ ] No hardcoded credentials or secrets
- [ ] Sensitive parameters use `no_log=True` in argument_spec only (not in DOCUMENTATION)

## Module Standards

- [ ] Module has `DOCUMENTATION`, `EXAMPLES`, and `RETURN` blocks
- [ ] DOCUMENTATION includes `extends_documentation_fragment: stevefulme1.oci_cloud.oci_common`
- [ ] DOCUMENTATION includes `version_added` set to the correct release
- [ ] DOCUMENTATION includes `author: Oracle (@oracle)`
- [ ] List-type parameters include `elements:` definition
- [ ] Module supports `check_mode`
- [ ] Module is idempotent (re-running produces no changes)
- [ ] Module uses `to_dict()` helper for serializing OCI SDK responses
- [ ] Module handles 404 responses gracefully in get/find functions

## Testing

- [ ] `ansible-test sanity` passes on Python 3.12 and 3.13
- [ ] `ansible-test sanity` passes on ansible-core 2.16, 2.17, 2.18, and 2.20
- [ ] Unit tests added for new modules
- [ ] Unit tests pass (`pytest tests/unit/ -v`)

## Documentation

- [ ] CHANGELOG.md updated
- [ ] README.md updated if new modules or features added
- [ ] Module examples are valid and demonstrate common use cases

## Security

- [ ] No credentials or tokens in code or examples
- [ ] Password/key parameters marked `no_log=True` in argument_spec
- [ ] No use of `eval()`, `exec()`, or `subprocess` with user input
- [ ] OCI SDK calls use `call_with_retry` wrapper
