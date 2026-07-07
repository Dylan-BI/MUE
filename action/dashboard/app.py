"""
action/dashboard/app.py
Ergonomic interactive Streamlit dashboard for MUE learner progress.
Reads all data from the action/ folder and visualizes progress,
scorecards, evidence, and readiness classification.

Usage:
    streamlit run action/dashboard/app.py
    # or:  python -m streamlit run action/dashboard/app.py
"""
import os
import sys
from datetime import date, datetime
from collections import Counter

# Ensure we can import reader
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reader

import streamlit as st

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title='MUE Learner Dashboard',
    page_icon='📊',
    layout='wide',
    initial_sidebar_state='expanded',
)

# ── Load data ────────────────────────────────────────────────────────────────
@st.cache_data(ttl=10)
def load_data():
    notes = reader.load_all_notes()
    summary = reader.compute_summary(notes)
    evidence = reader.get_proof_task_evidence()
    reports = reader.get_reports()
    weeks = reader.compute_week_boundaries(notes)
    return notes, summary, evidence, reports, weeks

notes, summary, evidence, reports, weeks = load_data()

# ── Color palette ────────────────────────────────────────────────────────────
CLS_COLORS = {
    'Foundational': '#6c757d',
    'Developing': '#ffc107',
    'Operational': '#0d6efd',
    'Ready for codex acceleration': '#198754',
}
SCORE_COLORS = {'Pass': '#198754', 'Partial': '#ffc107', 'Fail': '#dc3545'}
TRACK_COLORS = {
    'Pyramid operations': '#0d6efd',
    'Codex productivity': '#6f42c1',
    'BI judgment': '#fd7e14',
}

# ── Sidebar ──────────────────────────────────────────────────────────────────
st.sidebar.title('📊 MUE Dashboard')
st.sidebar.caption('Multifaceted User Education')

if notes:
    total = summary['total_days']
    pct = min(total / 28 * 100, 100)
    st.sidebar.markdown(f'**Progress:** {total}/28 days ({pct:.0f}%)')
    st.sidebar.progress(pct / 100)
    st.sidebar.markdown(f'**Classification:** {summary["latest_classification"]}')
    st.sidebar.markdown(f'**Evidence files:** {summary["evidence_count"]}')
else:
    st.sidebar.info('No notes found yet. Start your training!')

page = st.sidebar.radio(
    'Navigate',
    ['📋 Overview', '📅 Daily Progress', '🏆 Scorecard',
     '✅ Proof Tasks', '📁 Evidence', '📈 Classification Trend', '🚪 Codex Gate'],
)
st.sidebar.markdown('---')
st.sidebar.caption(f'Refreshed: {datetime.now():%H:%M:%S}')
if st.sidebar.button('🔄 Refresh Data'):
    st.cache_data.clear()
    st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════════
