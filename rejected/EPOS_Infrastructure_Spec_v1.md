# EPOS Infrastructure Spec v1

This document defines the modular, extensible infrastructure for the EPOS MCP workspace.

- Kernel: global config, environment, global rules
- Agents: registry + role specs
- MCP Servers: tool layer for filesystem, Airtable, Google Drive, web, logging
- Content: templates, strategies, service packages
- Blueprints: reusable blueprints for content, sites, agents
- Sites: concrete implementations (e.g., PGP marketing site + funnels)
- Workflows: orchestrator + shared workflow components
- Ops: logging, monitoring, diagnostics
