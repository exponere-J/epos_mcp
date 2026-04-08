from router.decision_router import DecisionRouter

if __name__ == "__main__":
    dr = DecisionRouter()
    tests = [
        (["intent:code"], "product.development"),
        (["intent:marketing"], "content.research_and_creation"),
        (["intent:airtable"], "automation.workflow_design"),
        (["intent:family"], "personal.identity_routine"),
        (["intent:unknown"], "fallback.llm_classify"),
    ]
    for tags, expected in tests:
        pipeline, route = dr.route(tags)
        print(tags, "=>", pipeline, "|", "OK" if pipeline == expected else "FAIL")
