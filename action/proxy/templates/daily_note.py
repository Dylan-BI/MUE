"""
action/proxy/templates/daily_note.py
Builds daily note content that matches build_data.py's parse_note() expectations.

The output format must include these exact patterns:
  - # Daily Note — Day N
  - **Date:** YYYY-MM-DD
  - **Classification:** Foundational|Developing|Operational|Ready For Codex Acceleration
  - **Primary track:** Pyramid operations|Codex productivity|BI judgment
  - **Week Number:** N
  - **Day N**
  - **Required Artifact:** ...
  - ## What I learned today:
  - ## What evidence I produced:
  - ## What remains open:
  - ## Next narrow step:
  - ## Scorecard:  (Area: Unscored)
  - ## Codex gates: (Gate: Yes|No)
"""

from action.proxy.curriculum import (
    CURRICULUM, SCORE_AREAS, CODEX_GATES, LEVEL_DAYS,
    get_classification, get_primary_track, get_level_for_day,
)


# ── Scorecard progression templates ─────────────────────────────────────────
# Maps day ranges to expected scorecard state (trending from Fail→Pass)
_SCORECARD_PROGRESSION = {
    # All areas start as Unscored — instructors assign scores
    range(1, 29): {'Prompt discipline': 'Unscored', 'Repo or workspace analysis': 'Unscored',
                    'Change isolation': 'Unscored', 'Validation order': 'Unscored',
                    'Deployment awareness': 'Unscored', 'Reviewer handoff': 'Unscored',
                    'Reusability': 'Unscored'},
}

# ── Codex gate progression ──────────────────────────────────────────────────
_GATE_PROGRESSION = {
    range(1, 9):   {g: 'No' for g in CODEX_GATES},
    range(9, 13):  {**{g: 'No' for g in CODEX_GATES},
                     'One end-to-end workflow completed': 'Yes',
                     'Business-logic ownership understood': 'Yes'},
    range(13, 18): {**{g: 'No' for g in CODEX_GATES},
                     'One end-to-end workflow completed': 'Yes',
                     'Business-logic ownership understood': 'Yes',
                     'Validation evidence produced without help': 'Yes'},
    range(18, 22): {**{g: 'No' for g in CODEX_GATES},
                     'One end-to-end workflow completed': 'Yes',
                     'Business-logic ownership understood': 'Yes',
                     'Validation evidence produced without help': 'Yes',
                     'One clean reviewable change slice': 'Yes'},
    range(22, 26): {**{g: 'No' for g in CODEX_GATES},
                     'One end-to-end workflow completed': 'Yes',
                     'Business-logic ownership understood': 'Yes',
                     'Validation evidence produced without help': 'Yes',
                     'Proof tasks completed': 'Yes',
                     'One clean reviewable change slice': 'Yes'},
    range(26, 29): {g: 'Yes' for g in CODEX_GATES},
}

