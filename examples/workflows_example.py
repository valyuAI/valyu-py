"""
Workflows example: browse curated workflows, preview one, run it as a
DeepResearch task, and manage your org's own workflows.
"""

import os
from valyu import Valyu

valyu = Valyu(api_key=os.getenv("VALYU_API_KEY"))

# --- Browse the curated catalog -------------------------------------------

catalog = valyu.workflows.list(scope="valyu")
print(f"{catalog.total} curated workflows. Verticals: {catalog.verticals}")
for wf in (catalog.workflows or [])[:5]:
    print(f"  {wf.slug} - {wf.title}")

# --- Inspect one ------------------------------------------------------------

detail = valyu.workflows.get("ib-company-profile")
wf = detail.workflow
print(f"\n{wf.title} (v{wf.version}, mode={wf.recommended_mode})")
for var in wf.variables or []:
    print(f"  variable: {var.key} ({'required' if var.required else 'optional'})")

# --- Preview the resolved template (no task created) ------------------------

preview = valyu.workflows.preview(
    "ib-company-profile",
    workflow_params={"company": "NVIDIA (NVDA)"},
)
print(f"\nResolved prompt preview: {preview.resolved.input[:200]}...")

# --- Run it as a DeepResearch task ------------------------------------------

task = valyu.deepresearch.create(
    workflow_id="ib-company-profile",
    workflow_params={"company": "NVIDIA (NVDA)"},
)
print(f"\nTask {task.deepresearch_id} created from {task.workflow.slug} v{task.workflow.version}")

# result = valyu.deepresearch.wait(task.deepresearch_id)
# print(result.output)

# --- Manage your org's own workflows ----------------------------------------

created = valyu.workflows.create(
    slug="weekly-competitor-scan",
    title="Weekly Competitor Scan",
    vertical="strategy",
    version={
        "prompt": "Summarize the week's most important developments at {company}.",
        "strategy": "Prioritize primary sources: filings, press releases, earnings calls.",
        "report_format": "Bullet-point briefing, grouped by theme.",
        "variables": [{"key": "company", "label": "Company", "required": True}],
        "recommended_mode": "fast",
    },
)
print(f"\nCreated {created.workflow.slug} v{created.workflow.version}")

updated = valyu.workflows.update(
    created.workflow.slug,
    version={
        "prompt": "Summarize this week's developments at {company}, with sources.",
        "strategy": "Primary sources first; flag anything market-moving.",
        "report_format": "Bullet-point briefing, grouped by theme.",
        "variables": [{"key": "company", "label": "Company", "required": True}],
        "changelog": "Require sources on every bullet",
    },
)
print(f"Updated to v{updated.workflow.version}")

history = valyu.workflows.versions(created.workflow.slug)
for v in history.versions or []:
    print(f"  v{v.version} {'(current)' if v.is_current else ''} - {v.changelog}")

deleted = valyu.workflows.delete(created.workflow.slug)
print(f"Deleted {deleted.slug} at {deleted.deleted_at}")
