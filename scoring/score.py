"""
Scoring calculator used to assign points.

Required as part of a compstate.
"""

import warnings


class InvalidScoresheetException(Exception):
    def __init__(self, message: str, *, code: str) -> None:
        super().__init__(message)
        self.code = code


class Scorer:
    def __init__(self, teams_data, arena_data):
        self._teams_data = teams_data
        self._arena_data = arena_data

    def calculate_scores(self):
        scores = {}

        for tla, info in self._teams_data.items():
            scores[tla] = 0

        return scores

    def validate(self, other_data):
        warnings.warn("Scoresheet validation not implemented")


if __name__ == '__main__':
    import libproton
    libproton.main(Scorer)
