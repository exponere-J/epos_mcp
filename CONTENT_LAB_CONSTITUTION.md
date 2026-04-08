# File: C:\Users\Jamie\workspace\epos_mcp\content\CONTENT_LAB_CONSTITUTION.md

# CONTENT LAB CONSTITUTION
## Algorithmic Echolocation & Whitepaper Cascading Framework

**Version:** 1.0.0  
**Status:** Constitutional Document  
**Governance:** Must pass through governance_gate.py before execution

---

## I. CORE ARCHITECTURE PRINCIPLES

### A. Dual-Flow Content Strategy

**Bottom-Up Tributary (Algorithmic Echolocation)**
- **Source Platforms:** X (Twitter), TikTok
- **Flow Direction:** Short-form → Long-form
- **Strategy:** Capture high-engagement micro-content, algorithmically identify patterns, repurpose into deeper formats
- **Governance:** All captured content must pass brand validation before repurposing

**Top-Down Cascade (Whitepaper Strategy)**
- **Source Platforms:** YouTube, LinkedIn
- **Flow Direction:** Long-form → Short-form
- **Strategy:** Start with authoritative long-form content, cascade into bite-sized derivatives
- **Governance:** All cascaded content must maintain source attribution and brand compliance

---

## II. TRIBUTARY ARCHITECTURE (Bottom-Up)

### Platform Configuration: X (Twitter)

**Capture Mechanism:**
```python
# Algorithmic echolocation from X
capture_rules = {
    "platforms": ["twitter"],
    "trigger_metrics": {
        "min_engagement": 100,  # likes + retweets + replies
        "min_impressions": 1000,
        "velocity_threshold": "10_interactions_per_hour"
    },
    "content_types": ["original_tweets", "threads", "replies_with_context"],
    "brand_filters": ["EPOS", "Agent Zero", "PGP", "Exponere", "sovereignty", "local-first"]
}
```

**Repurposing Flow:**
1. **Capture:** High-performing tweets/threads enter `/content/lab/tributaries/x/captured/`
2. **Analysis:** Echolocation algorithm identifies:
   - Core insight/hook
   - Engagement patterns
   - Missing context that would benefit long-form
3. **Transformation:** Generate:
   - LinkedIn post (expanded context)
   - Blog post outline
   - YouTube script segment
   - Email newsletter section
4. **Validation:** Pass through `brand_compliance_validator.py`
5. **Promotion:** Move to `/content/lab/production/` if validated

### Platform Configuration: TikTok

**Capture Mechanism:**
```python
# Algorithmic echolocation from TikTok
capture_rules = {
    "platforms": ["tiktok"],
    "trigger_metrics": {
        "min_views": 5000,
        "min_engagement_rate": 0.05,  # 5%
        "watch_time_threshold": "75_percent_completion"
    },
    "content_types": ["videos", "captions", "top_comments"],
    "brand_filters": ["business automation", "AI tools", "property management", "sovereignty"]
}
```

**Repurposing Flow:**
1. **Capture:** High-performing TikToks → `/content/lab/tributaries/tiktok/captured/`
2. **Transcription:** Auto-generate transcript via Whisper
3. **Analysis:** Extract:
   - Visual storytelling patterns
   - Narrative hooks (first 3 seconds analysis)
   - Call-to-action performance
4. **Transformation:** Generate:
   - YouTube Shorts script
   - Instagram Reel adaptation
   - Twitter thread (story breakdown)
   - Blog post (expanded explanation)
5. **Validation:** Brand compliance + platform format check
6. **Promotion:** Validated content → production queue

---

## III. CASCADE ARCHITECTURE (Top-Down)

### Platform Configuration: YouTube

**Source Content Types:**
- Long-form explainers (10-30 min)
- Technical deep-dives
- Case study walkthroughs
- Interview/conversation format

**Cascade Flow:**
```python
cascade_rules = {
    "source": "youtube_long_form",
    "derivatives": {
        "youtube_shorts": {
            "count": 5,
            "duration": "30-60s",
            "focus": "single_insight_per_short",
            "format": "hook_explain_cta"
        },
        "linkedin_posts": {
            "count": 3,
            "length": "800-1200_chars",
            "focus": "professional_takeaway",
            "format": "story_lesson_application"
        },
        "twitter_threads": {
            "count": 2,
            "length": "5-8_tweets",
            "focus": "tactical_breakdown",
            "format": "numbered_list_with_examples"
        },
        "email_newsletter": {
            "count": 1,
            "length": "600_words",
            "focus": "comprehensive_summary",
            "format": "problem_solution_proof"
        }
    }
}
```

