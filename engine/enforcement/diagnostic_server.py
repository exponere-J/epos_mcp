# EPOS GOVERNANCE WATERMARK
# File: /mnt/c/Users/Jamie/workspace/epos_mcp/engine/enforcement/diagnostic_server.py
"""
EPOS Diagnostic Server - Through the Looking Glass
Constitutional Authority: NODE_SOVEREIGNTY_CONSTITUTION.md Article III

This server powers the $497 Through the Looking Glass diagnostic:
1. Analyzes client needs
2. Maps to node capabilities
3. Generates engagement recommendations
4. Calculates constitutional pricing
"""

from pathlib import Path
from datetime import datetime
import json
import os
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, asdict
from enum import Enum

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from event_bus import get_event_bus
except ImportError:
    get_event_bus = None


class PricingTier(Enum):
    """Pricing tiers per NODE_SOVEREIGNTY_CONSTITUTION Article IV."""
    INDIVIDUAL = "individual"  # No discount
    BUNDLE = "bundle"          # 20-30% discount
    DEPARTMENT = "department"  # 30-40% discount
    ENTERPRISE = "enterprise"  # Custom


@dataclass
class Node:
    """An EPOS node definition."""
    node_id: str
    display_name: str
    description: str
    capabilities: List[str]
    price_monthly: float
    sovereignty_certified: bool
    port: int
    status: str  # "active", "planned", "deprecated"


@dataclass
class EngagementOption:
    """A recommended engagement option."""
    name: str
    nodes: List[str]
    total_price: float
    individual_total: float
    discount_percent: float
    fit_score: float
    reasoning: str
    constitutional_compliance: bool


@dataclass
class DiagnosticResult:
    """Result of a Through the Looking Glass diagnostic."""
    diagnostic_id: str
    client_needs: List[str]
    budget_range: Tuple[float, float]
    recommended_engagements: List[EngagementOption]
    minimum_viable: Optional[EngagementOption]
    recommended: Optional[EngagementOption]
    complete: Optional[EngagementOption]
    created_at: str


# Node registry (would normally be loaded from nodes_registry.json)
DEFAULT_NODES = [
    Node(
        node_id="research_engine",
        display_name="Research Engine Pro",
        description="Standalone competitive intelligence tool",
        capabilities=["market_intelligence", "competitor_tracking", "trend_detection", "keyword_monitoring"],
        price_monthly=49.00,
        sovereignty_certified=True,
        port=8010,
        status="planned"
    ),
    Node(
        node_id="analysis_engine",
        display_name="Analysis Intelligence API",
        description="Market sentiment analysis service",
        capabilities=["sentiment_analysis", "engagement_prediction", "trend_detection", "webhook_integration"],
        price_monthly=97.00,
        sovereignty_certified=True,
        port=8011,
        status="planned"
    ),
    Node(
        node_id="content_generator",
        display_name="Content Generator Studio",
        description="Automated content repurposing",
        capabilities=["content_creation", "multi_platform", "brand_voice", "template_library"],
        price_monthly=79.00,
        sovereignty_certified=True,
        port=8012,
        status="planned"
    ),
    Node(
        node_id="validation_engine",
        display_name="Validation Compliance Suite",
        description="Brand voice enforcement",
        capabilities=["compliance_checking", "brand_validation", "audit_trail", "rule_engine"],
        price_monthly=59.00,
        sovereignty_certified=True,
        port=8013,
        status="planned"
    ),
    Node(
        node_id="publisher_orchestrator",
        display_name="Publisher Automation",
        description="Multi-platform scheduling",
        capabilities=["scheduling", "rate_limiting", "analytics", "rollback"],
        price_monthly=39.00,
        sovereignty_certified=True,
        port=8014,
        status="planned"
    ),
    Node(
        node_id="market_awareness",
        display_name="Market Awareness Engine",
        description="Real-time market intelligence",
        capabilities=["market_monitoring", "feedback_analysis", "opportunity_detection"],
        price_monthly=67.00,
        sovereignty_certified=True,
        port=8015,
        status="planned"
    ),
    Node(
        node_id="linkedin_strategist",
        display_name="LinkedIn Content Strategist",
        description="LinkedIn-optimized content",
        capabilities=["linkedin_content", "professional_tone", "b2b_marketing"],
        price_monthly=49.00,
        sovereignty_certified=True,
        port=8020,
        status="planned"
    ),
    Node(
        node_id="governance_server",
        display_name="Governance Coaching Service",
        description="Constitutional compliance coaching",
        capabilities=["compliance_training", "violation_remediation", "quality_assurance"],
        price_monthly=197.00,
        sovereignty_certified=True,
        port=8100,
        status="active"
    ),
]


