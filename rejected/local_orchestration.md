# Local Orchestration Playbook

**Purpose:** Govern how the Orchestrator model, FileSmith.Local, and specialists
coordinate local-machine workflows.

## Roles

- **Jamie / Stacey** – Vision + approval.
- **Orchestrator (Phi-4 / Jarvis)** – Planner and router.
- **FileSmith.Local** – Local coordinator and router.
- **Specialists** – Filesystem, CLI (Huntsman), GUI (ComputerUse).
- **Keepers** – Permission gatekeepers for bridges and portals.
- **Verifier.Local** – Auditor (stub, to be upgraded with MARL).

## I.I.D.E.A.T.E Loop (with Audit)

- **Immerse** – Load context, identity kernel, and specs.
- **Ideate** – Generate options, plans, and branches.
- **Design** – Choose structure (workflows, routes, configs).
- **Execute** – Use specialists, never bypassing safety policies.
- **Audit** – Verify outputs, update logs and session.
- **Tweak** – Adjust configs, workflows, and policies.
- **Evolve** – Feed data into MARL + future training.

## Ritual

1. Orchestrator forms a plan for the requested task.
2. VerifyKeeper decides if terminal / GUI access is allowed.
3. FileSmith routes to the correct specialist (filesystem, CLI, GUI).
4. Specialist performs the work and logs full traces.
5. Verifier (stub) records audit events.
6. Session state updates to reflect reality.
7. Lessons become new sprint recipes and templates.
