---
name: mdm-steward-briefing
description: Produces a concise morning briefing for a data steward — what needs attention today, what's breached SLA, what trends matter. Designed for delivery via messaging gateway (email, Telegram, Slack) on a cron schedule. Consumes the output of the mdm-dq-audit skill and the current exception queue state.
version: 1.0.0
metadata:
  hermes:
    tags: [mdm, data-quality, briefing, steward, scheduled]
    category: mdm
---

# MDM Steward Briefing

## When to Use

Activate this skill when:

- A scheduled cron triggers a morning briefing (typically 07:30–08:30 local time on weekdays).
- The user asks for "today's briefing", "morning update", "what needs my attention", or "steward briefing".
- A new steward is onboarding and needs a daily-rhythm template to work from.

Do **not** use this skill for:

- Running the underlying audit (use `/mdm-dq-audit` first).
- Deep-dive investigations (the briefing is a glance, not a report — for detail, direct the steward to the audit output file).
- Sending ad-hoc alerts mid-day (those should be exception notifications, not briefings).

## Core principle

A briefing is **what must be decided today**. It is not a status report. If a steward finishes the briefing without knowing what their first three actions are, the briefing failed.

## Procedure

### Step 1 — Gather inputs

Before composing the briefing, assemble:

1. **Yesterday's DQ audit output** — from `/mdm-dq-audit`, typically at `/tmp/dq_audit_summary.md`.
2. **Exception queue state** — count of items awaiting steward action, grouped by severity.
3. **SLA state** — any exception breaching its resolution SLA.
4. **Trending issues** — any issue type that has grown materially in the last 7 days.
5. **Upcoming brand cutovers** — any brand scheduled for migration or onboarding in the next 14 days.

If any input is unavailable, state it explicitly in the briefing rather than omit the section. A missing input is itself a signal.

### Step 2 — Compose the briefing

Target length: 150–250 words. A steward should read it in under 90 seconds.

Structure:

```
Good morning.

## Attention today

[1–3 bullets. Each bullet is a decision or action, not a status.]

## SLA watch

[Any item breaching or nearing SLA, with time remaining.]

## Trending

[1 bullet if a trend has emerged. Omit the section if nothing meaningful.]

## Upcoming

[Brand cutovers or programme milestones in the next 14 days.]

## Numbers at a glance

[3–5 numeric lines: open exceptions, duplicates pending review, format violations, completeness on the most watched field.]
```

### Step 3 — Prioritization rules

- **CRITICAL issues first**, always. Deterministic duplicates, compliance flags, blocked-status merges.
- **SLA breaches next**, in ascending time-remaining order.
- **Trending third**, only if material (≥20% week-on-week change or absolute threshold).
- **Cutovers last**, as context. They are rarely "today's" action.

### Step 4 — Tone

- Direct. No filler. No "I hope you have a great day".
- Use steward's first name if known.
- Prefer numbers over adjectives: "5 duplicates pending" not "several duplicates pending".
- Close with a single clear next action, not a menu of options.

### Step 5 — Deliver

Send via the configured gateway. If delivering via email:

- Subject: `MDM Steward Briefing — <YYYY-MM-DD>`
- Plain text or simple Markdown. Avoid HTML; steward clients vary.

If delivering via Telegram or Slack:

- Use Markdown for structure.
- Keep under the platform's preview threshold (Telegram: ~1024 chars for full preview; Slack: ~3000 chars for unscrolled display).

### Example briefing

```
Good morning, Priya.

## Attention today
- 5 supplier duplicates confirmed via shared TRN — 2 cross-brand
  (Verdant + Luxora). Merge clusters ready for your approval in the
  exception queue.
- NX-SUP-00826 is Inactive but shares TRN with NX-SUP-00825 (Active).
  Do not auto-merge. Decide retention route before end of day.

## SLA watch
- NX-SUP-00903 (Arabian Logistics) — Pending Review for 48h, SLA
  breach in 6h.

## Trending
- Emirate-field "DXB" variant usage up from 2 to 4 records this week.
  Worth a quick note to the Abu Dhabi brand onboarding lead.

## Upcoming
- Petalia Fashion cutover to Core MDM: 5 working days away.

## Numbers at a glance
- Open exceptions: 9 (was 12 yesterday)
- TRN completeness: 77.8% (target: 95%)
- Cross-brand supplier overlaps: 3

First action: approve or reject NX-SUP-00142 / NX-SUP-00189 merge.
```

## Pitfalls

- **Never send an empty briefing.** If there is genuinely nothing to act on, state that explicitly: "No attention items today — queue is clean. Completeness on TRN is 95.2%." A missing briefing is indistinguishable from a failed cron.
- **Never lead with "yesterday's audit detected…".** Lead with what needs to happen today. Audit detail is reference material, not the headline.
- **Do not mix brands' detail into a single steward's briefing** unless the steward covers multiple brands. Personalize per recipient.
- **Never promise automatic action in the briefing.** A briefing informs; the steward decides. Phrases like "I will merge these" are out of scope.
- **Do not let the "Numbers at a glance" section grow.** If it exceeds 5 lines, the briefing has become a dashboard. Dashboards belong in a web UI, not an inbox.

## Verification

- Can the steward name their first action within 15 seconds of reading the briefing?
- Are all items in "Attention today" decisions, not statuses?
- Is the SLA section populated only with actual breaches or near-breaches, not all open items?
- Is the briefing under 250 words?

If any answer is "no", shorten and sharpen before sending.