class PricingCalculator:
    """
    Calculates constitutional pricing for node bundles.
    
    Constitutional Authority: NODE_SOVEREIGNTY_CONSTITUTION Article IV
    
    Pricing Rules:
    - Individual nodes: No discount
    - Bundles (2-4 nodes): 20-30% discount
    - Departments (5+ nodes): 30-40% discount
    - Enterprise: Custom pricing
    """
    
    BUNDLE_DISCOUNT_MIN = 0.20
    BUNDLE_DISCOUNT_MAX = 0.30
    DEPARTMENT_DISCOUNT_MIN = 0.30
    DEPARTMENT_DISCOUNT_MAX = 0.40
    
    def __init__(self, nodes: List[Node] = None):
        self.nodes = {n.node_id: n for n in (nodes or DEFAULT_NODES)}
    
    def calculate_bundle_price(
        self,
        node_ids: List[str],
        tier: str = "auto"
    ) -> Dict[str, Any]:
        """
        Calculate constitutionally compliant bundle price.
        
        Args:
            node_ids: List of node IDs to bundle
            tier: Pricing tier ("auto", "bundle", "department", "enterprise")
        
        Returns:
            Pricing details dict
        """
        # Get nodes
        selected_nodes = [self.nodes[nid] for nid in node_ids if nid in self.nodes]
        if not selected_nodes:
            return {"error": "No valid nodes selected"}
        
        # Calculate individual total
        individual_total = sum(n.price_monthly for n in selected_nodes)
        
        # Determine tier
        if tier == "auto":
            if len(selected_nodes) == 1:
                tier = "individual"
            elif len(selected_nodes) <= 4:
                tier = "bundle"
            else:
                tier = "department"
        
        # Apply discount
        if tier == "individual":
            discount_percent = 0.0
        elif tier == "bundle":
            # Use midpoint of range
            discount_percent = (self.BUNDLE_DISCOUNT_MIN + self.BUNDLE_DISCOUNT_MAX) / 2
        elif tier == "department":
            discount_percent = (self.DEPARTMENT_DISCOUNT_MIN + self.DEPARTMENT_DISCOUNT_MAX) / 2
        else:  # enterprise
            discount_percent = 0.40  # Custom
        
        bundle_price = individual_total * (1 - discount_percent)
        savings = individual_total - bundle_price
        
        # Validate constitutional compliance
        compliant = True
        rule_applied = f"Article IV: {tier.capitalize()} pricing"
        
        if tier == "bundle" and not (self.BUNDLE_DISCOUNT_MIN <= discount_percent <= self.BUNDLE_DISCOUNT_MAX):
            compliant = False
            rule_applied = f"ERROR: Discount {discount_percent:.0%} outside 20-30% range"
        elif tier == "department" and not (self.DEPARTMENT_DISCOUNT_MIN <= discount_percent <= self.DEPARTMENT_DISCOUNT_MAX):
            compliant = False
            rule_applied = f"ERROR: Discount {discount_percent:.0%} outside 30-40% range"
        
        return {
            "node_ids": node_ids,
            "node_count": len(selected_nodes),
            "tier": tier,
            "individual_total": round(individual_total, 2),
            "discount_percent": round(discount_percent * 100, 1),
            "bundle_price": round(bundle_price, 2),
            "savings": round(savings, 2),
            "constitutional_compliance": {
                "compliant": compliant,
                "rule_applied": rule_applied
            }
        }


