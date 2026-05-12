import unittest
from unittest.mock import Mock, patch

from exceptions import WrongPigeonGenderException
from neo_db import NeoDb
from utils import PigeonGender


def _mock_result(data_value):
    result = Mock()
    result.data.return_value = data_value
    return result


class TestNeoDb(unittest.TestCase):
    def setUp(self):
        self.db = Mock()

    def test_get_pigeon_by_id_returns_node(self):
        self.db.run.return_value = _mock_result([{"pigeon": {"id": "1-ABC-01"}}])
        result = NeoDb.get_pigeon_by_id(self.db, "1-ABC-01")
        self.assertEqual(result, {"id": "1-ABC-01"})
        self.assertIn("MATCH (p:Pigeon {id: $id })", self.db.run.call_args[0][0])
        self.assertEqual(self.db.run.call_args[1], {"id": "1-ABC-01"})

    def test_get_pigeon_by_id_returns_none(self):
        self.db.run.return_value = _mock_result([])
        result = NeoDb.get_pigeon_by_id(self.db, "1-ABC-01")
        self.assertIsNone(result)
        self.assertEqual(self.db.run.call_args[1], {"id": "1-ABC-01"})

    def test_get_mother_of_pigeon_returns_node(self):
        self.db.run.return_value = _mock_result([{"mother": {"id": "1-ABC-02"}}])
        result = NeoDb.get_mother_of_pigeon(self.db, "1-ABC-01")
        self.assertEqual(result, {"id": "1-ABC-02"})
        self.assertIn("MATCH (m:Pigeon)-[:MATKA]->", self.db.run.call_args[0][0])
        self.assertEqual(self.db.run.call_args[1], {"id": "1-ABC-01"})

    def test_get_father_of_pigeon_returns_node(self):
        self.db.run.return_value = _mock_result([{"father": {"id": "1-ABC-03"}}])
        result = NeoDb.get_father_of_pigeon(self.db, "1-ABC-01")
        self.assertEqual(result, {"id": "1-ABC-03"})
        self.assertIn("MATCH (f:Pigeon)-[:OTEC]->", self.db.run.call_args[0][0])
        self.assertEqual(self.db.run.call_args[1], {"id": "1-ABC-01"})

    def test_add_parent_existing_parent_gender_matches(self):
        first = _mock_result([{"pigeon": {"pohlavi": "1.0"}}])
        self.db.run.side_effect = [first, Mock()]
        NeoDb.add_parent(self.db, "1-ABC-01", "1-ABC-02", PigeonGender.HOLUB)
        self.assertEqual(self.db.run.call_count, 2)
        self.assertIn("MATCH (a:Pigeon) WHERE a.id = $id RETURN a AS pigeon", self.db.run.call_args_list[0][0][0])
        self.assertEqual(self.db.run.call_args_list[0][1], {"id": "1-ABC-02"})
        self.assertIn("CREATE (a)-[r:OTEC]->(b)", self.db.run.call_args_list[1][0][0])
        self.assertEqual(self.db.run.call_args_list[1][1], {"parent_id": "1-ABC-02", "pigeon_id": "1-ABC-01"})

    def test_add_parent_existing_parent_gender_mismatch_raises(self):
        self.db.run.return_value = _mock_result([{"pigeon": {"pohlavi": "0.1"}}])
        with self.assertRaises(WrongPigeonGenderException):
            NeoDb.add_parent(self.db, "1-ABC-01", "1-ABC-02", PigeonGender.HOLUB)

    def test_add_parent_creates_parent_and_relationship_when_missing(self):
        empty = _mock_result([])
        self.db.run.side_effect = [empty, Mock(), Mock()]
        NeoDb.add_parent(self.db, "1-ABC-01", "1-ABC-02", PigeonGender.HOLUB)
        self.assertEqual(self.db.run.call_count, 3)
        self.assertIn("CREATE (p:Pigeon $data )", self.db.run.call_args_list[1][0][0])
        self.assertEqual(self.db.run.call_args_list[1][1]["data"]["id"], "1-ABC-02")
        self.assertEqual(self.db.run.call_args_list[1][1]["data"]["pohlavi"], "1.0")
        self.assertIn("CREATE (a)-[r:OTEC]->(b)", self.db.run.call_args_list[2][0][0])
        self.assertEqual(self.db.run.call_args_list[2][1], {"parent_id": "1-ABC-02", "pigeon_id": "1-ABC-01"})

    def test_remove_parent_executes_expected_query(self):
        NeoDb.remove_parent(self.db, "1-ABC-01", "1-ABC-02", PigeonGender.HOLUB)
        self.db.run.assert_called_once()
        query = self.db.run.call_args[0][0]
        self.assertIn('MATCH (:Pigeon {id: "1-ABC-02"} )', query)
        self.assertIn('OTEC', query)
        self.assertIn('1-ABC-01', query)
        self.assertIn('DELETE r', query)

    def test_replace_parent_calls_remove_and_add(self):
        with patch("neo_db.NeoDb.remove_parent") as remove_parent, patch("neo_db.NeoDb.add_parent") as add_parent:
            NeoDb.replace_parent(self.db, "1-ABC-01", "1-ABC-02", "1-ABC-03", PigeonGender.HOLUB)
            remove_parent.assert_called_once_with(self.db, pigeon_id="1-ABC-01", parent_id="1-ABC-02", parent_gender=PigeonGender.HOLUB)
            add_parent.assert_called_once_with(self.db, pigeon_id="1-ABC-01", parent_id="1-ABC-03", parent_gender=PigeonGender.HOLUB)

    def test_update_parent_no_parent_no_new_parent(self):
        with patch("neo_db.NeoDb.add_parent") as add_parent, patch("neo_db.NeoDb.remove_parent") as remove_parent:
            NeoDb.update_parent(self.db, 1, "1-ABC-01", None, "", PigeonGender.HOLUB)
            add_parent.assert_not_called()
            remove_parent.assert_not_called()

    def test_update_parent_adds_new_parent_when_missing(self):
        with patch("neo_db.NeoDb.add_parent") as add_parent:
            NeoDb.update_parent(self.db, 1, "1-ABC-01", None, "XYZ/22", PigeonGender.HOLUB)
            add_parent.assert_called_once_with(self.db, pigeon_id="1-ABC-01", parent_id="1-XYZ-22", parent_gender=PigeonGender.HOLUB)

    def test_update_parent_replaces_parent_when_changed(self):
        with patch("neo_db.NeoDb.replace_parent") as replace_parent:
            NeoDb.update_parent(self.db, 1, "1-ABC-01", {"id": "1-OLD-01"}, "NEW/02", PigeonGender.HOLUB)
            replace_parent.assert_called_once_with(self.db, pigeon_id="1-ABC-01", old_parent_id="1-OLD-01", new_parent_id="1-NEW-02", parent_gender=PigeonGender.HOLUB)

    def test_update_parent_removes_parent_when_form_empty(self):
        with patch("neo_db.NeoDb.remove_parent") as remove_parent:
            NeoDb.update_parent(self.db, 1, "1-ABC-01", {"id": "1-OLD-01"}, "", PigeonGender.HOLUB)
            remove_parent.assert_called_once_with(self.db, pigeon_id="1-ABC-01", parent_id="1-OLD-01", parent_gender=PigeonGender.HOLUB)

    def test_update_pigeon_data_builds_set_query(self):
        NeoDb.update_pigeon_data(self.db, "1-ABC-01", {"plemeno": "Test", "barva": "White"})
        self.db.run.assert_called_once()
        q = self.db.run.call_args[0][0]
        self.assertIn("MATCH (p:Pigeon { id: '1-ABC-01' })", q)
        self.assertIn("SET p.plemeno = 'Test'", q)
        self.assertIn("SET p.barva = 'White'", q)

    def test_get_ancestor_paths_returns_data(self):
        self.db.run.return_value = _mock_result([{"path": [1, 2, 3]}])
        result = NeoDb.get_ancestor_paths(self.db, "1-ABC-01")
        self.assertEqual(result, [{"path": [1, 2, 3]}])
        query = self.db.run.call_args[0][0]
        self.assertIn("MATCH path=", query)
        self.assertIn("1-ABC-01", query)
        self.assertIn("*0..4", query)

    def test_calculate_inbreeding_accumulates_coefficients(self):
        self.db.run.return_value = _mock_result([{"path_length": 1}, {"path_length": 2}, {"path_length": None}])
        result = NeoDb.calculate_inbreeding(self.db, "1-ABC-01")
        self.assertAlmostEqual(result, 0.75)
        self.assertIn("MATCH (a:Pigeon {id : $id})", self.db.run.call_args[0][0])
        self.assertIn("OPTIONAL MATCH", self.db.run.call_args[0][0])
        self.assertEqual(self.db.run.call_args[1], {"id": "1-ABC-01"})
