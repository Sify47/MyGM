import json
import tempfile
import unittest
from pathlib import Path

from config import Config
from data.save_manager import SaveManager
from game.game_manager import GameManager


class GameplayFoundationTests(unittest.TestCase):
    def test_ai_has_independent_roster(self):
        gm = GameManager.new_game("Test League", seed=1)
        player_ids = {w.id for w in gm.state.roster}
        ai_ids = {w.id for w in gm.state.ai_roster}

        self.assertEqual(len(gm.state.roster), 20)
        self.assertEqual(len(gm.state.ai_roster), Config.AI_ROSTER_SIZE)
        self.assertTrue(player_ids.isdisjoint(ai_ids))

        ai_show = gm.turn.ai_engine.book_ai_show(gm.state)
        booked_ids = [pid for m in ai_show.matches for pid in m.participant_ids]
        self.assertEqual(len(booked_ids), len(set(booked_ids)))
        self.assertTrue(set(booked_ids).issubset(ai_ids))

    def test_ai_roster_survives_save_load(self):
        gm = GameManager.new_game("Save Test", seed=2)
        with tempfile.TemporaryDirectory() as tmp:
            save_path = Path(tmp) / "save.json"
            SaveManager().save(gm.state, str(save_path))
            loaded = SaveManager().load(str(save_path))

        self.assertIsNotNone(loaded)
        self.assertEqual(
            [w.name for w in loaded.ai_roster],
            [w.name for w in gm.state.ai_roster],
        )

    def test_bankruptcy_counter_increments_once_per_week(self):
        gm = GameManager.new_game("Bankruptcy Test", seed=3)
        gm.state.player_budget = -1
        gm.state.negative_weeks = 0

        gm.end_week()

        self.assertEqual(gm.state.negative_weeks, 1)
        self.assertFalse(gm.is_bankrupt())

    def test_full_season_smoke(self):
        gm = GameManager.new_game("Season Test", seed=7)
        for _ in range(gm.state.season_length):
            show = gm.auto_build_show()
            self.assertGreaterEqual(len(show.matches), 1)
            gm.simulate_player_show(show)
            gm.run_ai_turn()
            gm.end_week()

        self.assertTrue(gm.is_season_over())
        self.assertEqual(len(gm.state.shows), gm.state.season_length)
        self.assertEqual(len(gm.state.ai_roster), Config.AI_ROSTER_SIZE)

    def test_featured_story_returns_story_update(self):
        from core.enums import StoryType, MatchImportance, MatchType
        from domain.engines import StoryBuilder

        gm = GameManager.new_game("Story Test", seed=4)
        men = [w for w in gm.state.roster if w.gender.value == "MALE"]
        story = StoryBuilder(gm.state).create_story(
            StoryType.CHAMPION_VS_CHALLENGER,
            [men[0].id, men[1].id],
            title="Test Crown Story",
        )
        show = gm.booking.create_show()
        gm.booking.add_match(
            show,
            match_type=MatchType.SINGLES,
            participant_ids=[men[0].id, men[1].id],
            importance=MatchImportance.MAIN_EVENT,
            story_id=story.id,
        )

        result = gm.simulate_player_show(show)

        self.assertEqual(len(result["story_updates"]), 1)
        self.assertEqual(result["story_updates"][0]["title"], "Test Crown Story")
        self.assertGreaterEqual(result["story_updates"][0]["heat"], 30)

    def test_segments_change_story_heat_and_wrestler_state(self):
        from core.enums import MatchImportance, MatchType, StoryType
        from domain.engines import StoryBuilder

        gm = GameManager.new_game("Segments Test", seed=5)
        men = [w for w in gm.state.roster if w.gender.value == "MALE"]
        story = StoryBuilder(gm.state).create_story(
            StoryType.BETRAYAL,
            [men[0].id, men[1].id],
            title="The Betrayal Test",
        )
        show = gm.booking.create_show()
        gm.booking.add_segment(
            show, "PROMO", [men[0].id], story_id=story.id
        )
        gm.booking.add_segment(
            show, "BACKSTAGE_ATTACK", [men[0].id, men[1].id], story_id=story.id
        )
        gm.booking.add_match(
            show,
            MatchType.SINGLES,
            [men[0].id, men[1].id],
            MatchImportance.MAIN_EVENT,
            story_id=story.id,
        )

        result = gm.simulate_player_show(show)

        self.assertEqual(len(result["segments"]), 2)
        self.assertGreater(story.heat, 30)
        self.assertLess(men[1].health, 100)
        self.assertTrue(any("BACKSTAGE_ATTACK" in item["type"] for item in result["segments"]))


if __name__ == "__main__":
    unittest.main()
