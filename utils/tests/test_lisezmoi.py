from datetime import UTC, datetime
from unittest import TestCase

from utils.lisezmoi import fill, french_month


class LisezmoiTestCase(TestCase):
    def test_the_month_is_french(self) -> None:
        self.assertEqual(french_month(datetime(2026, 8, 1, tzinfo=UTC)), "Août 2026")

    def test_every_placeholder_is_filled(self) -> None:
        text = fill("@DATE@ @VERSION@ @VERSION@", "v1.0.0b0", datetime(2026, 10, 13, tzinfo=UTC))
        self.assertEqual(text, "Octobre 2026 v1.0.0b0 v1.0.0b0")
