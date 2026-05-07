# Contributing to stevefulme1.oci_cloud

Thank you for your interest in contributing to the Oracle OCI Ansible
collection. This document explains the process for contributing code,
reporting issues, and running tests.

## Getting Started

### Prerequisites

| Requirement | Version |
|---|---|
| Python | >= 3.12 |
| ansible-core | >= 2.16 |
| OCI Python SDK | >= 2.90.0 |
| pytest | latest |

### Environment Setup

1. Fork the repository and clone your fork:

   ```bash
   mkdir -p ansible_collections/oracle
   git clone https://github.com/<your-fork>/stevefulme1.oci_cloud.git ansible_collections/oracle/oci
   cd ansible_collections/oracle/oci
   ```

2. Create a Python virtual environment:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install ansible-core>=2.16 oci pytest pytest-cov yamllint flake8 ansible-lint
   ```

3. Configure OCI credentials in `~/.oci/config` or via environment variables.

## Running Tests

### Linting

```bash
yamllint -c .yamllint .
flake8 plugins/ --max-line-length=120 --ignore=E402,W503
ansible-lint --strict
```

### Sanity Tests

The collection must be checked out at the path
`ansible_collections/oracle/oci/` for sanity tests to work:

```bash
ansible-test sanity --python 3.12 -v
ansible-test sanity --python 3.13 -v
```

### Unit Tests

```bash
PYTHONPATH=$(pwd)/../../.. pytest tests/unit/ -v --tb=short
```

## Pull Request Process

1. **Fork** the repository and create a feature branch from `main`.
2. **Write your changes** following the module patterns in `plugins/modules/`.
3. **Add tests** for new modules in `tests/unit/`.
4. **Run all checks** (lint, sanity, unit tests) before submitting.
5. **Submit a pull request** with a clear description of the changes.
6. **Sign-off**: All commits must include a `Signed-off-by` line
   (use `git commit -s`).

### PR Requirements

- [ ] All sanity tests pass (`ansible-test sanity`)
- [ ] All unit tests pass (`pytest tests/unit/`)
- [ ] flake8 passes with `--max-line-length=120 --ignore=E402,W503`
- [ ] yamllint passes
- [ ] ansible-lint passes with `--strict`
- [ ] New modules include `DOCUMENTATION`, `EXAMPLES`, and `RETURN` blocks
- [ ] New modules extend `stevefulme1.oci_cloud.oci_common` documentation fragment
- [ ] New modules set `version_added: "X.Y.0"` to the next release version
- [ ] CHANGELOG.md updated with changes

## Module Development Guidelines

### Module Structure

All modules must follow the standalone pattern:

```python
# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI <Resource>."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""..."""
EXAMPLES = r"""..."""
RETURN = r"""..."""

# imports after DOCUMENTATION block
```

### Key Rules

- No shebangs (`#!/usr/bin/python`) in module files.
- Imports must come after the `DOCUMENTATION`/`EXAMPLES`/`RETURN` blocks.
- Use `no_log=True` in `argument_spec` for sensitive parameters (passwords,
  keys), but **not** in the `DOCUMENTATION` block.
- All modules must support `check_mode`.
- All modules must be idempotent.
- Use `extends_documentation_fragment: stevefulme1.oci_cloud.oci_common`.
- List-type parameters must include `elements:` in the DOCUMENTATION block.

## Release Process

1. Create a release branch from `main`.
2. Update `version` in `galaxy.yml`.
3. Update `CHANGELOG.md` and `changelogs/changelog.rst`.
4. Merge the release branch to `main`.
5. Tag the merge commit with the version (e.g., `v1.1.0`).
6. The CI pipeline publishes to Ansible Galaxy automatically.

## Reporting Issues

Open a GitHub issue at
<https://github.com/stevefulme1/oracle.oci/issues> with:

- A clear title and description
- Steps to reproduce (for bugs)
- Expected vs actual behavior
- Ansible version, Python version, and OCI SDK version
- Relevant playbook snippets or error output

## Code of Conduct

This project follows the
[Ansible Community Code of Conduct](https://docs.ansible.com/ansible/latest/community/code_of_conduct.html).
See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) for details.

## License

By contributing, you agree that your contributions will be licensed under the
GNU General Public License v3.0 or later. See [COPYING](COPYING).
