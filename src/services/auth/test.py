#!/usr/bin/env python3
"""
Auth Service Lambda Test Script
"""

from pathlib import Path

from core.test_utils import ServiceTester


class AuthServiceTester(ServiceTester):
    def __init__(self):
        super().__init__("auth", cfg={})


def main():
    tester = AuthServiceTester()
    tester.test()


if __name__ == "__main__":
    main()
