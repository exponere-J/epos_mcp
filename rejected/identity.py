from pydantic import BaseModel
from typing import List, Dict, Optional

class IdentityProfile(BaseModel):
    user_id: str
    display_name: str
    role: str  # "ARCHITECT" (Jamie) or "CREATIVE_DIRECTOR" (Stacey)
    
    # The Core Archetypes
    primary_archetype: str # e.g., "LOVER" (Creative/Connection)
    secondary_archetype: str # e.g., "QUEEN" (Sovereign/Strategy)
    
    # The Mission
    mantle: str # "I am the voice of Stories for Zayne"
    values: List[str]
    
    # Operational Rules
    work_hours: str
    preferred_voice: str # Tone for AI generation

class TenantConfig(BaseModel):
    # This separates "Exponere" from "Stories for Zayne"
    tenant_id: str
    name: str
    members: List[str] # user_ids
