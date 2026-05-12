import unittest
from unittest.mock import patch, Mock

import pigeon_app


class TestPigeonApp(unittest.TestCase):
    def test_check_ownership_returns_true_for_valid_owner(self):
        with patch.object(pigeon_app, "current_user", Mock(id=5)):
            self.assertTrue(pigeon_app.check_ownership("5-AXY1-21"))

    def test_check_ownership_returns_false_for_invalid_owner(self):
        with patch.object(pigeon_app, "current_user", Mock(id=5)):
            self.assertFalse(pigeon_app.check_ownership("6-AXY1-21"))

    def test_check_ownership_returns_false_for_invalid_id(self):
        with patch.object(pigeon_app, "current_user", Mock(id=5)):
            self.assertFalse(pigeon_app.check_ownership("bad-id"))

    def test_get_holub_data_from_form_returns_empty_defaults(self):
        form = {"pohlavi": "1.0"}
        data = pigeon_app.get_holub_data_from_form(form)
        self.assertEqual(data["pohlavi"], "1.0")
        self.assertEqual(data["plemeno"], "")
        self.assertEqual(data["barva"], "")
        self.assertEqual(data["bydliste"], "")