class DiagnosticEngine:
    """
    Powers Through the Looking Glass with automated recommendations.
    
    Constitutional Authority: NODE_SOVEREIGNTY_CONSTITUTION Article III
    """
    
    DEFAULT_EPOS_ROOT = Path(os.getenv("EPOS_ROOT", str(Path(__file__).resolve().parent.parent.parent)))
    
    # Capability keywords mapping
    CAPABILITY_KEYWORDS = {
        "market intelligence": ["market_intelligence", "competitor_tracking", "trend_detection"],
        "content creation": ["content_creation", "multi_platform", "template_library"],
        "linkedin": ["linkedin_content", "b2b_marketing", "professional_tone"],
        "analytics": ["sentiment_analysis", "engagement_prediction", "analytics"],
        "compliance": ["compliance_checking", "brand_validation", "quality_assurance"],
        "automation": ["scheduling", "rate_limiting", "webhook_integration"],
        "training": ["compliance_training", "violation_remediation"],
    }
    
    def __init__(self, nodes: List[Node] = None):
        self.nodes = nodes or DEFAULT_NODES
        self.pricing = PricingCalculator(self.nodes)
        self.event_bus = get_event_bus() if get_event_bus else None
    
    def run_diagnostic(
        self,
        client_needs: List[str],
        budget_min: float,
        budget_max: float,
        trace_id: str = None
    ) -> DiagnosticResult:
        """
        Run Through the Looking Glass diagnostic.
        
        Args:
            client_needs: List of client requirement keywords
            budget_min: Minimum budget
            budget_max: Maximum budget
            trace_id: Trace ID for correlation
        
        Returns:
            DiagnosticResult with 3 engagement options
        """
        diagnostic_id = f"DIAG_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Publish diagnostic started event
        if self.event_bus:
            self.event_bus.publish(
                event_type="diagnostic.started",
                payload={
                    "diagnostic_id": diagnostic_id,
                    "client_needs": client_needs,
                    "budget_range": [budget_min, budget_max]
                },
                metadata={"trace_id": trace_id},
                source_server="diagnostic_server"
            )
        
        # Map needs to capabilities
        required_capabilities = self._map_needs_to_capabilities(client_needs)
        
        # Find nodes that match capabilities
        matching_nodes = self._find_matching_nodes(required_capabilities)
        
        # Generate engagement options
        options = self._generate_options(matching_nodes, budget_min, budget_max, client_needs)
        
        # Sort by fit score
        options.sort(key=lambda o: o.fit_score, reverse=True)
        
        # Categorize options
        minimum_viable = None
        recommended = None
        complete = None
        
        for opt in options:
            if opt.total_price <= budget_min * 1.1 and not minimum_viable:
                minimum_viable = opt
            elif budget_min <= opt.total_price <= budget_max and not recommended:
                recommended = opt
            elif opt.total_price > budget_max * 0.9 and not complete:
                complete = opt
        
        # If no recommended, use highest fit score within budget
        if not recommended and options:
            budget_options = [o for o in options if budget_min <= o.total_price <= budget_max]
            if budget_options:
                recommended = max(budget_options, key=lambda o: o.fit_score)
        
        result = DiagnosticResult(
            diagnostic_id=diagnostic_id,
            client_needs=client_needs,
            budget_range=(budget_min, budget_max),
            recommended_engagements=options[:5],  # Top 5 options
            minimum_viable=minimum_viable,
            recommended=recommended,
            complete=complete,
            created_at=datetime.now().isoformat()
        )
        
        # Publish diagnostic completed event
        if self.event_bus:
            self.event_bus.publish(
                event_type="diagnostic.engagement_created",
                payload={
                    "diagnostic_id": diagnostic_id,
                    "options_count": len(options),
                    "recommended_price": recommended.total_price if recommended else None
                },
                metadata={"trace_id": trace_id},
                source_server="diagnostic_server"
            )
        
        return result
    
    def _map_needs_to_capabilities(self, needs: List[str]) -> List[str]:
        """Map client needs to capability keywords."""
        capabilities = set()
        
        for need in needs:
            need_lower = need.lower()
            for keyword, caps in self.CAPABILITY_KEYWORDS.items():
                if keyword in need_lower or any(c in need_lower for c in caps):
                    capabilities.update(caps)
        
        return list(capabilities)
    
    def _find_matching_nodes(self, required_capabilities: List[str]) -> List[Node]:
        """Find nodes that match required capabilities."""
        matching = []
        
        for node in self.nodes:
            overlap = set(node.capabilities) & set(required_capabilities)
            if overlap:
                matching.append((node, len(overlap)))
        
        # Sort by number of matching capabilities
        matching.sort(key=lambda x: x[1], reverse=True)
        return [n for n, _ in matching]
    
    def _generate_options(
        self,
        matching_nodes: List[Node],
        budget_min: float,
        budget_max: float,
        client_needs: List[str]
    ) -> List[EngagementOption]:
        """Generate engagement options from matching nodes."""
        options = []
        
        # Option 1: Minimum (1-2 nodes)
        if len(matching_nodes) >= 1:
            min_nodes = matching_nodes[:2]
            pricing = self.pricing.calculate_bundle_price(
                [n.node_id for n in min_nodes],
                tier="auto"
            )
            
            options.append(EngagementOption(
                name="Starter Package",
                nodes=[n.node_id for n in min_nodes],
                total_price=pricing["bundle_price"],
                individual_total=pricing["individual_total"],
                discount_percent=pricing["discount_percent"],
                fit_score=self._calculate_fit_score(min_nodes, client_needs, budget_min, budget_max),
                reasoning=f"Core capabilities with {len(min_nodes)} nodes",
                constitutional_compliance=pricing["constitutional_compliance"]["compliant"]
            ))
        
        # Option 2: Recommended (3-4 nodes)
        if len(matching_nodes) >= 3:
            rec_nodes = matching_nodes[:4]
            pricing = self.pricing.calculate_bundle_price(
                [n.node_id for n in rec_nodes],
                tier="bundle"
            )
            
            options.append(EngagementOption(
                name="Professional Package",
                nodes=[n.node_id for n in rec_nodes],
                total_price=pricing["bundle_price"],
                individual_total=pricing["individual_total"],
                discount_percent=pricing["discount_percent"],
                fit_score=self._calculate_fit_score(rec_nodes, client_needs, budget_min, budget_max),
                reasoning=f"Optimal coverage with {len(rec_nodes)} nodes and {pricing['discount_percent']}% bundle discount",
                constitutional_compliance=pricing["constitutional_compliance"]["compliant"]
            ))
        
        # Option 3: Complete (5+ nodes)
        if len(matching_nodes) >= 5:
            comp_nodes = matching_nodes[:6]
            pricing = self.pricing.calculate_bundle_price(
                [n.node_id for n in comp_nodes],
                tier="department"
            )
            
            options.append(EngagementOption(
                name="Enterprise Package",
                nodes=[n.node_id for n in comp_nodes],
                total_price=pricing["bundle_price"],
                individual_total=pricing["individual_total"],
                discount_percent=pricing["discount_percent"],
                fit_score=self._calculate_fit_score(comp_nodes, client_needs, budget_min, budget_max),
                reasoning=f"Full capability with {len(comp_nodes)} nodes and {pricing['discount_percent']}% department discount",
                constitutional_compliance=pricing["constitutional_compliance"]["compliant"]
            ))
        
        return options
    
    def _calculate_fit_score(
        self,
        nodes: List[Node],
        client_needs: List[str],
        budget_min: float,
        budget_max: float
    ) -> float:
        """Calculate how well an option fits client needs and budget."""
        # Capability coverage (0-0.5)
        all_capabilities = set()
        for node in nodes:
            all_capabilities.update(node.capabilities)
        
        required_capabilities = self._map_needs_to_capabilities(client_needs)
        coverage = len(all_capabilities & set(required_capabilities)) / max(len(required_capabilities), 1)
        capability_score = coverage * 0.5
        
        # Budget fit (0-0.5)
        total_price = sum(n.price_monthly for n in nodes)
        if total_price < budget_min:
            budget_score = 0.3  # Under budget is okay but not ideal
        elif total_price <= budget_max:
            # Prefer options closer to budget midpoint
            midpoint = (budget_min + budget_max) / 2
            distance = abs(total_price - midpoint) / (budget_max - budget_min)
            budget_score = 0.5 * (1 - distance)
        else:
            budget_score = 0.1  # Over budget
        
        return round(capability_score + budget_score, 2)
    
    def generate_engagement_manifest(
        self,
        option: EngagementOption,
        client_id: str,
        trace_id: str = None
    ) -> Dict[str, Any]:
        """Generate a formal engagement manifest."""
        manifest = {
            "engagement_id": f"ENG_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{client_id}",
            "client_id": client_id,
            "active_nodes": [
                {
                    "node_id": nid,
                    "role": "active",
                    "allocation": "monthly"
                }
                for nid in option.nodes
            ],
            "financials": {
                "total_price": option.total_price,
                "individual_total": option.individual_total,
                "discount_percent": option.discount_percent,
                "savings": round(option.individual_total - option.total_price, 2)
            },
            "constitutional_compliance": option.constitutional_compliance,
            "created_at": datetime.now().isoformat(),
            "trace_id": trace_id
        }
        
        return manifest


