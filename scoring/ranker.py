from __future__ import annotations

from typing import Collection, Mapping

from league_ranker import LeaguePoints, RankedPosition, TZone
from sr.comp.ranker import LeagueRanker
from sr.comp.types import MatchId, MatchNumber

FIRST_PHYSICAL_MATCH_NUMBER = MatchNumber(23)


class Ranker(LeagueRanker):
    def calc_ranked_points(
        self,
        positions: Mapping[RankedPosition, Collection[TZone]],
        *,
        disqualifications: Collection[TZone],
        num_zones: int,
        match_id: MatchId,
    ) -> dict[TZone, LeaguePoints]:
        points = super().calc_ranked_points(
            positions,
            disqualifications=disqualifications,
            num_zones=num_zones,
            match_id=match_id,
        )

        # Physical league matches are worth double for SR2025
        _, match_number = match_id
        if match_number >= FIRST_PHYSICAL_MATCH_NUMBER:
            return {k: LeaguePoints(v * 2) for k, v in points.items()}

        return points
