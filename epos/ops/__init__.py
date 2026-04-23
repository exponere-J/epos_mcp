# EPOS Artifact — Operations Core
# Constitutional Authority: EPOS_CONSTITUTION_v3.1 Articles V, X
"""epos.ops — supervisory monitoring, client health, talking points, briefings."""
from .supervisory_monitor import SupervisoryMonitor, ClientState, run_pass
from .talking_point_cards import TalkingPointCardGenerator, generate_card
from .client_health_scoring import ClientHealthScorer, score_all
from .friday_client_briefing import FridayClientBriefing, build_briefing

__all__ = [
    "SupervisoryMonitor", "ClientState", "run_pass",
    "TalkingPointCardGenerator", "generate_card",
    "ClientHealthScorer", "score_all",
    "FridayClientBriefing", "build_briefing",
]
