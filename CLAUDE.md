# CLAUDE.md — EPOS Build Protocol

## Git Discipline
NEVER run git add, git commit, or git push.
NEVER ask for commit approval during a session.
Make all file changes directly using write or edit tools.
When the full task is complete, output a summary of every file changed.
The human (Jamie) runs git manually after reviewing the summary.

## Session Protocol
1. Complete the full assigned task without interruption
2. Run validation when instructed
3. Surface a single clean summary at the end
4. Wait for approval before anything touches git

## Commit Message Format
SURGEON: [area healed] — [N] files | doctor: green | gate: [verdict]
