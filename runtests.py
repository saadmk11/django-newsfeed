#!/usr/bin/env python
"""Run the newsfeed test suite."""

import os
import sys

import django
from django.conf import settings
from django.test.utils import get_runner


def run_tests(*test_args: str) -> None:
    """Run the Django test suite.

    Args:
        test_args: Optional test labels. The whole suite runs when omitted.

    """
    if not test_args:
        test_args = ("tests",)

    os.environ["DJANGO_SETTINGS_MODULE"] = "test_project.settings"
    django.setup()
    test_runner_class = get_runner(settings)
    test_runner = test_runner_class()
    failures = test_runner.run_tests(test_args)
    sys.exit(bool(failures))


if __name__ == "__main__":
    run_tests(*sys.argv[1:])
