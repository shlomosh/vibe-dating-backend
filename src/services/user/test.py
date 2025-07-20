#!/usr/bin/env python3
"""
User Service Lambda Test Script
"""

from pathlib import Path

from core.test_utils import ServiceTester


class UserServiceTester(ServiceTester):
    def __init__(self):
        super().__init__("user", cfg={})


def main(action=None):
    tester = UserServiceTester()
    tester.test()


if __name__ == "__main__":
    main()