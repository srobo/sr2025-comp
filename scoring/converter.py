"""
Converter to assist the SRComp Scorer UI reading & writing score files.

This should be updated in tandem with `update.html` which is used to render the
scores and define the form inputs.

Required as part of a compstate, though the default implementation may suffice
for simple cases.
"""

from __future__ import annotations

from sr.comp.scorer.converter import (
    Converter as BaseConverter,
    parse_int,
    render_int,
)


class Converter(BaseConverter):
    pass
