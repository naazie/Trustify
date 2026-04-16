from typing import List, Optional
from datetime import datetime

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse

from models.finding import FindingResponse

router = APIRouter()


def get_db(request: Request):
    return request.app.state.db


def _to_response(doc: dict) -> FindingResponse:
    return FindingResponse(
        id=str(doc["_id"]),
        scan_id=doc["scan_id"],
        tool=doc["tool"],
        type=doc.get("type"),
        subcategory=doc.get("subcategory"),
        confidence=doc.get("confidence"),
        severity=doc["severity"],
        rule_id=doc["rule_id"],
        cwe=doc.get("cwe"),
        title=doc["title"],
        description=doc["description"],
        file_path=doc["file_path"],
        line_start=doc["line_start"],
        line_end=doc["line_end"],
        code_snippet=doc.get("code_snippet"),
        commit_history=doc.get("commit_history"),
        found_in_history=doc.get("found_in_history"),
        plain_english=doc.get("plain_english"),
        what_it_means=doc.get("what_it_means"),
        how_to_fix=doc.get("how_to_fix"),
        why_it_matters=doc.get("why_it_matters"),
        remediation=doc.get("remediation"),
        impact_score=doc.get("impact_score"),
        created_at=doc["created_at"],
    )


# ── GET /api/findings/:scan_id ────────────────────────────────────────────────
@router.get("/{scan_id}", response_model=List[FindingResponse])
async def get_findings(
    scan_id: str,
    db=Depends(get_db),
    severity: Optional[str] = None,
    tool: Optional[str] = None,
    type: Optional[str] = None,
    skip: int = 0,
    limit: int = 500,
):
    query: dict = {"scan_id": scan_id}
    if severity:
        query["severity"] = severity
    if tool:
        query["tool"] = tool
    if type:
        query["type"] = type

    cursor = (
        db.findings.find(query)
        .sort([("severity", 1), ("impact_score", -1)])
        .skip(skip)
        .limit(limit)
    )
    findings = await cursor.to_list(length=limit)
    return [_to_response(f) for f in findings]


# ── GET /api/findings/single/:finding_id ─────────────────────────────────────
@router.get("/single/{finding_id}", response_model=FindingResponse)
async def get_finding(finding_id: str, db=Depends(get_db)):
    doc = await db.findings.find_one({"_id": ObjectId(finding_id)})
    if not doc:
        raise HTTPException(404, "Finding not found")
    return _to_response(doc)


