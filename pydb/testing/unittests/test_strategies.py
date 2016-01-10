# coding=utf-8
import unittest
import pydb.com.strategies as strategies


class TestStrategyPackage(unittest.TestCase):
    def test_strategy_phase_id_valid(self):
        name = 'requesting_metadata'
        strategy_id = strategies.strategy_phase_id(name)
        self.assertEquals(21, strategy_id)

    def test_strategy_phase_name_valid(self):
        name = 'requesting_metadata'
        strategy_id = 21

        strategy_name = strategies.strategy_phase_name(strategy_id)
        self.assertEquals(name, strategy_name)

    def test_strategy_phase_name_invalid_raises_key_error(self):
        with self.assertRaises(KeyError):
            strategies.strategy_phase_id('i do not exist')

    def test_strategy_phase_id_invalid_raises_keyerror(self):
        with self.assertRaises(KeyError):
            strategies.strategy_phase_name(123132)
