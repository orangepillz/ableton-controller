"""Target-specific gate registry."""

from __future__ import annotations

from .bass import score_bass_bus, score_reese
from .drop import score_drop
from .glitch import score_glitch
from .growl import score_growl
from .kick import score_kick
from .mix import score_full_mix
from .riser import score_downlifter, score_riser, score_transition
from .snare import score_snare
from .wub import score_wub

GATES = {
    "kick": score_kick,
    "snare": score_snare,
    "wub": score_wub,
    "growl": score_growl,
    "yoi": score_growl,
    "talking-bass": score_growl,
    "bass-bus": score_bass_bus,
    "reese": score_reese,
    "glitch": score_glitch,
    "microfill": score_glitch,
    "riser": score_riser,
    "downlifter": score_downlifter,
    "drop": score_drop,
    "full-mix": score_full_mix,
    "transition": score_transition,
}

SUPPORTED_TARGETS = tuple(sorted(GATES))