# ── GET /api/findings/:scan_id/report ─── JSON Report (view + download) ──────
@router.get("/{scan_id}/report")
async def get_report(
    scan_id: str,
    format: str = "json",   # "json" or "html"
    db=Depends(get_db),
):
    """
    Generate a structured report for a scan.
    - format=json  → returns full JSON report (for download)
    - format=html  → returns standalone HTML report (view in browser)
    """
    # Fetch scan metadata
    scan = await db.scans.find_one({"_id": ObjectId(scan_id)})
    if not scan:
        raise HTTPException(404, "Scan not found")

    # Fetch all findings for this scan
    cursor = (
        db.findings.find({"scan_id": scan_id})
        .sort([("severity", 1), ("impact_score", -1)])
    )
    findings_raw = await cursor.to_list(length=1000)
    findings = [_to_response(f).dict() for f in findings_raw]

    # Serialize datetimes
    def _serialize(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return str(obj)

    # ── JSON report ───────────────────────────────────────────────────────────
    if format == "json":
        report = {
            "report_generated_at": datetime.utcnow().isoformat(),
            "scan": {
                "id": scan_id,
                "source": scan.get("source_url") or scan.get("source_filename"),
                "status": scan.get("status"),
                "created_at": scan.get("created_at", "").isoformat() if scan.get("created_at") else "",
                "completed_at": scan.get("completed_at", "").isoformat() if scan.get("completed_at") else "",
                "languages": scan.get("languages", []),
                "tools_run": scan.get("tools_run", []),
                "summary": dict(scan.get("summary", {})),
            },
            "findings": findings,
        }
        # Convert non-serializable fields
        import json as _json
        json_str = _json.dumps(report, default=_serialize, indent=2)
        return Response(
            content=json_str,
            media_type="application/json",
            headers={
                "Content-Disposition": f'attachment; filename="trustify-report-{scan_id[:8]}.json"'
            },
        )

    # ── HTML report ───────────────────────────────────────────────────────────
    if format == "html":
        scan_source = scan.get("source_url") or scan.get("source_filename") or scan_id
        summary = dict(scan.get("summary", {}))
        generated_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

        sev_color = {"critical": "#ef4444", "warning": "#f59e0b", "info": "#60a5fa"}
        type_icon = {"SECURITY": "🔒", "SECRET": "🔑", "CODE_QUALITY": "🔧", "DEPENDENCY": "📦"}

        # Group findings by severity
        critical_findings = [f for f in findings if f.get("severity") == "critical"]
        warning_findings  = [f for f in findings if f.get("severity") == "warning"]
        info_findings     = [f for f in findings if f.get("severity") == "info"]

        def _render_finding_card(f, idx):
            sev = f.get("severity", "info")
            color = sev_color.get(sev, "#60a5fa")
            icon = type_icon.get(f.get("type", ""), "🔍")
            what_it_means = f.get("what_it_means") or []
            how_to_fix = f.get("how_to_fix") or []
            commits = f.get("commit_history") or []

            what_html = "".join(f"<li>{item}</li>" for item in what_it_means) if what_it_means else "<li>See description above.</li>"
            fix_html  = "".join(f"<li>{item}</li>" for item in how_to_fix) if how_to_fix else "<li>Review the flagged code and apply best practices.</li>"
            commit_html = (
                f'<div class="commits"><strong>⏱ Found in commits:</strong> {", ".join(c[:8] for c in commits[:5])}</div>'
                if commits else ""
            )
            snippet = f.get("code_snippet") or ""
            snippet_html = f'<pre class="snippet"><code>{snippet[:400]}</code></pre>' if snippet else ""

            return f"""
<div class="finding" id="f{idx}">
  <div class="finding-header" style="border-left:4px solid {color}">
    <div class="finding-meta">
      <span class="badge" style="background:{color}22;color:{color};border:1px solid {color}44">{sev.upper()}</span>
      <span class="type-badge">{icon} {f.get('type','')}</span>
      <span class="subcategory">{f.get('subcategory','').replace('_',' ')}</span>
    </div>
    <h3 class="finding-title">{f.get('title','Finding')}</h3>
    <div class="finding-location">
      📄 <code>{f.get('file_path','')}</code> · line {f.get('line_start',0)}
      {'· <span class="history-tag">⏳ IN GIT HISTORY</span>' if f.get('found_in_history') else ''}
      {f'· <span class="cwe">{f["cwe"]}</span>' if f.get("cwe") else ''}
      · <strong>Tool:</strong> {f.get('tool','')}
      {f'· <strong>Confidence:</strong> {round((f.get("confidence") or 0)*100)}%' if f.get('confidence') else ''}
      {f'· <strong>Impact:</strong> {f.get("impact_score","")}/10' if f.get("impact_score") is not None else ''}
    </div>
  </div>
  <div class="finding-body">
    <p class="plain-english">{f.get('plain_english') or f.get('description','')}</p>
    {f'<p class="why"><strong>⚡ Why it matters:</strong> {f["why_it_matters"]}</p>' if f.get("why_it_matters") else ''}
    {commit_html}
    {'<div class="section"><strong>📌 What it means:</strong><ul>' + what_html + '</ul></div>' if what_it_means else ''}
    {'<div class="section"><strong>🔧 How to fix:</strong><ol>' + fix_html + '</ol></div>' if how_to_fix else ''}
    {snippet_html}
  </div>
</div>"""

        all_cards = ""
        for section_label, section_findings in [
            ("🔴 Critical", critical_findings),
            ("🟡 Warning",  warning_findings),
            ("🔵 Info",     info_findings),
        ]:
            if not section_findings:
                continue
            all_cards += f'<h2 class="section-header">{section_label} ({len(section_findings)})</h2>'
            for i, f in enumerate(section_findings):
                all_cards += _render_finding_card(f, i)

        tools_used = ", ".join(scan.get("tools_run", []))
        langs_used = ", ".join(scan.get("languages", []))

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Trustify Security Report — {scan_source}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0f172a; color: #e2e8f0; line-height: 1.6; }}
  .container {{ max-width: 960px; margin: 0 auto; padding: 2rem 1.5rem; }}
  /* Header */
  .report-header {{ background: linear-gradient(135deg,#1e293b,#0f172a); border: 1px solid #334155; border-radius: 12px; padding: 2rem; margin-bottom: 2rem; }}
  .report-title {{ font-size: 1.8rem; font-weight: 800; color: #f1f5f9; margin-bottom: .5rem; }}
  .report-sub {{ color: #94a3b8; font-size: .9rem; }}
  .report-meta {{ display: flex; flex-wrap: wrap; gap: 1rem; margin-top: 1.2rem; font-size: .82rem; color: #64748b; }}
  .report-meta span {{ background: #1e293b; border: 1px solid #334155; padding: .25rem .75rem; border-radius: 6px; }}
  /* Summary cards */
  .summary {{ display: grid; grid-template-columns: repeat(auto-fit,minmax(140px,1fr)); gap: 1rem; margin-bottom: 2rem; }}
  .summary-card {{ background: #1e293b; border: 1px solid #334155; border-radius: 10px; padding: 1.2rem; text-align: center; }}
  .summary-card .num {{ font-size: 2.5rem; font-weight: 900; }}
  .summary-card .lbl {{ font-size: .78rem; text-transform: uppercase; letter-spacing: .05em; color: #64748b; margin-top: .25rem; }}
  .critical-card .num {{ color: #ef4444; }}
  .warning-card  .num {{ color: #f59e0b; }}
  .info-card     .num {{ color: #60a5fa; }}
  .total-card    .num {{ color: #a78bfa; }}
  /* Section headers */
  .section-header {{ font-size: 1.15rem; font-weight: 700; margin: 2rem 0 1rem; padding-bottom: .5rem; border-bottom: 1px solid #334155; }}
  /* Finding card */
  .finding {{ background: #1e293b; border: 1px solid #334155; border-radius: 10px; margin-bottom: 1rem; overflow: hidden; }}
  .finding-header {{ padding: 1rem 1.2rem .75rem; }}
  .finding-meta {{ display: flex; flex-wrap: wrap; gap: .5rem; margin-bottom: .5rem; align-items: center; }}
  .badge {{ font-size: .72rem; font-weight: 700; padding: .2rem .6rem; border-radius: 4px; text-transform: uppercase; letter-spacing: .05em; }}
  .type-badge {{ font-size: .78rem; color: #94a3b8; }}
  .subcategory {{ font-size: .78rem; color: #64748b; font-family: monospace; }}
  .finding-title {{ font-size: 1rem; font-weight: 600; color: #f1f5f9; margin-bottom: .4rem; }}
  .finding-location {{ font-size: .78rem; color: #64748b; }}
  .finding-location code {{ background: #0f172a; padding: .1rem .3rem; border-radius: 3px; color: #93c5fd; font-size: .75rem; }}
  .history-tag {{ background: #7c3aed22; color: #a78bfa; border: 1px solid #7c3aed44; padding: .1rem .4rem; border-radius: 4px; font-size: .72rem; font-weight: 600; }}
  .cwe {{ background: #0f172a; color: #fbbf24; font-family: monospace; font-size: .72rem; padding: .1rem .4rem; border-radius: 3px; }}
  .finding-body {{ padding: 0 1.2rem 1.2rem; border-top: 1px solid #1e293b; }}
  .plain-english {{ color: #cbd5e1; font-size: .9rem; margin: .8rem 0; }}
  .why {{ font-size: .85rem; color: #94a3b8; margin-bottom: .75rem; }}
  .commits {{ font-size: .78rem; background: #7c3aed11; border: 1px solid #7c3aed33; border-radius: 6px; padding: .5rem .75rem; margin-bottom: .75rem; color: #c4b5fd; }}
  .section {{ margin-bottom: .75rem; }}
  .section strong {{ font-size: .85rem; color: #94a3b8; display: block; margin-bottom: .3rem; }}
  ul, ol {{ padding-left: 1.4rem; }}
  li {{ font-size: .85rem; color: #cbd5e1; margin-bottom: .25rem; }}
  .snippet {{ background: #0f172a; border: 1px solid #334155; border-radius: 6px; padding: .75rem 1rem; margin-top: .75rem; overflow-x: auto; }}
  .snippet code {{ font-size: .78rem; color: #7dd3fc; font-family: 'Fira Code', monospace; white-space: pre; }}
  /* Footer */
  .footer {{ text-align: center; color: #334155; font-size: .78rem; margin-top: 3rem; padding-top: 1.5rem; border-top: 1px solid #1e293b; }}
  @media print {{
    body {{ background: #fff; color: #000; }}
    .finding {{ break-inside: avoid; }}
  }}
</style>
</head>
<body>
<div class="container">
  <div class="report-header">
    <div class="report-title">🛡️ Trustify Security Report</div>
    <div class="report-sub">{scan_source}</div>
    <div class="report-meta">
      <span>📅 {generated_at}</span>
      <span>🔧 Tools: {tools_used}</span>
      <span>💬 Languages: {langs_used}</span>
      <span>🆔 Scan: {scan_id[:16]}…</span>
    </div>
  </div>

  <div class="summary">
    <div class="summary-card total-card"><div class="num">{summary.get('total',0)}</div><div class="lbl">Total</div></div>
    <div class="summary-card critical-card"><div class="num">{summary.get('critical',0)}</div><div class="lbl">Critical</div></div>
    <div class="summary-card warning-card"><div class="num">{summary.get('warning',0)}</div><div class="lbl">Warning</div></div>
    <div class="summary-card info-card"><div class="num">{summary.get('info',0)}</div><div class="lbl">Info</div></div>
  </div>

  {all_cards if all_cards else '<div style="text-align:center;padding:3rem;color:#64748b">✅ No findings — clean scan!</div>'}

  <div class="footer">Generated by Trustify · {generated_at}</div>
</div>
</body>
</html>"""

        return Response(
            content=html,
            media_type="text/html",
            headers={
                "Content-Disposition": f'inline; filename="trustify-report-{scan_id[:8]}.html"'
            },
        )

    raise HTTPException(400, "format must be 'json' or 'html'")