# ── Focus-specific learning content ─────────────────────────────────────────
_FOCUS_CONTENT = {
    1: {
        'learned': 'Set up the development environment and explored the admin console. Learned the four chat modes (Ask, Edit, Agent, Plan) and when to use each. Understood prompt structure and context-window limits. Reviewed team communication channels and standup format.',
        'evidence': 'Captured environment setup screenshots. Documented mode selection criteria. Recorded standup format template.',
        'remains': 'Need to practice prompt crafting with real repo analysis. Standup delivery needs rehearsal.',
        'next_step': 'Build three reusable prompts and practice the Codex loop.',
    },
    2: {
        'learned': 'Built three reusable prompts for repo analysis, model validation, and deployment/QC. Learned the Codex loop: pull context → summarise → identify → execute → record. Completed Handoff Reading exercise — extracted 5 facts from an existing handoff in under 60 seconds.',
        'evidence': 'Three working prompts with revision log showing first failure and fix. Handoff Reading exercise result documenting extraction accuracy.',
        'remains': 'Prompts need testing on real scenarios. Context pull scoping could be tighter.',
        'next_step': 'Practice change isolation and deliver first standup update.',
    },
    3: {
        'learned': 'Practised narrow-scope review behaviour and change isolation. Learned to scope a reviewable change slice with purpose, audience, and focus. Delivered first 30-second standup update to the team.',
        'evidence': 'Clean review draft documenting purpose, audience, focus, and reviewer questions. Standup note recording what was done, what is next, and any blockers.',
        'remains': 'Change slice boundaries need refinement. Standup timing needs practice.',
        'next_step': 'Trace model lineage from source through all layers.',
    },
    4: {
        'learned': 'Traced source → transformation → snapshot → rollup → QC pipeline. Built a one-page dependency map naming each layer and its responsibilities. Identified which layer owns row selection, deduplication, and aggregation.',
        'evidence': 'Dependency map documenting source inputs, transformation logic, snapshot definitions, rollup paths, and QC checkpoints.',
        'remains': 'Need to validate hierarchy structure in the actual model. Rollup logic unclear for derived measures.',
        'next_step': 'Build deployment checklist and set up task tracking.',
    },
    5: {
        'learned': 'Built v1 deployment checklist covering model migration, security, access, and rerun procedures. Set up task tracking in GitHub Issues. Completed Week 1 scorecard self-assessment.',
        'evidence': 'Deployment checklist covering preflight, migration, access, and rerun. Task board snapshot with initial work items. Week 1 Scorecard with self-ratings.',
        'remains': 'Checklist needs validation against actual deployment. Task board items need acceptance criteria.',
        'next_step': 'Map source-to-output inventory for the data foundation layer.',
    },
    6: {
        'learned': 'Mapped all source inputs to their target outputs across the model. Defined reporting grain for each output. Communicated findings as a brief status update to a peer.',
        'evidence': 'Source-to-output inventory documenting each source, its transformation, target output, and grain definition. Status update note shared with team.',
        'remains': 'Some source-to-output paths are unclear. Grain definitions need peer validation.',
        'next_step': 'Identify row ownership and deduplication logic.',
    },
    7: {
        'learned': 'Identified who owns row selection in each layer. Traced deduplication logic from source through transformation. Documented history handling rules for dimension tables.',
        'evidence': 'Row ownership note mapping each table to its owning layer. Deduplication logic documenting merge rules and conflict resolution.',
        'remains': 'Some edge cases in deduplication are unclear. History handling needs clarification.',
        'next_step': 'Map aggregation boundaries and double-counting risks.',
    },
    8: {
        'learned': 'Identified double-counting risks at aggregation boundaries. Mapped grain boundaries between fact tables. Documented where weighted vs summed vs derived totals are used.',
        'evidence': 'Aggregation boundary note documenting grain definitions, double-counting risk areas, and total calculation methods.',
        'remains': 'Need to validate aggregation logic with actual data samples.',
        'next_step': 'Complete PT1: Repository Analysis Brief.',
    },
    9: {
        'learned': 'Completed PT1: Repository Analysis Brief — documented business purpose, dependency order, key I/O, risks, and safe change points. Completed Codex Exercise 2: Context Pull using Pattern 1 to pull context, evaluate scope, and refine.',
        'evidence': 'PT1 Repository Analysis Brief with business context, dependency map, risk assessment. Context Pull exercise with before/after prompt comparison.',
        'remains': 'Some dependency relationships need validation. Risk assessment could be more specific.',
        'next_step': 'Validate hierarchy structure and close data-foundation layer.',
    },
    10: {
        'learned': 'Validated hierarchy structure across the model. Closed the data-foundation layer by confirming all upstream dependencies are resolved. Completed Week 2 scorecard.',
        'evidence': 'Hierarchy validation note documenting level structure, parent-child relationships, and rollup paths. Week 2 Scorecard.',
        'remains': 'Some hierarchy levels need peer review. Scorecard areas still showing gaps.',
        'next_step': 'Validate measure and service logic.',
    },
    11: {
        'learned': 'Validated active/inactive row logic in the model. Traced cancellation handling through the transformation layer. Confirmed measure calculations match business definitions.',
        'evidence': 'Active-row logic note documenting filter conditions, status flags, and cancellation propagation rules.',
        'remains': 'Edge cases in cancellation handling need further testing.',
        'next_step': 'Validate time logic and parameters.',
    },
    12: {
        'learned': 'Validated time logic including period definitions, target calculations, and list/parameter/level behaviour. Completed Codex Exercise 3: State Summary — drafted 3-sentence state summary using Pattern 2.',
        'evidence': 'Time logic note with period definitions and target calculations. List/parameter note documenting runtime behaviour. State Summary exercise result.',
        'remains': 'Time logic edge cases (year-end rollover, leap year) need testing.',
        'next_step': 'Begin Week 3 with PT3: Metric Lineage Walkthrough.',
    },
    13: {
        'learned': 'Completed PT3: Metric Lineage Walkthrough — traced counting grain, active-row rules, period definitions, calculation point, and rollup path. Validated snapshot logic against source data.',
        'evidence': 'PT3 Metric Lineage Walkthrough documenting grain, active-row rules, period definitions, calc point, and full rollup path. Snapshot validation note.',
        'remains': 'Some calculation edge cases need verification. Snapshot refresh timing needs clarification.',
        'next_step': 'Validate rollup behaviour from lowest grain to summaries.',
    },
    14: {
        'learned': 'Validated rollup behaviour from lowest grain through summaries. Identified where weighted, summed, and derived totals are used. Confirmed aggregation boundaries match business definitions.',
        'evidence': 'Rollup behaviour note documenting grain hierarchy, aggregation methods, and boundary conditions for each summary level.',
        'remains': 'Weighted total logic needs peer validation.',
        'next_step': 'Build QC evidence pack and practise validation checks.',
    },
    15: {
        'learned': 'Drafted QC plan documenting what to check, expected outcomes, and anomaly classification. Used Codex Pattern 4 (Validation Check) to classify gaps. Escalated anomalies to a peer for discussion.',
        'evidence': 'QC evidence template (first pass) with check items and expected results. Validation Check prompt result. Anomaly escalation note.',
        'remains': 'QC template needs refinement based on peer feedback.',
        'next_step': 'Complete QC evidence pack and draft handoff.',
    },
    16: {
        'learned': 'Completed PT4: QC Evidence Pack — ran all checks, separated defects from limitations. Used Codex Pattern 3 (Handoff Draft) to record findings for reviewer consumption.',
        'evidence': 'Completed PT4 QC evidence pack with check results, defect classification, and limitation documentation. Handoff Draft exercise result graded against Quality Rubric.',
        'remains': 'Some defect classifications may need escalation. Handoff clarity could improve.',
        'next_step': 'Prepare deployment preflight and task breakdown.',
    },
    17: {
        'learned': 'Mapped deployment sequence from model export through import, validation, and go-live. Documented access and reviewer boundaries. Broke deployment into assignable tasks for team distribution.',
        'evidence': 'Preflight checklist with sequence steps. Access note documenting permissions and reviewer paths. Task breakdown with assignees and acceptance criteria.',
        'remains': 'Access permissions need verification. Task estimates need team review.',
        'next_step': 'Complete PT5: Deployment Rehearsal.',
    },
    18: {
        'learned': 'Completed PT5: Deployment Rehearsal — drafted deployment sequence, ran dry run, and recorded results. Identified gaps between planned and actual deployment steps.',
        'evidence': 'PT5 Deployment Rehearsal record with draft sequence, dry run results, gap analysis, and corrective actions.',
        'remains': 'Deployment timing estimates need refinement. Rollback procedure needs testing.',
        'next_step': 'Close operations layer and sync with team.',
    },
    19: {
        'learned': 'Finalised deployment, QC, and handoff readiness. Gave summary update of Week 3 completion to the team. Completed Week 3 scorecard showing improvement across all areas.',
        'evidence': 'Week 3 Scorecard with ratings. Deployment closeout documenting final state. Team sync note recording status and next steps.',
        'remains': 'Final handoff package needs assembly. Reusable asset not yet started.',
        'next_step': 'Begin contribution layer — content movement and handoff path.',
    },
    20: {
        'learned': 'Validated artifact movement between environments. Built reviewer path documenting how work flows from development through review to production. Updated task board with current status.',
        'evidence': 'Content-movement checklist with environment transition steps. Handoff draft documenting reviewer consumption requirements. Task board update.',
        'remains': 'Reviewer path needs team validation. Task board items need priority ordering.',
        'next_step': 'Complete PT2: Review Dry Run and PT6: Handoff Test.',
    },
    21: {
        'learned': 'Completed PT2: Review Workflow Dry Run — walked through review process end-to-end. Completed PT6: Handoff Test — verified handoff package is consumable without clarification. Used Codex Pattern 6 (Change Impact) to scope review package.',
        'evidence': 'PT2 Review package with dry run results. PT6 Handoff test result. Change Impact prompt result.',
        'remains': 'Review process needs one more iteration. Handoff package could be clearer.',
        'next_step': 'Select narrow change slice and practise feedback.',
    },
    22: {
        'learned': 'Selected a narrow change slice with clear baseline and owning surface. Practised receiving feedback from a peer on the change charter. Learned to incorporate feedback without defensive reaction.',
        'evidence': 'Change-slice charter with baseline and owning surface. Feedback reception note documenting what was received and how it was incorporated.',
        'remains': 'Change slice scope may need narrowing. Feedback incorporation speed needs improvement.',
        'next_step': 'Draft fix path and validate.',
    },
    23: {
        'learned': 'Drafted the smallest fix path for the change slice. Ran validation cycle and repaired issues. Completed Codex Exercise 6: Bounded Codex Simulation with 2+ "Do NOT" constraints.',
        'evidence': 'Fix-path draft with minimal changes. Validation record showing checks passed. Bounded Codex exercise result with constraint documentation.',
        'remains': 'Fix path needs peer review. Bounded constraints need refinement.',
        'next_step': 'Assemble review package and close the change slice.',
    },
    24: {
        'learned': 'Recorded before/after state for the change slice. Prepared review package and stress-tested it. Used Codex Pattern 3 to draft handoff graded against Quality Rubric. Completed Week 4 scorecard.',
        'evidence': 'Before/after note. Review package with test results. Handoff graded against rubric. Week 4 Scorecard.',
        'remains': 'Review package needs one final read-through. Rubric score could improve.',
        'next_step': 'Rehearse handoff with peer review.',
    },
    25: {
        'learned': 'Practised surface recommendation and reviewer explanation. Walked through handoff with a peer and incorporated their input. Finalised the handoff rehearsal.',
        'evidence': 'Surface recommendation note. Reviewer summary. Final handoff rehearsal log. Peer feedback log.',
        'remains': 'Final handoff polish needed. Peer feedback needs one more incorporation cycle.',
        'next_step': 'Create reusable team asset.',
    },
    26: {
        'learned': 'Chartered a reusable Codex prompt template (Pattern 1–7). Drafted v1, tested it, and revised based on results. Shared draft with teammate for early feedback.',
        'evidence': 'Asset charter. Draft v1 of prompt pattern template. Test note with results. v2 revision. Early feedback note.',
        'remains': 'Asset needs platform specificity. Testing coverage needs expansion.',
        'next_step': 'Finalise asset and hand off to team.',
    },
    27: {
        'learned': 'Added platform specificity and example use cases to the reusable asset. Completed external review and published final version. Handed off the asset to a teammate with a walkthrough.',
        'evidence': 'Surface-aware revision. Example use case documentation. Gap list and v3. Final published asset. Team handoff record.',
        'remains': 'Asset documentation could be more detailed. Handoff walkthrough needs recording.',
        'next_step': 'Complete Codex Gate and final closeout.',
    },
    28: {
        'learned': 'Completed Bounded Codex test. Ran Exercise 5: Manual-vs-Codex Comparison for one defined task. Drafted final readiness statement. Passed Codex Gate with all 6 gates cleared.',
        'evidence': 'Codex comparison note with Manual-vs-Codex results. Final readiness statement. Final Readiness Package with all exercises completed. Team closeout note.',
        'remains': 'Nothing — curriculum complete. Ready for bounded Codex use in production.',
        'next_step': 'Begin bounded Codex use in production workflows.',
    },
}


