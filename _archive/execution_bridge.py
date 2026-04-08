# EPOS GOVERNANCE WATERMARK
# File: C:/Users/Jamie/workspace/epos_mcp/engine\execution_bridge.py
# Constitutional Authority: EPOS Constitution v3.1
# Governed: True
# Note: Legacy file — migration to root scheduled Sprint 5
# File: C:\Users\Jamie\workspace\epos_mcp\execution_bridge.py

from abc import ABC, abstractmethod
import json
import logging
from pathlib import Path
from typing import Dict, Any

# Configure logging — use absolute path per Article II Rule 1
_EPOS_ROOT = Path(__file__).resolve().parent.parent
_LOG_PATH = _EPOS_ROOT / "ops" / "logs" / "execution_bridge.log"
_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename=str(_LOG_PATH)
)
logger = logging.getLogger(__name__)

class ExecutionBridge(ABC):
    """
    Abstract base class for mission execution bridges
    Enforces a standard interface for mission execution across different agents
    """
    
    @abstractmethod
    def execute(self, mission):
        """
        Execute a mission
        
        Args:
            mission: Mission specification object
        
        Returns:
            Execution result dictionary
        """
        pass
    
    @abstractmethod
    def validate(self, mission):
        """
        Validate mission before execution
        
        Args:
            mission: Mission specification object
        
        Returns:
            Boolean indicating mission validity
        """
        pass

class AgentZeroExecutionBridge(ExecutionBridge):
    """
    Execution bridge specifically for Agent Zero
    Implements mission validation and execution
    """
    
    def __init__(self, agent_bridge):
        """
        Initialize bridge with Agent Zero communication bridge
        
        Args:
            agent_bridge: Configured AgentZeroBridge instance
        """
        self.agent_bridge = agent_bridge
        logger.info("AgentZeroExecutionBridge initialized")
    
    def validate(self, mission):
        """
        Validate mission before execution
        
        Checks:
        - Mission JSON structure
        - Success criteria defined
        - Failure modes mapped
        - Agent Zero bridge reachability
        
        Args:
            mission: Mission specification object
        
        Returns:
            Boolean indicating mission validity
        """
        try:
            # 1. Basic mission JSON structure
            if not hasattr(mission, 'mission_id') or not mission.mission_id:
                logger.warning("Invalid mission: No mission ID")
                return False
            
            # 2. Success criteria check
            if not mission.success_criteria or not isinstance(mission.success_criteria, list):
                logger.warning("Invalid mission: No success criteria")
                return False
            
            # 3. Failure modes mapping
            if not mission.failure_modes or not isinstance(mission.failure_modes, list):
                logger.warning("Invalid mission: No failure modes defined")
                return False
            
            # 4. Agent Zero bridge status
            bridge_status = self.agent_bridge.status()
            if bridge_status.get('status') != 'healthy':
                logger.warning("Agent Zero bridge not ready")
                return False
            
            logger.info(f"Mission {mission.mission_id} validated successfully")
            return True
        
        except Exception as e:
            logger.error(f"Mission validation error: {e}")
            return False
    
    def execute(self, mission):
        """
        Execute mission via Agent Zero bridge
        
        Workflow:
        1. Validate mission
        2. Convert mission to JSON
        3. Execute via agent bridge
        4. Log and verify results
        
        Args:
            mission: Mission specification object
        
        Returns:
            Execution result dictionary
        """
        try:
            # 1. Validate mission before execution
            if not self.validate(mission):
                logger.error(f"Mission {mission.mission_id} failed validation")
                return {
                    "status": "rejected",
                    "reason": "Mission validation failed"
                }
            
            # 2. Prepare mission for execution
            mission_json = mission.to_json()
            logger.info(f"Executing mission: {mission.mission_id}")
            
            # 3. Execute via Agent Zero bridge
            result = self.agent_bridge.execute(json.loads(mission_json))
            
            # 4. Verify result against success criteria
            success_status = self._check_success_criteria(mission, result)
            
            # 5. Log execution details
            logger.info(f"Mission {mission.mission_id} completed with status: {success_status}")
            
            return {
                "status": success_status,
                **result
            }
        
        except Exception as e:
            logger.error(f"Mission execution error: {e}")
            return {
                "status": "failed",
                "reason": str(e),
                "mission_id": mission.mission_id
            }
    
    def _check_success_criteria(self, mission, result):
        """
        Check mission result against predefined success criteria
        
        Args:
            mission: Mission specification object
            result: Execution result dictionary
        
        Returns:
            Mission completion status: 'success', 'partial', or 'failed'
        """
        try:
            criteria_met = 0
            total_criteria = len(mission.success_criteria)
            
            for criterion in mission.success_criteria:
                # Simple check - can be expanded with more complex logic
                if criterion.lower() in str(result).lower():
                    criteria_met += 1
            
            # Determine mission status
            if criteria_met == total_criteria:
                return "success"
            elif criteria_met > 0:
                return "partial"
            else:
                return "failed"
        
        except Exception as e:
            logger.error(f"Success criteria check error: {e}")
            return "failed"