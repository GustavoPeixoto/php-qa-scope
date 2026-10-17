"""Shared fixtures for the helper and workflow-owned publisher."""

import json
from pathlib import Path
import unittest

from release.validate import ReleaseError, remote_tags, validate


FIXTURES = json.loads(Path(__file__).with_name("fixtures.json").read_text())
REPOSITORY = "GustavoPeixoto/php-qa-scope"


class ContractTests(unittest.TestCase):
    def test_shared_contract(self):
        for fixture in FIXTURES:
            with self.subTest(fixture=fixture):
                args = (fixture["branch"], fixture["manifest"], fixture["tags"], REPOSITORY,
                        "fork/repo" if fixture.get("fork") else REPOSITORY)
                if fixture["ok"]:
                    result = validate(*args)
                    self.assertEqual(fixture["branch"].startswith("release/"), result["release"])
                else:
                    with self.assertRaises(ReleaseError):
                        validate(*args)

    def test_pages_numeric_maximum_and_errors(self):
        first = [{"name": f"ignored-{i}"} for i in range(98)] + [{"name": "v1.9.0"}, {"name": "1.8.0"}]
        calls = []

        def request(endpoint):
            calls.append(endpoint)
            return first if endpoint.endswith("page=1") else [{"name": "v1.10.0"}, {"name": "v2.0.0-rc.1"}]

        tags = remote_tags(REPOSITORY, request)
        self.assertEqual(2, len(calls))
        self.assertEqual("1.10.0", validate("release/v1.10.1", {"version": "1.10.1"}, tags, REPOSITORY, REPOSITORY)["baseline"])
        self.assertEqual([], remote_tags(REPOSITORY, lambda _: []))
        for response in ({}, None, [None], [{"name": 1}], [{"name": ""}], first + first):
            with self.subTest(response=response), self.assertRaises(ReleaseError):
                remote_tags(REPOSITORY, lambda _: response)
        with self.assertRaises(ReleaseError):
            remote_tags(REPOSITORY, lambda _: first)

        def fail_second(endpoint):
            if endpoint.endswith("page=1"):
                return first
            raise ReleaseError("network error")

        with self.assertRaises(ReleaseError):
            remote_tags(REPOSITORY, fail_second)

    def test_wrong_base(self):
        with self.assertRaises(ReleaseError):
            validate("release/v0.1.0", {"version": "0.1.0"}, [], REPOSITORY, REPOSITORY, "develop")


if __name__ == "__main__":
    unittest.main()
