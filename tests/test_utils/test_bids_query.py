from unittest import TestCase

from _pytest.fixtures import fixture

# import datalad
from tests.fixtures import TEST_BIDS_DIRECTORIES


class BidsQueryTestCase(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        # Before all tests
        return super().setUpClass()

    def setUp(self) -> None:
        # Before each test
        return super().setUp()

    def test_bids_layout(self):
        self.assertEqual(1, 1)
