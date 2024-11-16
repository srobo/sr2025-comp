"""
Converter to assist the SRComp Scorer UI reading & writing score files.

This should be updated in tandem with `update.html` which is used to render the
scores and define the form inputs.

Required as part of a compstate, though the default implementation may suffice
for simple cases.
"""

from __future__ import annotations

from sr.comp.match_period import Match
from sr.comp.scorer.converter import (
    Converter as BaseConverter,
    InputForm,
    OutputForm,
    ZoneId,
)
from sr.comp.types import ScoreArenaZonesData, ScoreData, ScoreTeamData, TLA

from sr2025 import DISTRICTS, RawDistrict


class SR2025ScoreTeamData(ScoreTeamData):
    left_starting_zone: bool


class Converter(BaseConverter):
    """
    Base class for converting between representations of a match's score.
    """

    def form_team_to_score(self, form: InputForm, zone_id: ZoneId) -> SR2025ScoreTeamData:
        """
        Prepare a team's scoring data for saving in a score dict.

        This is given a zone as form data is all keyed by zone.
        """
        return {
            **super().form_team_to_score(form, zone_id),
            'left_starting_zone':
                form.get(f'left_starting_zone_{zone_id}', None) is not None,
        }

    def form_district_to_score(self, form: InputForm, name: str) -> RawDistrict:
        """
        Prepare a district's scoring data for saving in a score dict.
        """
        return RawDistrict({
            'highest': form.get(f'district_{name}_highest', ''),
            'pallets': form.get(f'district_{name}_pallets', ''),
        })

    def form_to_score(self, match: Match, form: InputForm) -> ScoreData:
        """
        Prepare a score dict for the given match and form dict.

        This method is used to convert the submitted information for storage as
        YAML in the compstate.
        """
        zone_ids = range(len(match.teams))

        teams: dict[TLA, ScoreTeamData] = {}
        for zone_id in zone_ids:
            tla = form.get(f'tla_{zone_id}', None)
            if tla:
                teams[TLA(tla)] = self.form_team_to_score(form, zone_id)

        arena = ScoreArenaZonesData({
            'other': {
                'districts': {
                    district: self.form_district_to_score(form, district)
                    for district in DISTRICTS
                },
            },
        })

        return ScoreData({
            'arena_id': match.arena,
            'match_number': match.num,
            'teams': teams,
            'arena_zones': arena,
        })

    def score_team_to_form(self, tla: TLA, info: ScoreTeamData) -> OutputForm:
        zone_id = info['zone']
        return {
            **super().score_team_to_form(tla, info),
            f'left_starting_zone_{zone_id}': info.get('left_starting_zone', False),
        }

    def score_district_to_form(self, name: str, district: RawDistrict) -> OutputForm:
        return OutputForm({
            f'district_{name}_highest': district['highest'].upper(),
            f'district_{name}_pallets': district['pallets'].upper(),
        })

    def score_to_form(self, score: ScoreData) -> OutputForm:
        """
        Prepare a form dict for the given score dict.

        This method is used when there is an existing score for a match.
        """
        form = OutputForm({})

        for tla, team_info in score['teams'].items():
            form.update(self.score_team_to_form(tla, team_info))

        districts = score.get('arena_zones', {}).get('other', {}).get('districts', {})  # type: ignore[attr-defined, union-attr, call-overload]  # noqa: E501

        for name, district in districts.items():
            form.update(self.score_district_to_form(name, district))

        return form

    def match_to_form(self, match: Match) -> OutputForm:
        """
        Prepare a fresh form dict for the given match.

        This method is used when there is no existing score for a match.
        """

        form = OutputForm({})

        for zone_id, tla in enumerate(match.teams):
            if tla:
                form[f'tla_{zone_id}'] = tla
                form[f'disqualified_{zone_id}'] = False
                form[f'present_{zone_id}'] = False
                form[f'left_starting_zone_{zone_id}'] = False

        for name in DISTRICTS:
            form[f'district_{name}_highest'] = ''
            form[f'district_{name}_pallets'] = ''

        return form
