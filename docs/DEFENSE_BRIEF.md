# Defense Brief — MDM Steward Agent

Cumulative talking points for defending the technical choices in this project. When someone asks "why did you choose X over Y?", the answer lives here.

---

## Why Hermes Agent over another framework?

**The question behind the question:** there are several agent frameworks available — LangGraph, AutoGen, OpenAI's Assistants API, Anthropic Claude Code, a dozen open-source alternatives. Why this one?

**The answer.** Hermes has three properties that map directly to the MDM steward problem. First, a skill-creation loop that captures successful resolutions as reusable playbooks — exactly the pattern of steward work. Second, a persistent memory layer that lets the agent build a running model of each brand's data quirks across sessions. Third, a messaging gateway that meets stewards on the channels they already use — email, Telegram, Slack — rather than asking them to log into yet another portal.

Other frameworks solve parts of this. None solves all three as a coherent offering. Picking the framework that is purpose-built for long-running persistent workloads was the right match for a workload that is fundamentally long-running and persistent.

**Alternative considered and rejected:** LangGraph with a custom memory layer. Technically feasible but adds substantial engineering burden — memory persistence, session management, skill retrieval, and gateway integration would all need to be built. Hermes ships them.

## Why a skill pack and not a fork?

**The answer.** Hermes is at v0.8 and evolving. A fork creates a merge-conflict maintenance burden every time the upstream framework changes. The `external_dirs` extension point is documented as a first-class mechanism — skills loaded this way are read-only from Hermes' perspective, so upstream upgrades cannot overwrite them.

The skill pack survives framework churn. A fork does not.

**Alternative considered and rejected:** forking and maintaining a Hermes branch. Viable for a team with dedicated maintenance capacity. Not viable for a portfolio project maintained in evenings and weekends.

## Why the agentskills.io standard rather than Hermes-native extensions?

**The answer.** The value of the playbooks is independent of the framework executing them. The agentskills.io specification is an open standard, compatible across multiple agents. If the framework landscape shifts in 12 months — either because Hermes changes direction or because a better framework emerges — the skills port with minimal rewrite.

Hermes-specific metadata (tags, category) is namespaced under `metadata.hermes.*` in the YAML frontmatter, so non-Hermes agents can safely ignore it.

**Trade-off acknowledged.** Some Hermes-specific features (e.g., fallback_for_toolsets for conditional skill activation) are not used, because they do not exist in the open standard. This is a deliberate trade of convenience for portability.

## Why Python over JavaScript for the DQ audit script?

**The answer.** The audit produces structured output — completeness percentages, duplicate candidates, format violations. Pandas handles this idiomatically with a fraction of the code that equivalent JavaScript libraries (Danfo, dataframe-js) require. Pandas is also already available in the Hermes sandbox by default, so there is no install overhead for users.

**Alternative considered and rejected:** Node.js with a CSV library. Viable. Rejected because the data science ecosystem in Python is broader — if the audit later grows to include clustering-based near-duplicate detection or fuzzy matching, those libraries exist in Python and would require rebuilding in JavaScript.

## Why bundle a synthetic dataset?

**The answer.** Two reasons, one legal and one practical.

Legally, using real brand names in a public repository raises IP and confidentiality questions that are simply not worth it. The author maintains a strict boundary — fictitious brand names in all public outputs. That boundary is non-negotiable for career reasons.

Practically, bundling synthetic data means the skill pack works out of the box with zero external dependencies. A user can clone the repo and run the audit in under five minutes. No MDM platform credentials, no database setup, no dataset licensing. This is essential for the project's purpose: **demonstration**.

**Alternative considered and rejected:** pointing to public datasets like Open Corporates or UN Global Compact. Both carry licensing constraints that complicate redistribution, and neither has the Gulf-region characteristics that make the location-validator skill interesting.

## Why six skills and not more?