if page == '📋 Overview':
    st.title('📋 Overview')
    st.caption('High-level summary of your MUE training progress')

    # -- Top row metrics --
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric('Days Completed', summary['total_days'], f'{28 - summary["total_days"]} remaining')
    with col2:
        st.metric('Weeks Active', summary['unique_weeks'])
    with col3:
        ev = summary['evidence_count']
        st.metric('Evidence Artifacts', ev)
    with col4:
        st.metric('Classification', summary['latest_classification'])

    # -- Week progress --
    st.subheader('📆 Program Progress')
    if notes:
        day_numbers = sorted([n['day_number'] for n in notes if n['day_number']])
        all_days = list(range(1, 29))
        cols = st.columns(28)
        for i, day in enumerate(all_days):
            done = day in day_numbers
            bg = '#198754' if done else '#e9ecef'
            cols[i].markdown(
                f'<div style="background:{bg};border-radius:4px;text-align:center;'
                f'padding:6px 0;font-size:11px;color:{"white" if done else "#888"};'
                f'width:100%">{day}</div>',
                unsafe_allow_html=True,
            )
        st.caption('Green = completed | Grey = not yet done')

        # -- Track distribution --
        st.subheader('🎯 Track Distribution')
        tracks = summary['completed_tracks']
        if tracks:
            total_days = sum(tracks.values())
            track_colors = {'Pyramid operations': '#0d6efd', 'Codex productivity': '#6f42c1', 'BI judgment': '#fd7e14'}
            st.bar_chart(
                data={'Days': tracks},
                color=['#0d6efd', '#6f42c1', '#fd7e14'],
                height=250,
            )
            for track, count in sorted(tracks.items()):
                pct = count / total_days * 100
                color = track_colors.get(track, '#888')
                st.markdown(
                    f'<span style="color:{color}">■</span> **{track}:** {count} days ({pct:.0f}%)',
                    unsafe_allow_html=True,
                )
        else:
            st.info('No track data recorded yet.')
    else:
        st.info('No notes found. Create your first daily note to start tracking.')

    # -- Quick links --
    st.subheader('🔗 Quick Links')
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown('[📖 4-Week Onboarding Map](../source/4-Week%20Onboarding%20Map.md)')
    with c2:
        st.markdown('[📝 Retention Review](templates/retention-review.md)')
    with c3:
        st.markdown('[✅ Contributor Readiness Check](templates/contributor-readiness-check.md)')


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: DAILY PROGRESS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == '📅 Daily Progress':
    st.title('📅 Daily Progress')
    st.caption('Day-by-day breakdown of your training journey')

    if not notes:
        st.info('No notes found yet. Create your first daily note!')
    else:
        # Sort notes by day number
        sorted_notes = sorted(notes, key=lambda x: x['day_number'] if x['day_number'] else 0)

        # -- Timeline --
        for n in sorted_notes:
            day = n['day_number'] or '?'
            date_str = n['date'].strftime('%a %d %b') if n['date'] else '—'
            cls = n['classification'] or '—'
            track = n['primary_track'] or '—'
            artifact = n['required_artifact'] or '—'

            with st.expander(f'**Day {day}** — {date_str}  |  {cls}'):
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f'**Track:** {track}')
                    st.markdown(f'**Classification:** {cls}')
                    st.markdown(f'**Evidence:** {artifact}')
                with c2:
                    st.markdown(f'**Learned:** {n["what_learned"] or "—"}')
                    st.markdown(f'**Next step:** {n["next_step"] or "—"}')

                if n['scorecard']:
                    st.markdown('**Scorecard:**')
                    for area, score in n['scorecard'].items():
                        color = SCORE_COLORS.get(score, '#888')
                        label = area.replace('_', ' ').title()
                        st.markdown(f'- {label}: <span style="color:{color}">**{score}**</span>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: SCORECARD
# ═══════════════════════════════════════════════════════════════════════════════
elif page == '🏆 Scorecard':
    st.title('🏆 Scorecard Tracker')
    st.caption('Weekly scores across all 7 competency areas')

    if not summary['scorecard_trend']:
        st.info('No scorecard data yet. Complete your first week to see scores.')
    else:
        trend = summary['scorecard_trend']
        area_labels = {
            'prompt_discipline': 'Prompt Discipline',
            'repo_analysis': 'Repo Analysis',
            'change_isolation': 'Change Isolation',
            'validation_order': 'Validation Order',
            'deployment_awareness': 'Deployment Awareness',
            'reviewer_handoff': 'Reviewer Handoff',
            'reusability': 'Reusability',
        }

        for area_key, area_label in area_labels.items():
            scores = trend.get(area_key, [])
            if not scores:
                continue

            st.markdown(f'**{area_label}**')
            cols = st.columns(len(scores))
            for i, entry in enumerate(scores):
                score = entry['score']
                color = SCORE_COLORS.get(score, '#888')
                day = entry['day']
                cols[i].markdown(
                    f'<div style="background:{color};border-radius:4px;text-align:center;'
                    f'padding:8px 4px;color:white;font-weight:bold;font-size:14px;'
                    f'min-width:50px">{score}<br><span style="font-size:10px">Day {day}</span></div>',
                    unsafe_allow_html=True,
                )

            # Determine trend
            values = [{'Pass': 2, 'Partial': 1, 'Fail': 0}.get(s['score'], 0) for s in scores]
            if len(values) >= 2:
                if values[-1] > values[0]:
                    st.caption('📈 Improving')
                elif values[-1] < values[0]:
                    st.caption('📉 Declining — needs attention')
                else:
                    st.caption('➡️ Steady')
            st.markdown('---')

        # Fail count warning
        fail_areas = []
        for area_key, scores in trend.items():
            if scores and scores[-1]['score'] == 'Fail':
                fail_areas.append(area_key)
        if len(fail_areas) >= 2:
            st.warning(f'⚠️ {len(fail_areas)} areas scored **Fail** in the latest week. Repeat this layer before expanding scope.')


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: PROOF TASKS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == '✅ Proof Tasks':
    st.title('✅ Proof Task Tracker')
    st.caption('6 proof tasks required before passing the Codex Gate')

    pt_mentions = summary.get('proof_task_mentions', {})
    if not pt_mentions:
        st.info('No proof task data yet.')
    else:
        for abbr, info in sorted(pt_mentions.items()):
            status = '✅' if info['found'] else '⬜'
            days = info['days'] or []
            days_str = f'(found on days {", ".join(map(str, days))})' if days else ''
            st.markdown(f'{status} **{info["title"]}** — {info["description"]} {days_str}')

        completed = sum(1 for info in pt_mentions.values() if info['found'])
        st.markdown('---')
        st.markdown(f'**Progress:** {completed}/6 proof tasks complete')
        st.progress(completed / 6)
        if completed == 6:
            st.success('🎉 All 6 proof tasks completed! You\'re ready for the Codex Gate.')
        else:
            st.info(f'{6 - completed} proof task(s) remaining.')


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: EVIDENCE
# ═══════════════════════════════════════════════════════════════════════════════
elif page == '📁 Evidence':
    st.title('📁 Evidence Gallery')
    st.caption('All evidence artifacts produced during training')

    if not evidence:
        st.info('No evidence files yet. Every day should produce one evidence artifact.')
    else:
        st.markdown(f'**{len(evidence)}** artifacts found in `action/evidence/`')
        st.divider()

        # Group by week
        weeks_map = {}
        for e in evidence:
            wk = e['modified'].strftime('%Y-W%V')
            weeks_map.setdefault(wk, []).append(e)

        for wk in sorted(weeks_map.keys(), reverse=True):
            items = weeks_map[wk]
            with st.expander(f'**{wk}** — {len(items)} artifacts'):
                for e in items:
                    size_kb = e['size_bytes'] / 1024
                    mod = e['modified'].strftime('%d %b %H:%M')
                    st.markdown(
                        f'- `{e["relative_path"]}` ({size_kb:.1f} KB, {mod})'
                    )


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: CLASSIFICATION TREND
# ═══════════════════════════════════════════════════════════════════════════════
elif page == '📈 Classification Trend':
    st.title('📈 Readiness Classification Trend')
    st.caption('How your readiness level has evolved over time')

    cls_seq = summary['classification_sequence']
    if not cls_seq:
        st.info('No classification data yet.')
    else:
        # Map classifications to numeric for charting
        cls_order = ['Foundational', 'Developing', 'Operational', 'Ready For Codex Acceleration']
        cls_map = {c: i for i, c in enumerate(cls_order)}

        chart_data = []
        for entry in cls_seq:
            idx = cls_map.get(entry['classification'], 0)
            chart_data.append({
                'day': entry['day'],
                'level': idx + 1,
                'classification': entry['classification'],
                'date': entry['date'].strftime('%d %b') if entry['date'] else '',
            })

        # Simple bar chart of classification levels
        import pandas as pd
        df = pd.DataFrame(chart_data)
        st.bar_chart(
            df.set_index('day')['level'],
            height=300,
            use_container_width=True,
        )

        # Y-axis labels
        st.caption('Level: 1=Foundational, 2=Developing, 3=Operational, 4=Ready For Codex Acceleration')

        # Table
        st.subheader('Classification History')
        for entry in cls_seq:
            day = entry['day']
            cls = entry['classification']
            date_str = entry['date'].strftime('%a %d %b') if entry['date'] else ''
            color = CLS_COLORS.get(cls.lower(), '#888')
            st.markdown(
                f'Day {day} ({date_str}): '
                f'<span style="color:{color};font-weight:bold">{cls}</span>',
                unsafe_allow_html=True,
            )


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: CODEX GATE
# ═══════════════════════════════════════════════════════════════════════════════
elif page == '🚪 Codex Gate':
    st.title('🚪 Codex Gate Status')
    st.caption('Final checkpoint — all 6 gates must be Yes to begin bounded Codex use')

    gate_status = summary.get('codex_gate_status', {})
    if not gate_status:
        st.info('No Codex Gate data yet. This is checked on Day 28 (end of Week 4).')
    else:
        gate_labels = {
            'end_to_end_workflow': 'End-to-end workflow completed',
            'business_logic_ownership': 'Business-logic ownership understood',
            'validation_evidence': 'Validation evidence without help',
            'proof_tasks_completed': 'All 6 proof tasks completed',
            'clean_change_slice': 'Clean change slice delivered',
            'reusable_asset': 'Reusable asset created',
        }

        for key, label in gate_labels.items():
            status = gate_status.get(key, '—')
            icon = '✅' if status == 'Yes' else ('❌' if status == 'No' else '⬜')
            st.markdown(f'{icon} **{label}:** {status}')

        st.divider()
        all_yes = all(
            gate_status.get(k) == 'Yes'
            for k in ['end_to_end_workflow', 'business_logic_ownership', 'validation_evidence',
                      'proof_tasks_completed', 'clean_change_slice', 'reusable_asset']
        )

        if all_yes:
            st.success('🎉 **Codex Gate: PASSED** — You may begin bounded Codex use.')
            st.balloons()
        else:
            missing = [gate_labels[k] for k in gate_status if gate_status.get(k) != 'Yes']
            if missing:
                st.warning(f'**Codex Gate: NOT YET** — Missing: {", ".join(missing)}')
            else:
                st.warning('**Codex Gate: NOT YET** — Complete the gate checklist on Day 28.')


# ── Footer ────────────────────────────────────────────────────────────────────
st.sidebar.markdown('---')
st.sidebar.caption('Built for MUE • ' + date.today().strftime('%Y-%m-%d'))
