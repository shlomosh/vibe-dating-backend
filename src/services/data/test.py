#!/usr/bin/env python3
"""
Data Service Test Script
"""

from pathlib import Path

from core.test_utils import ServiceTester


class DataServiceTester(ServiceTester):
    def __init__(self):
        super().__init__("data", cfg={})


def main(action=None):
    tester = DataServiceTester()
    tester.test()


if __name__ == "__main__":
    main()
