#!/usr/bin/env python3
"""
Core Service Test Script
"""

from core.test_utils import ServiceTester


class CoreServiceTester(ServiceTester):
    def __init__(self):
        super().__init__("core", cfg={})


def main(action=None):
    tester = CoreServiceTester()
    tester.test()


if __name__ == "__main__":
    main()