class DiagnosticServer:
    """Main diagnostic server."""
    
    def __init__(self):
        self.event_bus = get_event_bus() if get_event_bus else None
        self.engine = DiagnosticEngine()
        self._running = False
    
    def start(self):
        if not self.event_bus:
            print("[DiagnosticServer] Warning: Event bus not available")
            return
        
        self.event_bus.start_polling()
        self._running = True
        print("[DiagnosticServer] Started")
    
    def stop(self):
        self._running = False
        if self.event_bus:
            self.event_bus.stop_polling()
        print("[DiagnosticServer] Stopped")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="EPOS Diagnostic Server")
    parser.add_argument("--test", action="store_true", help="Run self-test")
    parser.add_argument("--pricing", nargs="+", help="Calculate pricing for nodes")
    
    args = parser.parse_args()
    
    if args.pricing:
        calc = PricingCalculator()
        result = calc.calculate_bundle_price(args.pricing)
        print("\n💰 Pricing Calculation")
        print("=" * 40)
        for k, v in result.items():
            print(f"  {k}: {v}")
    
    elif args.test:
        print("\n🔍 Diagnostic Engine Self-Test")
        print("=" * 40)
        
        engine = DiagnosticEngine()
        
        result = engine.run_diagnostic(
            client_needs=["market intelligence", "linkedin content", "analytics"],
            budget_min=200,
            budget_max=500
        )
        
        print(f"\n  Diagnostic ID: {result.diagnostic_id}")
        print(f"  Options generated: {len(result.recommended_engagements)}")
        
        if result.recommended:
            print(f"\n  Recommended:")
            print(f"    Name: {result.recommended.name}")
            print(f"    Price: ${result.recommended.total_price}")
            print(f"    Fit Score: {result.recommended.fit_score}")
            print(f"    Nodes: {result.recommended.nodes}")
        
        print("\n✅ Self-test complete!")
    
    else:
        print("Use --test for self-test or --pricing NODE1 NODE2 ... for pricing")
