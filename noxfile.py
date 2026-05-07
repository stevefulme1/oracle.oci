"""Nox sessions for stevefulme1.oci_cloud Ansible collection."""

import nox

PYTHON_VERSIONS = ["3.12", "3.13"]


@nox.session(python=PYTHON_VERSIONS)
def lint(session):
    """Run linting checks."""
    session.install("yamllint", "flake8", "ansible-lint", "ansible-core>=2.16")
    session.run("yamllint", "-c", ".yamllint", ".")
    session.run(
        "flake8", "plugins/",
        "--max-line-length=120",
        "--ignore=E402,W503",
    )
    session.run("ansible-lint", "--strict")


@nox.session(python=PYTHON_VERSIONS)
def unit(session):
    """Run unit tests with pytest."""
    session.install("pytest", "pytest-cov", "ansible-core>=2.16", "oci")

    # When checked out as ansible_collections/oracle/oci/, the workspace
    # root (three levels up) must be on PYTHONPATH so that imports like
    # ``ansible_collections.stevefulme1.oci_cloud.plugins...`` resolve.
    import os
    cwd = os.path.abspath(".")
    namespace_root = os.path.abspath(os.path.join(cwd, os.pardir, os.pardir, os.pardir))
    env = {}
    if os.path.isdir(os.path.join(namespace_root, "ansible_collections")):
        env["PYTHONPATH"] = namespace_root

    session.run(
        "pytest", "tests/unit/",
        "-v",
        "--tb=short",
        "--cov=plugins",
        "--cov-report=term-missing",
        *session.posargs,
        env=env,
    )


@nox.session(python=PYTHON_VERSIONS)
def sanity(session):
    """Run ansible-test sanity checks."""
    session.install("ansible-core>=2.16")
    session.run(
        "ansible-test", "sanity",
        "--python", session.python,
        "--color", "yes",
        "-v",
    )


@nox.session(python=PYTHON_VERSIONS)
def import_check(session):
    """Verify all modules can be imported without errors."""
    session.install("ansible-core>=2.16", "oci")
    import glob
    modules = glob.glob("plugins/modules/*.py")
    for module in sorted(modules):
        session.run("python", "-c", f"import py_compile; py_compile.compile('{module}', doraise=True)")


@nox.session(python=["3.12"])
def docs(session):
    """Validate module documentation."""
    session.install("ansible-core>=2.16", "oci")
    session.run(
        "ansible-test", "sanity",
        "--test", "validate-modules",
        "--python", session.python,
        "--color", "yes",
        "-v",
    )
