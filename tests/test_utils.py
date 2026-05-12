import unittest

from exceptions import WrongPigeonIdFormat
from utils import (
    cislo_krouzku_full_from_id,
    pigeon_id_from_cislo_krouzku_full,
    split_pigeon_id,
    user_id_from_pigoen_id,
    check_pigeon_id_validity,
    PigeonGender,
)


class TestUtils(unittest.TestCase):
    def test_cislo_krouzku_full_from_id_valid(self):
        self.assertEqual(cislo_krouzku_full_from_id("1-ABC123-21"), "ABC123/21")

    def test_cislo_krouzku_full_from_id_invalid(self):
        with self.assertRaises(WrongPigeonIdFormat):
            cislo_krouzku_full_from_id("1-INVALID")

    def test_user_id_from_pigoen_id_valid(self):
        self.assertEqual(user_id_from_pigoen_id("17-ABC123-21"), 17)

    def test_user_id_from_pigoen_id_invalid(self):
        with self.assertRaises(WrongPigeonIdFormat):
            user_id_from_pigoen_id("nope")

    def test_split_pigeon_id_valid(self):
        self.assertEqual(split_pigeon_id("2-XYZ-33"), ["2", "XYZ", "33"])

    def test_split_pigeon_id_invalid(self):
        with self.assertRaises(WrongPigeonIdFormat):
            split_pigeon_id("bad-format")

    def test_pigeon_id_from_cislo_krouzku_full_valid(self):
        self.assertEqual(pigeon_id_from_cislo_krouzku_full("ABC123/21", 3), "3-ABC123-21")

    def test_pigeon_id_from_cislo_krouzku_full_invalid(self):
        with self.assertRaises(WrongPigeonIdFormat):
            pigeon_id_from_cislo_krouzku_full("no-slash", 1)

    def test_check_pigeon_id_validity(self):
        self.assertTrue(bool(check_pigeon_id_validity("1-ABC123-21")))
        self.assertFalse(bool(check_pigeon_id_validity("1-abc-21")))

    def test_get_gender_from_marking(self):
        self.assertEqual(PigeonGender.get_gender_from_marking("1.0"), PigeonGender.HOLUB)
        self.assertEqual(PigeonGender.get_gender_from_marking("0.1"), PigeonGender.HOLUBICE)
        self.assertIsNone(PigeonGender.get_gender_from_marking("unknown"))
