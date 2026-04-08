# EPOS CONSTITUTION v3.0
## Constitutional Amendment: Context Governance (C09)

**Effective**: 2026-01-21
**Rationale**: Integrate Recursive Language Model (RLM) context scaling to enable unlimited effective context without violating governance principles.

---

## ARTICLE VII: CONTEXT GOVERNANCE

### Section 1: Context Limits & Vault Requirements

**1.1 Token Inline Limit**
- No mission specification may inline more than **8,192 tokens** of data
- Data exceeding this limit MUST be stored in `/context_vault` directory
- Violations: `ERR-CONTEXT-001: Inline data exceeds token limit`

**1.2 Vault Directory Structure**
```
C:\Users\Jamie\workspace\epos_mcp\context_vault\
├── mission_data\
│   ├── mission_001.txt
│   └── mission_001.meta.json
├── bi_history\
│   └── decisions_2026.jsonl
└── registry.json
```

**1.3 Mandatory Vault Usage**
When data > 8,192 tokens, missions MUST:
1. Store data in `/context_vault/[category]/[name].txt`
2. Reference vault in mission spec via `context_vault_path` field
3. Use ContextVault symbolic search (not full load)

### Section 2: Component C09 - Context Orchestrator

**2.1 Purpose**
- Store ultra-long mission/BI/state data
- Expose symbolic search tools to Agent Zero and Execution Bridge
- Enable million+ token working context
- Prevent "context rot" in long-running analysis

**2.2 Constitutional Compliance**
- Uses `pathlib.Path` for all operations (Article II.3)
- Validates all paths are in `/context_vault/` directory
- Logs all search operations (Article II.4)
- Pre-imagined failure modes documented (Article IV)

**2.3 Search Methods** (RLM "Symbolic Queries")
- `regex_search()`: Pattern-based retrieval
- `window_search()`: Context window extraction
- `chunk_search()`: Chunked location-aware search
- `extract_json_objects()`: Structured data extraction

### Section 3: Agent Zero Integration

**3.1 Tool Exposure**
Agent Zero receives ContextVault as **tools**, not inline context:
```python
tools = {
    "search_context": vault.regex_search,
    "get_context_window": vault.window_search,
    "get_metadata": vault.get_metadata
}
```

**3.2 Execution Pattern**
1. Agent Zero receives mission with `context_vault_path`
2. Execution Bridge instantiates ContextVault
3. Agent Zero uses search tools to query vault
4. Agent Zero receives ONLY relevant snippets (not full file)
5. Agent Zero can recursively refine queries ("multi-hop")

**3.3 Prohibition**
- Agent Zero MUST NOT load full vault into prompt
- Execution Bridge MUST NOT inline vault content
- Mission specs MUST NOT contain > 8K tokens of data

### Section 4: Governance Gate Enforcement

**4.1 Pre-Flight Checks**
Governance Gate validates:
1. Files > 50KB do NOT inline data (use vault)
2. Missions referencing vaults include valid `context_vault_path`
3. Vault files exist and are in `/context_vault/` directory
4. Vault files do not exceed 100MB size limit

**4.2 Rejection Codes**
- `ERR-CONTEXT-001`: Inline long literal; must use ContextVault
- `ERR-CONTEXT-002`: Invalid vault path (not in context_vault/)
- `ERR-CONTEXT-003`: Vault file not found
- `ERR-CONTEXT-004`: Vault file exceeds size limit (100MB)

**4.3 Snapshot Detection**
`epos_snapshot.py` flags:
- Hard-coded strings > 2000 characters
- Ad-hoc file reads outside context_vault
- Mission specs > 8K tokens without vault reference

### Section 5: Business Intelligence Integration

**5.1 BI Logging**
BI engine tracks:
- Which vault files used in each mission
- Depth of recursive searches (RLM "trajectory length")
- Context query costs (proxy for token usage)
- Vault file sizes over time

**5.2 Optimization Triggers**
Missions that trigger deep recursive searches (>10 iterations) get flagged for optimization.

**5.3 Historical Analysis**
BI engine can query vault history without token limits:
```python
vault = ContextVault(Path("context_vault/bi_history/decisions_2026.jsonl"))
pivots = vault.extract_json_objects()  # No context window limit
```

---

## AMENDMENTS TO EXISTING ARTICLES

### Article II.7 (NEW): Configuration Explicitness Extended
- Environment variables MUST be loaded via `load_dotenv()`
- Context vaults MUST be registered in `context_vault/registry.json`
- Vault paths MUST use Windows-native format: `C:\Users\Jamie\workspace\epos_mcp\context_vault\...`

### Article IV (UPDATED): Pre-Imagined Failure Modes

Add to `FAILURE_SCENARIOS.md`:

**FS-CV01: Vault File Missing**
- Symptom: `FileNotFoundError` on vault initialization
- Cause: Mission references non-existent vault file
- Detection: Pre-flight validation in Execution Bridge
- Recovery: Reject mission with ERR-CONTEXT-003

**FS-CV02: Vault Path Outside Directory**
- Symptom: `ContextVaultError: Vault files must be in context_vault/`
- Cause: Attempt to access file outside governed directory
- Detection: Path validation in `ContextVault.__init__()`
- Recovery: Reject with ERR-CONTEXT-002

**FS-CV03: Vault Size Exceeded**
- Symptom: `ContextVaultError: Vault file too large`
- Cause: Vault file > 100MB
- Detection: Size validation in `_validate_size()`
- Recovery: Reject with ERR-CONTEXT-004

**FS-CV04: Invalid Regex Pattern**
- Symptom: `ContextVaultError: Invalid regex pattern`
- Cause: Malformed regex in search query
- Detection: `re.error` exception in `regex_search()`
- Recovery: Log error, return empty results

---

## COMPONENT INTERACTION MATRIX UPDATES

Add C09 row:

| ID | Component | Inputs | Outputs | Dependencies | Failure Modes |
|----|-----------|--------|---------|--------------|---------------|
| C09 | Context Orchestrator | Vault files (txt/json), search patterns | Search results, metadata | pathlib, re, json | FS-CV01, FS-CV02, FS-CV03, FS-CV04 |

C09 integrates with:
- **C03 (Execution Bridge)**: Provides vault instance to Agent Zero
- **C02 (Agent Zero Bridge)**: Receives search tools
- **C07 (BI Engine)**: Stores decision history in vaults

---

## RATIFICATION

**Amendment Status**: ✅ RATIFIED
**Version**: 3.0
**Supersedes**: Constitution v2.0
**Next Review**: After Sprint 2 completion

**Key Benefit**: EPOS can now scale to million+ token contexts without changing models or breaking governance rules.

**Compliance Mandate**: All future missions involving large data MUST use Context Vault. Inline data > 8K tokens is a constitutional violation.
