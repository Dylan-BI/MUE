# MUE ChatGPT Desktop Environment

This folder contains repo-local setup/action scripts for using MUE from Codex in the ChatGPT desktop app.

Suggested local environment setup script:

```powershell
powershell -ExecutionPolicy Bypass -File .codex/scripts/setup.ps1
```

Suggested actions:

```powershell
powershell -ExecutionPolicy Bypass -File .codex/scripts/build-dashboard.ps1
powershell -ExecutionPolicy Bypass -File .codex/scripts/serve-review-dashboard.ps1
powershell -ExecutionPolicy Bypass -File .codex/scripts/watch-dashboard.ps1
```

If the desktop app generates a local-environment config file, keep it inside this `.codex` folder at the project root so it can be shared with the repo.
