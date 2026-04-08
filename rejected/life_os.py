import asyncio
from datetime import datetime
from epos_hq.kernel.types.identity import IdentityProfile

class LifeOSEngine:
    def __init__(self, profile: IdentityProfile):
        self.profile = profile
        self.current_state = "neutral"
    
    def get_active_archetype(self, hour: int):
        """
        Determines which archetype should be active based on time of day.
        """
        # Simple heuristic for V1 (make this configurable later)
        if 5 <= hour < 9:
            return "WARRIOR" # Morning Discipline
        elif 9 <= hour < 17:
            return "SOVEREIGN" # Business Strategy
        elif 17 <= hour < 20:
            return "FATHER" # Family Time
        else:
            return "LOVER" # Creative/Rest
            
    def generate_nudge(self):
        """
        Creates a context-aware nudge.
        """
        now = datetime.now()
        archetype = self.get_active_archetype(now.hour)
        
        nudge = {
            "timestamp": now.isoformat(),
            "archetype": archetype,
            "message": f"Time to embody the {archetype}. Check your alignment.",
            "voice": self.profile.preferred_voice
        }
        return nudge

# Mock Profile for testing
mock_profile = IdentityProfile(
    user_id="jamie",
    display_name="Jamie",
    role="ARCHITECT",
    primary_archetype="SOVEREIGN",
    secondary_archetype="WARRIOR",
    mantle="Build the Sovereign Future",
    values=["Truth", "Speed", "Ownership"],
    work_hours="09:00-17:00",
    preferred_voice="Direct and stoic"
)

life_engine = LifeOSEngine(mock_profile)
