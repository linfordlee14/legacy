"""The curated MASTER_CONTEXT claim dataset (MVP-013; TASK-111).

Transcribed by hand from knowledge/MASTER_CONTEXT.md (consolidated
2 July 2026) so every claim boundary is a reviewed decision, per the
"scripted with a review pass" default recorded in IMPLEMENTATION_TASKS.

Transcription rules:
- Tiers map exactly: verified (from a checkmark marker), self_reported
  (yellow marker), flagged (red marker). Nothing is upgraded, ever.
- Mixed markers take the WEAKER tier; tier_rationale preserves the
  document's original marking.
- The section 9 "gap" rows (no Medium/Hashnode/Facebook/Instagram or
  interview footprint found) are section 12 research tasks, not
  biographical claims, and are deliberately not imported, keeping the
  flagged set at exactly the six section 12 verification items.
- Sources: every claim links to the MASTER_CONTEXT document source with
  support_type mentions; verified claims additionally link to their
  platform source stub with support_type supports. Platform URLs are
  null until TASK-001 attaches them from Research/15 Sources.md, which
  keeps those sources visible in the verification queue (DATABASE_SCHEMA
  section 4.4 unarchived-URL rule).
"""

from typing import Any

# Source stubs. Keyed for reference from claims; find-or-create by title.
SOURCES: dict[str, dict[str, str | None]] = {
    "master_context": {
        "source_type": "document",
        "title": "MASTER_CONTEXT.md (consolidated 2 July 2026)",
        "publisher": None,
        "url": None,
        "reliability_note": "First-party consolidated research record; canonical context.",
    },
    "github": {
        "source_type": "url",
        "title": "GitHub profile linfordlee14",
        "publisher": "GitHub",
        "url": None,
        "reliability_note": "URL pending attachment from Research/15 Sources.md (TASK-001).",
    },
    "hackathon_platform": {
        "source_type": "url",
        "title": "Hackathon platform profile hacker1401",
        "publisher": "Hackathon platform",
        "url": None,
        "reliability_note": "URL pending attachment from Research/15 Sources.md (TASK-001).",
    },
    "devto": {
        "source_type": "url",
        "title": "DEV.to author page",
        "publisher": "DEV.to",
        "url": None,
        "reliability_note": "URL pending attachment from Research/15 Sources.md (TASK-001).",
    },
    "gdg_cape_town": {
        "source_type": "url",
        "title": "GDG Cape Town event pages",
        "publisher": "GDG Cape Town",
        "url": None,
        "reliability_note": "URL pending attachment from Research/15 Sources.md (TASK-001).",
    },
}

# Subject entities. The owner Person row (DATABASE_SCHEMA 4.3: the owner is
# a Person kept in sync with MASTER_CONTEXT through Claims only) and the
# section 6 projects. Project status is entity metadata, not a claim:
# verified-footprint projects are marked shipped, described-only projects
# concept, with section 12 item 5 (live repos versus concept stage) noted.
OWNER_PERSON = {
    "full_name": "Linford Musiyambodza",
    "relationship_to_owner": "self",
    "aliases": ["Linford Lee", "LinfordLee14", "linfordlee14", "hacker1401"],
}

PROJECTS: dict[str, dict[str, str]] = {
    "wildguard-ai": {"name": "WildGuard AI", "status": "shipped"},
    "cyberbuddy": {"name": "CyberBuddy", "status": "shipped"},
    "necronet": {"name": "NecroNet", "status": "shipped"},
    "phishguard": {"name": "PhishGuard", "status": "shipped"},
    "rhinoshield": {"name": "RhinoShield", "status": "shipped"},
    "rhinoguardians": {"name": "RhinoGuardians", "status": "concept"},
    "spazalink": {"name": "SpazaLink", "status": "concept"},
    "safewatch-sa": {"name": "SafeWatch SA", "status": "concept"},
    "guardian-sa": {"name": "Guardian-SA", "status": "concept"},
    "linfy-academy": {"name": "Linfy Academy", "status": "concept"},
    "rentguard-ct": {"name": "RentGuard CT", "status": "concept"},
    "hermes-ecosystem": {"name": "Hermes agent ecosystem", "status": "concept"},
}

