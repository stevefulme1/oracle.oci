from __future__ import absolute_import, division, print_function
__metaclass__ = type

from jinja2.runtime import Undefined

DOCUMENTATION = r"""
---
name: override
short_description: Optionally override a default value
description:
  - A filter to allow optionally overriding a default value with a variable.
  - If the override variable is undefined, the hardcoded default is used.
  - If the override variable is explicitly null, the field is omitted.
  - If the override variable has a value, that value is used.
version_added: "1.2.0"
author:
  - Oracle (@oracle)
"""


class FilterModule(object):
    def filters(self):
        return {"override": self.override_filter}

    def override_filter(self, hardcoded_default, override, omit):
        if override is None:
            return omit
        elif isinstance(override, Undefined):
            return hardcoded_default
        else:
            return override