**Cascade Automation:**
1. **Source Analysis:**
   - Timestamp segmentation
   - Key insight extraction
   - Visual asset identification
   - Transcript generation
2. **Derivative Generation:**
   - Auto-generate 5 YouTube Shorts (different angles)
   - Auto-generate 3 LinkedIn posts (different audiences)
   - Auto-generate 2 Twitter threads (different depth)
   - Auto-generate 1 newsletter section
3. **Brand Validation:**
   - Voice consistency check
   - Claim verification
   - Attribution accuracy
4. **Scheduling:**
   - Platform-specific timing optimization
   - Content calendar integration
   - Cross-platform coordination

### Platform Configuration: LinkedIn

**Source Content Types:**
- Long-form articles (1500+ words)
- Multi-post series
- Case study narratives

**Cascade Flow:**
```python
cascade_rules = {
    "source": "linkedin_article",
    "derivatives": {
        "twitter_threads": {
            "count": 3,
            "strategy": "extract_tactical_insights"
        },
        "instagram_carousel": {
            "count": 2,
            "slides_per_carousel": 10,
            "strategy": "visual_breakdown"
        },
        "tiktok_script": {
            "count": 1,
            "duration": "60s",
            "strategy": "hook_from_article_opener"
        },
        "email_excerpt": {
            "count": 1,
            "length": "300_words",
            "strategy": "compelling_preview_with_link"
        }
    }
}
```

---

## IV. GOVERNANCE INTEGRATION

### Pre-Flight Validation

**Every Content Lab operation must:**
1. ✅ Pass `epos_doctor.py` environment check
2. ✅ Declare source platform and capture method
3. ✅ Include brand validation schema
4. ✅ Specify repurposing target platforms
5. ✅ Document expected engagement metrics

### Content Lab Gate Rules

**File Header Requirement:**
```python
# File: C:\Users\Jamie\workspace\epos_mcp\content\lab\[subsystem]\[filename].py
# Content Lab Component
# Source Platform: [X/TikTok/YouTube/LinkedIn]
# Flow Direction: [Tributary/Cascade]
# Brand Validation: Required
```

**Rejection Criteria:**
- ❌ Missing source attribution
- ❌ Brand voice inconsistency
- ❌ Engagement metrics below threshold
- ❌ Platform format violations
- ❌ Missing governance header

### Stasis Requirements

**Content Lab achieves stasis when:**
- All capture mechanisms are active and logging
- Brand validation passes 95%+ of content
- Repurposing workflows execute without manual intervention
- Cross-platform attribution is maintained
- Engagement metrics feed back into algorithm tuning

---

## V. ALGORITHMIC ECHOLOCATION LOGIC

### Core Algorithm

**Purpose:** Identify which micro-content deserves macro-expansion

**Inputs:**
- Platform engagement data (likes, shares, comments, views)
- Velocity metrics (engagement rate over time)
- Audience signals (who engaged, their follower count, their industry)
- Content signals (keywords, hooks, format, length)

**Processing:**
```python
def echolocation_score(content):
    """
    Calculates content amplification priority
    Higher score = Higher priority for long-form expansion
    """
    engagement_score = (
        content.likes * 1.0 +
        content.shares * 3.0 +  # Shares weighted higher
        content.comments * 2.0 +
        content.saves * 4.0  # Saves highest intent signal
    )
    
    velocity_score = engagement_score / content.hours_since_published
    
    audience_quality_score = sum([
        follower.authority_score for follower in content.engagers
    ]) / len(content.engagers)
    
    brand_alignment_score = count_brand_keywords(content.text) * 10
    
    total_score = (
        engagement_score * 0.3 +
        velocity_score * 0.4 +
        audience_quality_score * 0.2 +
        brand_alignment_score * 0.1
    )
    
    return total_score
```

**Outputs:**
- Priority queue for repurposing (highest score first)
- Recommended transformation (tweet → blog vs tweet → video)
- Engagement prediction for derivative content

### Feedback Loop

**Self-Improvement Mechanism:**
1. Track derivative content performance
2. Compare predicted vs actual engagement
3. Adjust algorithm weights based on accuracy
4. Log decisions to `/content/lab/intelligence/algorithm_tuning.jsonl`

---

## VI. DIRECTORY STRUCTURE