**The answer.** Six is a coherent catalog that demonstrates the skill-pack pattern is structured and reusable without becoming maintenance debt. The skills chosen cover the four core steward activities (detect duplicates, clean records, compose golden records, run audits) plus two delivery skills (scheduled audit, morning briefing) that turn the pack into an always-on service rather than a reference library.

Adding more skills without clear marginal value is feature creep. The v0.1 release is deliberately lean.

**Alternative considered and rejected:** a single omnibus "MDM steward" skill. This would violate the progressive-disclosure principle — skills are meant to be loaded only when their specific context applies. A monolith would be loaded on every steward interaction, wasting tokens and diluting focus.

## Why local-only when Hermes supports VPS, Modal, Daytona?

**The answer.** Local-only keeps the scope of the initial release tight. The interesting engineering problem was encoding MDM resolution patterns as skills — not figuring out the right hosting tier. Local deployment means anyone with Hermes installed can run the pack immediately, with no cloud accounts, no budget, no operational overhead.

Moving to a VPS is a documented roadmap item. When the project is ready to demonstrate 24/7 always-on behaviour (which requires a host that is on 24/7), the VPS move is a change of host configuration, not a change of architecture.

**Alternative considered and rejected:** starting on Modal (serverless, pay-per-use, $0 when idle). Tempting, but introduces a cloud account dependency that new users have to set up before they can try the pack. Local-first is lower friction for the primary audience — fellow practitioners who want to see the pattern working.

## Why is the email gateway setup outside the repo?

**The answer.** Hermes' gateway setup varies by email provider (Gmail app passwords, corporate SMTP, IMAP credentials) and is documented at length in the Hermes docs. Reproducing that documentation in this repo would be duplication that risks going stale as Hermes evolves. Referring to the upstream docs means users always get the current procedure.

**Trade-off acknowledged.** This means the "runs locally with email delivery" story requires two setups — the skill pack (which this repo fully documents) and the Hermes gateway (which requires following the upstream docs). A single-click setup would be friendlier but is not achievable while Hermes' own configuration patterns continue to evolve.

## Why is there no connection to a real MDM platform?

**The answer.** Connecting to a specific Core MDM platform (Informatica IDMC, Microsoft MDS, Profisee, Reltio) requires credentials, VPN configuration, and platform-specific API glue that cannot be generically packaged. The right integration for each deployment is tenant-specific.

The pack is designed so that integration is straightforward — the DQ audit script accepts arbitrary CSV paths, so pointing it at a nightly export from any MDM platform is a matter of changing a single argument. But packaging any particular integration into the v0.1 release would bake in a dependency that locks users into one vendor.

**Alternative considered and rejected:** shipping a reference integration with a specific platform. Would demonstrate the end-to-end flow for users of that platform. Excludes everyone else. The neutral CSV interface serves all platforms at the cost of some demo polish.

## Why is this MIT licensed?

**The answer.** MIT is the default permissive licence for experimental, portfolio, and demonstration projects. It lets anyone fork, adapt, and build on the work without obligation. The author's value is not in the code — it is in the practice of building. Open licensing lowers friction for others to pick this up and extend it.

**Alternative considered and rejected:** AGPL or a more restrictive licence. Would discourage enterprise adoption (enterprise legal teams avoid AGPL reflexively). For a pack that is meant to demonstrate a pattern, restriction defeats the purpose.

## If challenged: "this is just a prompt wrapper"

**The answer.** The pack is structured procedural knowledge that an agent applies consistently across sessions. That is what separates a skill from a prompt — a skill is reused with deterministic structure; a prompt is authored once per session. The difference matters when the same resolution pattern needs to be applied the same way by ten different stewards on ten different shifts.

That said — the pack's value is not in code complexity. It is in **captured expertise**. The author has spent twenty years building this kind of knowledge. The engineering is lightweight because the engineering was never the hard part. The hard part was knowing which gates to check, in which order, for each master data entity type in each region — and writing it down so anyone can use it.

The framework makes that knowledge executable. The knowledge itself was the expensive part.

---

*When adding a new major technical decision, append the rationale here with alternatives considered and the trigger that would cause a reversal.*