def get_scorecard(day_number: int) -> dict[str, str]:
    """Return the scorecard state for a given day number."""
    for day_range, scores in _SCORECARD_PROGRESSION.items():
        if day_number in day_range:
            return dict(scores)
    return {area: 'Fail' for area in SCORE_AREAS}


def get_codex_gates(day_number: int) -> dict[str, str]:
    """Return the codex gate state for a given day number."""
    for day_range, gates in _GATE_PROGRESSION.items():
        if day_number in day_range:
            return dict(gates)
    return {g: 'No' for g in CODEX_GATES}


def build_note_content(date: str, day_number: int) -> str:
    """
    Build a complete daily note in the format expected by build_data.py.

    Args:
        date: ISO date string (YYYY-MM-DD)
        day_number: Curriculum day number (1-28)

    Returns:
        Markdown content for the daily note.
    """
    entry = CURRICULUM.get(day_number)
    if not entry:
        raise ValueError(f'No curriculum entry for day {day_number}')

    classification = get_classification(day_number)
    primary_track = get_primary_track(day_number)
    level = get_level_for_day(day_number)
    focus = entry['focus']
    week_number = entry['week_number']
    required_artifact = entry['required_artifact']

    # Get content for this day's focus
    content = _FOCUS_CONTENT.get(day_number, {})
    learned = content.get('learned', f'Practised {focus} concepts and completed exercises.')
    evidence = content.get('evidence', f'Produced evidence artifacts for {focus}.')
    remains = content.get('remains', 'Continue practising and refining skills.')
    next_step = content.get('next_step', 'Progress to the next curriculum day.')

    # Build scorecard
    scorecard = get_scorecard(day_number)
    scorecard_lines = '\n'.join(f'{area}: {scorecard[area]}' for area in SCORE_AREAS)

    # Build codex gates
    gates = get_codex_gates(day_number)
    gate_lines = '\n'.join(f'{gate}: {gates[gate]}' for gate in CODEX_GATES)

    note = f"""# Daily Note — Day {day_number}

**Date:** {date}
**Classification:** {classification}
**Primary track:** {primary_track}
**Level:** {level}
**Week Number:** {week_number}
**Day {day_number}**
**Required Artifact:** {required_artifact}

## What I learned today:
{learned}

## What evidence I produced:
{evidence}

## What remains open:
{remains}

## Next narrow step:
{next_step}

## Scorecard:
{scorecard_lines}

## Codex gates:
{gate_lines}
"""
    return note