PROJECT_STATUS_NOTE = (
    "Status pending MASTER_CONTEXT section 12 item 5 (live repos versus concept stage)."
)

# Claims. subject is ("owner", None) or ("project", slug). sources lists the
# SOURCES keys linked with support_type supports (the master_context mentions
# link is added to every claim automatically).
Claim = dict[str, Any]
CLAIMS: list[Claim] = [
    # --- Section 1: identity -------------------------------------------------
    {"subject": ("owner", None), "predicate": "has_full_name", "tier": "verified",
     "section": "1", "sources": [],
     "statement": "Full name is Linford Musiyambodza."},
    {"subject": ("owner", None), "predicate": "has_origin", "tier": "self_reported",
     "section": "1", "sources": [],
     "statement": "Linford states he is a first-generation Zimbabwean and a first-time Zimbabwean passport applicant."},
    {"subject": ("owner", None), "predicate": "based_in", "tier": "verified",
     "section": "1", "sources": [],
     "statement": "Based in Strand, Cape Town, South Africa."},
    {"subject": ("owner", None), "predicate": "has_public_tagline", "tier": "verified",
     "section": "1", "sources": [],
     "statement": "Public tagline: 'Building in public. Building for Africa.'"},
    {"subject": ("owner", None), "predicate": "uses_faith_signature", "tier": "verified",
     "section": "1", "sources": [],
     "statement": "Closes posts and messages with 'El Roi' (Hebrew: 'the God who sees')."},
    {"subject": ("owner", None), "predicate": "has_public_persona", "tier": "verified",
     "section": "1", "sources": [],
     "statement": "Primary public persona: faith-driven African software builder and AI engineer."},
    {"subject": ("owner", None), "predicate": "uses_github_handle", "tier": "verified",
     "section": "1", "sources": ["github"],
     "statement": "GitHub handle linfordlee14 is his primary code presence."},
    {"subject": ("owner", None), "predicate": "uses_hackathon_handle", "tier": "verified",
     "section": "1", "sources": ["hackathon_platform"],
     "statement": "Hackathon platform handle hacker1401 is his corroborated competition handle."},
    {"subject": ("owner", None), "predicate": "uses_alias", "tier": "self_reported",
     "section": "1", "sources": [],
     "statement": "The alias 'Linford Lee' / LinfordLee14 appears tied to the same person; treated as consistent-with, not independently proven.",
     "rationale": "Document marks the alias mapping as requiring a definitive cross-link (section 12 item 6)."},
    # --- Section 2: values and philosophy ------------------------------------
    {"subject": ("owner", None), "predicate": "holds_value", "tier": "verified",
     "section": "2", "sources": [],
     "statement": "Faith-led mission: personal and professional identity are intertwined; work is framed as mission-led service, signed 'El Roi'."},
    {"subject": ("owner", None), "predicate": "holds_value", "tier": "verified",
     "section": "2", "sources": [],
     "statement": "Builds for Africa, in public: prioritizes practical, deployable tools for African communities across conservation, township economies, safety, and youth."},
    {"subject": ("owner", None), "predicate": "holds_value", "tier": "verified",
     "section": "2", "sources": [],
     "statement": "Practical impact over theory: ships working prototypes and enters them into hackathons and showcases rather than keeping work private."},
    {"subject": ("owner", None), "predicate": "holds_value", "tier": "verified",
     "section": "2", "sources": ["gdg_cape_town"],
     "statement": "Community-embedded: active contributor in the developer community (GDG Cape Town) with mentorship and skills-sharing framing.",
     "rationale": "Document marks specific leadership titles separately (section 4)."},
    {"subject": ("owner", None), "predicate": "practices_methodology", "tier": "self_reported",
     "section": "2", "sources": [],
     "statement": "Linford reports practicing Specification-Driven Development as a discipline, starting builds with mission.md, roadmap.md, and techstack.md."},
    {"subject": ("owner", None), "predicate": "has_brand_style", "tier": "self_reported",
     "section": "2", "sources": [],
     "statement": "Self-reported brand identifiers: Unicode bold serif headers on LinkedIn, horizontal dividers, faith-driven closing lines, no em dashes in written content, social artifacts as copyable HTML, direct and warm builder-narrative tone."},
    # --- Section 3: mission ---------------------------------------------------
    {"subject": ("owner", None), "predicate": "has_mission", "tier": "verified",
     "section": "3", "sources": [],
     "statement": "Mission: to build practical, AI-powered software that serves African communities, protecting wildlife, digitizing the informal economy, improving community safety, and empowering township youth, as an act of faith-driven service.",
     "rationale": "Verified as a pattern from tagline and portfolio; the exact wording is an editorial synthesis, not a verbatim quote (section 3)."},
    # --- Section 4: companies and roles ---------------------------------------
    {"subject": ("owner", None), "predicate": "founder_and_ceo_of", "tier": "verified",
     "section": "4", "sources": [],
     "statement": "Founder and CEO of Linfy Tech Solutions (Strand, Cape Town), his core company with verified brand presence."},
    {"subject": ("owner", None), "predicate": "cto_of", "tier": "verified",
     "section": "4", "sources": [],
     "statement": "CTO of NeuroGrowth Labs."},
    {"subject": ("owner", None), "predicate": "holds_role", "tier": "flagged",
     "section": "4", "sources": [],
     "statement": "Assistant Cluster Leader, Tech and Digital Skills at IUS Africa.",
     "rationale": "Not independently verified in the research pass; confirm with an official IUS Africa listing (section 12 item 2)."},
    {"subject": ("owner", None), "predicate": "ambassador_of", "tier": "self_reported",
     "section": "4", "sources": [],
     "statement": "Pie and AI Ambassador for DeepLearning.AI; consistent with the ambassador program, official listing pending (section 12 item 3)."},
    {"subject": ("owner", None), "predicate": "ambassador_of", "tier": "self_reported",
     "section": "4", "sources": [],
     "statement": "Ambassador for Thinking About Thinking."},
    {"subject": ("owner", None), "predicate": "member_of", "tier": "verified",
     "section": "4", "sources": ["gdg_cape_town"],
     "statement": "Community member of GDG Cape Town with verified participation."},
    # --- Section 5: technical expertise ---------------------------------------
    {"subject": ("owner", None), "predicate": "demonstrates_skill", "tier": "verified",
     "section": "5", "sources": ["github"],
     "statement": "Languages: Python, TypeScript, JavaScript, and Kotlin (Android), evidenced via GitHub and project stacks."},
    {"subject": ("owner", None), "predicate": "demonstrates_skill", "tier": "verified",
     "section": "5", "sources": [],
     "statement": "Web and app frameworks: React and Next.js."},
    {"subject": ("owner", None), "predicate": "claims_skill", "tier": "self_reported",
     "section": "5", "sources": [],
     "statement": "Android stack detail: Jetpack Compose (Material3), Clean Architecture with MVVM, Room, Hilt.",
     "rationale": "Document marks the CyberBuddy stack as self-described but consistent (mixed marker taken at the weaker tier)."},
    {"subject": ("owner", None), "predicate": "demonstrates_skill", "tier": "verified",
     "section": "5", "sources": [],
     "statement": "Backend: FastAPI."},
    {"subject": ("owner", None), "predicate": "demonstrates_skill", "tier": "verified",
     "section": "5", "sources": [],
     "statement": "AI/ML: computer vision (YOLOv5 for anti-poaching) and LLM application development, evidenced by computer vision projects."},
    {"subject": ("owner", None), "predicate": "claims_skill", "tier": "self_reported",
     "section": "5", "sources": [],
     "statement": "Agentic AI and multi-agent systems (A2A protocol) and RAG internals.",
     "rationale": "Document marks agent ecosystem internals at the weaker tier."},
    {"subject": ("owner", None), "predicate": "uses_platforms", "tier": "self_reported",
     "section": "5", "sources": [],
     "statement": "AI platforms and APIs: Anthropic Claude API, Google Gemini API, Groq API."},
    {"subject": ("owner", None), "predicate": "uses_infrastructure", "tier": "self_reported",
     "section": "5", "sources": [],
     "statement": "Data and infrastructure: Supabase (including pgvector), Room, and MCP integrations (Supabase MCP, Tavily MCP)."},
    {"subject": ("owner", None), "predicate": "demonstrates_skill", "tier": "verified",
     "section": "5", "sources": [],
     "statement": "Cybersecurity: applied security tooling evidenced by shipped security projects (PhishGuard, CyberBuddy, Guardian-SA)."},
    {"subject": ("owner", None), "predicate": "claims_skill", "tier": "self_reported",
     "section": "5", "sources": [],
     "statement": "Depth of cybersecurity expertise beyond the shipped projects.",
     "rationale": "Document marks depth at the weaker tier while the shipped projects are verified."},
    {"subject": ("owner", None), "predicate": "claims_domain_breadth", "tier": "self_reported",
     "section": "5", "sources": [],
     "statement": "Self-reported skill breadth: programming, cybersecurity, data analytics, AI/ML, cloud, networking, DevOps, databases, UI/UX, leadership, public speaking, teaching and mentorship, business and entrepreneurship."},
    # --- Section 6: projects ---------------------------------------------------
    {"subject": ("project", "wildguard-ai"), "predicate": "is_described_as", "tier": "verified",
     "section": "6", "sources": ["github"],
     "statement": "WildGuard AI is a multi-agent wildlife conservation system with a verified public footprint."},
    {"subject": ("project", "cyberbuddy"), "predicate": "is_described_as", "tier": "verified",
     "section": "6", "sources": [],
     "statement": "CyberBuddy is a gamified Android cybersecurity coaching app (Kotlin, Jetpack Compose, Clean Architecture with MVVM, Room, Hilt, Gemini)."},
    {"subject": ("project", "cyberbuddy"), "predicate": "presented_at", "tier": "verified",
     "section": "6", "sources": ["gdg_cape_town"],
     "statement": "CyberBuddy was presented at GDG Cape Town Pet Projects: The 2026 Edition on 30 June 2026."},
    {"subject": ("project", "necronet"), "predicate": "is_described_as", "tier": "verified",
     "section": "6", "sources": ["github"],
     "statement": "NecroNet is a verified handle-linked repository (security/AI project); its purpose is to be confirmed."},
    {"subject": ("project", "phishguard"), "predicate": "is_described_as", "tier": "verified",
     "section": "6", "sources": ["github"],
     "statement": "PhishGuard is a verified phishing detection and security project (ML/security)."},
    {"subject": ("project", "rhinoshield"), "predicate": "is_described_as", "tier": "verified",
     "section": "6", "sources": [],
     "statement": "RhinoShield is a conservation project with a DePIN/Web3 angle; the name is verified and the architecture is to be confirmed."},
    {"subject": ("project", "rhinoguardians"), "predicate": "is_described_as", "tier": "self_reported",
     "section": "6", "sources": [],
     "statement": "Linford describes RhinoGuardians as an AI anti-poaching prototype (YOLOv5, about 95 percent accuracy) that originated at the AI Genesis Hackathon in November 2025."},
    {"subject": ("project", "rhinoguardians"), "predicate": "accepted_into", "tier": "flagged",
     "section": "6", "sources": [],
     "statement": "RhinoGuardians reportedly accepted into HBS Foundry via the Aspire Seed Fund as a top-scoring applicant.",
     "rationale": "Acceptance explicitly flagged for verification (sections 6, 7, and 12 item 2)."},
    {"subject": ("project", "spazalink"), "predicate": "is_described_as", "tier": "self_reported",
     "section": "6", "sources": [],
     "statement": "Linford describes SpazaLink as free digital storefronts for informal traders."},
    {"subject": ("project", "spazalink"), "predicate": "placed_at", "tier": "flagged",
     "section": "6", "sources": [],
     "statement": "SpazaLink reportedly placed 3rd at SA Startup Week 2026 (Makers Landing, V&A Waterfront).",
     "rationale": "Placement explicitly flagged for verification (sections 6, 7, and 12 item 2)."},
    {"subject": ("project", "safewatch-sa"), "predicate": "is_described_as", "tier": "self_reported",
     "section": "6", "sources": [],
     "statement": "Linford describes SafeWatch SA as AI community-safety intelligence built on Zoho Catalyst."},
    {"subject": ("project", "guardian-sa"), "predicate": "is_described_as", "tier": "self_reported",
     "section": "6", "sources": [],
     "statement": "Linford describes Guardian-SA as AI security middleware (FastAPI, scikit-learn Random Forest, TF-IDF, POPIA-compliant), submitted to the SS26Hack IDEATHON with Dean Silaule and Francis Matsoso."},
    {"subject": ("project", "linfy-academy"), "predicate": "is_described_as", "tier": "self_reported",
     "section": "6", "sources": [],
     "statement": "Linford describes Linfy Academy as mobile-first youth mentorship for Strand township youth."},
    {"subject": ("project", "rentguard-ct"), "predicate": "is_described_as", "tier": "self_reported",
     "section": "6", "sources": [],
     "statement": "Linford reports RentGuard CT launched in May 2026."},
    {"subject": ("project", "hermes-ecosystem"), "predicate": "is_described_as", "tier": "self_reported",
     "section": "6", "sources": [],
     "statement": "Linford describes the Hermes / Linfy Tech agent ecosystem as a nine-agent orchestration design (Hermes orchestrator; Maverick, Oracle, and Scribe specialists) using Supabase/pgvector and model routing."},
    {"subject": ("owner", None), "predicate": "names_additional_projects", "tier": "self_reported",
     "section": "6", "sources": [],
     "statement": "Other projects named in context: KasiAssist AI, AfriTranslate AI Studio, Linfy Secure Scan, CyberSentinel, Linfy Outreach, Linfy Sage, Beacon, and the Umunqophiso Primary School website (Lwandle, Strand)."},
    # --- Section 7: achievements and recognition -------------------------------
    {"subject": ("owner", None), "predicate": "publishes_writing", "tier": "verified",
     "section": "7", "sources": ["devto"],
     "statement": "Public technical writing on DEV.to."},
    {"subject": ("owner", None), "predicate": "has_shipped_projects", "tier": "verified",
     "section": "7", "sources": ["github"],
     "statement": "Multiple shipped, publicly visible projects (see the verified project table in section 6)."},
    {"subject": ("owner", None), "predicate": "submitted_to_program", "tier": "flagged",
     "section": "7", "sources": [],
     "statement": "ADEL Program 2026 (Atlantic Dialogues Emerging Leaders) submission or acceptance.",
     "rationale": "Status explicitly flagged for verification (section 12 item 2)."},
    {"subject": ("owner", None), "predicate": "submitted_to_program", "tier": "flagged",
     "section": "7", "sources": [],
     "statement": "ICMM Young Leaders Scholarship 2026 (One Young World) status.",
     "rationale": "Status explicitly flagged for verification (section 12 item 2)."},
    {"subject": ("owner", None), "predicate": "participated_in_hackathons", "tier": "self_reported",
     "section": "7", "sources": [],
     "statement": "Linford reports participation in 39 or more hackathon events."},
    {"subject": ("owner", None), "predicate": "holds_certification", "tier": "self_reported",
     "section": "7", "sources": [],
     "statement": "USAII CAIE certification (via hackathon scholarship) and a Claude for Startups application, self-reported."},
    # --- Section 8: education and certifications -------------------------------
    {"subject": ("owner", None), "predicate": "alumnus_of", "tier": "verified",
     "section": "8", "sources": [],
     "statement": "Alumnus of ALX Africa (Data Science and Cybersecurity tracks)."},
    {"subject": ("owner", None), "predicate": "graduate_of", "tier": "self_reported",
     "section": "8", "sources": [],
     "statement": "Graduate of the Aspire Leaders Program (Aspire Institute, HBS-linked); cohort to verify.",
     "rationale": "Document marks this with a mixed marker; taken at the weaker tier."},
    {"subject": ("owner", None), "predicate": "enrolled_at", "tier": "flagged",
     "section": "8", "sources": [],
     "statement": "WorldQuant University enrollment.",
     "rationale": "Not independently verified; confirm (section 12 item 2)."},
    {"subject": ("owner", None), "predicate": "completed_program", "tier": "self_reported",
     "section": "8", "sources": [],
     "statement": "OctoPrep 8-Week Career Prep (Cohort 5, April to June 2026, scholarship), self-reported."},
    {"subject": ("owner", None), "predicate": "completed_courses", "tier": "self_reported",
     "section": "8", "sources": [],
     "statement": "DeepLearning.AI course completions: A2A Protocol; Agentic AI; Voice for AI Agents; Spec-Driven Development with JetBrains."},
    {"subject": ("owner", None), "predicate": "completed_courses", "tier": "self_reported",
     "section": "8", "sources": [],
     "statement": "AWS AI Practitioner Challenge (Udacity with AWS), self-reported."},
    # --- Section 9: writing, talks, and public presence -------------------------
    {"subject": ("owner", None), "predicate": "maintains_presence", "tier": "verified",
     "section": "9", "sources": [],
     "statement": "Maintains an active LinkedIn presence.",
     "rationale": "Activity verified; the distinctive formatting and brand voice claims stay at the weaker tier (see the brand style claim)."},
    {"subject": ("owner", None), "predicate": "featured_in", "tier": "self_reported",
     "section": "9", "sources": [],
     "statement": "A GDG Cape Town community impact showcase video is reported (organizer Jessica Randall)."},
    # --- Section 10: people and network (kept private by default) ---------------
    {"subject": ("owner", None), "predicate": "collaborates_with", "tier": "self_reported",
     "section": "10", "sources": [],
     "statement": "Dean Silaule: final-year Mechatronics Engineering student, IUS Africa cluster leader, described as a close collaborator and prayer partner, Guardian-SA teammate."},
    {"subject": ("owner", None), "predicate": "collaborates_with", "tier": "self_reported",
     "section": "10", "sources": [],
     "statement": "Francis Matsoso: Guardian-SA teammate."},
    {"subject": ("owner", None), "predicate": "connected_to", "tier": "self_reported",
     "section": "10", "sources": [],
     "statement": "Jessica Randall: GDG Cape Town organizer (community impact showcase)."},
    {"subject": ("owner", None), "predicate": "collaborates_with", "tier": "self_reported",
     "section": "10", "sources": [],
     "statement": "Jaswir Raghoe: AI Game Maker collaborator (AI Agent Olympics)."},
    {"subject": ("owner", None), "predicate": "connected_to", "tier": "self_reported",
     "section": "10", "sources": [],
     "statement": "Cheslyn Jacobs: CEO of GoTyme Bank (networking connection)."},
    {"subject": ("owner", None), "predicate": "connected_to", "tier": "self_reported",
     "section": "10", "sources": [],
     "statement": "Dr. Joshua Awesome: executive coach (follow-up relationship)."},
    # --- Section 11: long-term vision -------------------------------------------
    {"subject": ("owner", None), "predicate": "pursues_direction", "tier": "verified",
     "section": "11", "sources": [],
     "statement": "Grows depth in cybersecurity, data analytics, and AI engineering while building tools for African innovation and conservation.",
     "rationale": "Verified as a pattern; specifics carry the weaker tier per the document."},
    {"subject": ("owner", None), "predicate": "plans_to_scale", "tier": "self_reported",
     "section": "11", "sources": [],
     "statement": "Linford reports planning to scale Linfy Tech Solutions into a product studio with an internal multi-agent operating layer (the Hermes ecosystem) for cost-efficient build, marketing, and research."},
    {"subject": ("owner", None), "predicate": "sustains_practice", "tier": "verified",
     "section": "11", "sources": [],
     "statement": "Sustains a build-in-public, faith-driven practice as both portfolio and ministry."},
]

# The six section 12 verification-queue items, by predicate and tier, used by
# tests and by the future verification queue seed check (FS-009).
EXPECTED_FLAGGED_PREDICATES = [
    ("holds_role", "IUS Africa"),
    ("accepted_into", "HBS Foundry"),
    ("placed_at", "SA Startup Week"),
    ("submitted_to_program", "ADEL"),
    ("submitted_to_program", "ICMM"),
    ("enrolled_at", "WorldQuant"),
]
