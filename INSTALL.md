# Installation

Wires this skill pack into Hermes Agent via its `external_dirs` mechanism. No fork, no patching — the skills are loaded alongside Hermes' bundled ones.

## Prerequisites

1. **Hermes Agent installed** — follow the official install guide at <https://hermes-agent.nousresearch.com/docs/getting-started/installation>. Hermes runs on Linux, macOS, or WSL2 (Windows native is not supported).
2. **An LLM provider configured** — Nous Portal, OpenRouter, Anthropic, OpenAI, or a local model via Ollama / LM Studio. Any works. Pick whatever you already have keys for.
3. **Python 3.10+** — the `mdm-dq-audit` skill ships a helper script that runs in Hermes' sandboxed execution environment.
4. **Git** — to clone this repo.

## Step 1 — Clone the skill pack

Clone anywhere outside `~/.hermes/`. A common convention:

```bash
mkdir -p ~/.agents
cd ~/.agents
git clone https://github.com/<your-username>/hermes-mdm-steward-skills.git
```

You now have the skill pack at `~/.agents/hermes-mdm-steward-skills/`.

## Step 2 — Point Hermes at the skill directory

Open (or create) `~/.hermes/config.yaml` and add the `external_dirs` entry under the `skills` section:

```yaml
skills:
  external_dirs:
    - ~/.agents/hermes-mdm-steward-skills/skills
```

Paths support `~` expansion and `${VAR}` substitution. If the section already exists, just append the path.

## Step 3 — Verify Hermes sees the skills

Start a Hermes session:

```bash
hermes chat
```

Then ask it to list available skills:

```
What skills do you have that start with "mdm-"?
```

You should see all six: `mdm-duplicate-resolver`, `mdm-supplier-standardizer`, `mdm-location-validator`, `mdm-golden-record-composer`, `mdm-dq-audit`, `mdm-steward-briefing`.

Alternatively, every skill is exposed as a slash command. In the CLI, type `/` and you should see them in the autocomplete.

## Step 4 — Run the first scenario

```
/mdm-duplicate-resolver Here are two supplier records from our synthetic 
dataset. Are they the same entity? Explain your reasoning step by step.

Record A:
  supplier_id: NX-SUP-00142
  name: Dubai Trading LLC
  address: PO Box 12345, Dubai, UAE
  trn: 100123456700003

Record B:
  supplier_id: NX-SUP-00189
  name: DUBAI TRADING L.L.C.
  address: P.O. Box 12345, Dubai, United Arab Emirates
  trn: 100123456700003
```

The agent should load the `mdm-duplicate-resolver` skill and walk through the decision using its procedure.

## Step 5 — Set up the email gateway (optional)

For scheduled briefings and audit summaries delivered to your inbox, configure Hermes' email gateway. Follow the official docs at <https://hermes-agent.nousresearch.com/docs/user-guide/messaging/> — the email setup differs by provider (Gmail app passwords, IMAP/SMTP credentials) and is outside the scope of this skill pack.

Once the gateway is running, you can ask Hermes to:

```
/mdm-steward-briefing generate tomorrow's briefing and email it to me 
at 08:00 every weekday
```

Hermes' built-in cron handles the scheduling; the gateway handles the delivery.

## Troubleshooting

### Skills not appearing

- Confirm the path in `config.yaml` points to the `skills/` subdirectory, not the repo root.
- Confirm the path exists — non-existent paths are silently skipped by Hermes.
- Restart `hermes chat` after editing the config.

### Slash commands collide

If a Hermes bundled skill uses a similar name, the local skill in `~/.hermes/skills/` wins over the external one. Rename the local copy or remove it.

### Python script fails in DQ audit

The `mdm-dq-audit` skill's helper script uses `pandas` and standard library only. If Hermes' sandbox doesn't have `pandas`, the skill will prompt the agent to install it via the sandbox's package manager.

## Updating

Skills are read-only to Hermes when loaded from `external_dirs`. To update:

```bash
cd ~/.agents/hermes-mdm-steward-skills
git pull
```

No Hermes restart required — the agent re-scans skills on each session start.

## Uninstall

Remove the path from `~/.hermes/config.yaml` and delete the cloned directory. Hermes' own bundled skills are untouched.