```
content/
├── lab/
│   ├── constitution.md  ← This file
│   ├── tributaries/
│   │   ├── x/
│   │   │   ├── captured/          # Raw high-performing tweets
│   │   │   ├── analyzed/          # Echolocation results
│   │   │   ├── transformed/       # Repurposed content
│   │   │   └── published/         # Deployed derivatives
│   │   └── tiktok/
│   │       ├── captured/          # Raw high-performing videos
│   │       ├── transcripts/       # Auto-generated text
│   │       ├── transformed/       # Repurposed content
│   │       └── published/         # Deployed derivatives
│   ├── cascades/
│   │   ├── youtube/
│   │   │   ├── source/            # Original long-form videos
│   │   │   ├── segments/          # Timestamped key moments
│   │   │   ├── derivatives/       # Generated shorts/posts
│   │   │   └── published/         # Deployed derivatives
│   │   └── linkedin/
│   │       ├── source/            # Original articles
│   │       ├── extracts/          # Key insights pulled
│   │       ├── derivatives/       # Generated threads/posts
│   │       └── published/         # Deployed derivatives
│   ├── production/
│   │   ├── ready/                 # Validated, awaiting schedule
│   │   ├── scheduled/             # Queued for specific publish times
│   │   └── published/             # Successfully deployed
│   ├── validation/
│   │   ├── brand_validator.py     # Voice/tone/claim checker
│   │   ├── format_validator.py    # Platform requirement checker
│   │   └── attribution_validator.py  # Source credit checker
│   ├── intelligence/
│   │   ├── echolocation_algorithm.py
│   │   ├── cascade_optimizer.py
│   │   ├── engagement_predictor.py
│   │   └── algorithm_tuning.jsonl  # Performance tracking
│   └── automation/
│       ├── capture_scheduler.py    # Platform monitoring
│       ├── repurpose_worker.py     # Content transformation
│       └── publish_orchestrator.py # Cross-platform deployment
```

---

## VII. INTEGRATION WITH EPOS CORE

### Component Registration

**Content Lab as EPOS Component (C10):**

```json
{
    "id": "C10_CONTENT_LAB",
    "name": "Content Lab - Algorithmic Echolocation & Cascading",
    "dependencies": [
        "C01_META_ORCHESTRATOR",
        "C05_GOVERNANCE_GATE",
        "C09_CONTEXT_VAULT"
    ],
    "inputs": [
        "Platform API data (X, TikTok, YouTube, LinkedIn)",
        "Brand knowledge from Context Vault",
        "Engagement metrics from analytics"
    ],
    "outputs": [
        "Repurposed content (validated)",
        "Publishing schedules",
        "Performance predictions"
    ],
    "failure_modes": [
        "FS-CL01: Platform API rate limit exceeded",
        "FS-CL02: Brand validation failure rate >5%",
        "FS-CL03: Derivative content underperforms source by >50%"
    ],
    "health_check": "/content/lab/health"
}
```

### Constitutional Requirements

**Content Lab must:**
1. Never publish content that fails brand validation
2. Always maintain source attribution
3. Log all algorithmic decisions for review
4. Respect platform API rate limits
5. Preserve brand voice consistency across all derivatives

**Content Lab must NOT:**
1. Repurpose content without engagement threshold validation
2. Publish derivatives before source content stabilizes (24hr minimum)
3. Override manual brand intervention
4. Mix tributary and cascade flows (keep separate)
5. Execute without governance gate approval

---

## VIII. DEPLOYMENT PHASES

### Phase 1: Infrastructure (Sprint 1)
- [ ] Create directory structure
- [ ] Deploy brand validators
- [ ] Integrate with governance gate
- [ ] Establish health checks

### Phase 2: Tributary (Sprint 2)
- [ ] Implement X capture mechanism
- [ ] Implement TikTok capture mechanism
- [ ] Deploy echolocation algorithm
- [ ] Test repurposing workflows

### Phase 3: Cascade (Sprint 3)
- [ ] Implement YouTube cascade
- [ ] Implement LinkedIn cascade
- [ ] Deploy derivative generators
- [ ] Test cross-platform coordination

### Phase 4: Automation (Sprint 4)
- [ ] Autonomous capture scheduling
- [ ] Self-optimizing algorithm tuning
- [ ] Predictive engagement modeling
- [ ] Full production deployment

---

## IX. SUCCESS METRICS

**Tributary Performance:**
- 80%+ of captured content generates ≥1 derivative
- Derivatives achieve ≥50% of source content engagement
- Brand validation pass rate ≥95%

**Cascade Performance:**
- 5+ derivatives per source content piece
- Aggregate derivative reach ≥2x source reach
- Cross-platform attribution maintained 100%

**System Performance:**
- Zero manual intervention required for 90%+ of content flow
- Algorithm prediction accuracy ≥70%
- End-to-end latency <24 hours (capture → publish)

---

**End of Constitution**

**Next Steps:** 
1. Promote this document to `/content/lab/` via governance gate
2. Create component interaction matrix entry for C10
3. Build tributary capture mechanisms for X and TikTok
4. Build cascade automation for YouTube and LinkedIn
