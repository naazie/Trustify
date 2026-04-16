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

        # Group findings by severity
        critical_findings = [f for f in findings if f.get("severity") == "critical"]
        warning_findings  = [f for f in findings if f.get("severity") == "warning"]
        info_findings     = [f for f in findings if f.get("severity") == "info"]

        def _render_finding_card(f, idx):
            sev = f.get("severity", "info")
            what_it_means = f.get("what_it_means") or []
            how_to_fix    = f.get("how_to_fix") or []
            commits       = f.get("commit_history") or []
            subcategory   = f.get("subcategory", "").replace("_", " ")
            confidence    = f.get("confidence")
            impact        = f.get("impact_score")

            what_html   = "".join(f"<li>{item}</li>" for item in what_it_means)
            fix_html    = "".join(f"<li>{step}</li>" for step in how_to_fix)
            commit_html = (
                f'<div class="commits-box"><strong>Found in git commits:</strong> '
                + ", ".join(f"<code>{c[:8]}</code>" for c in commits[:6])
                + "</div>"
            ) if commits else ""
            snippet     = (f.get("code_snippet") or "")[:500]
            snippet_html = f'<div class="sub-section"><div class="sub-label">Code</div><div class="snippet"><code>{snippet}</code></div></div>' if snippet else ""

            meta_extras = ""
            if confidence:
                meta_extras += f' &middot; <strong>Confidence:</strong> {round(confidence * 100)}%'
            if impact is not None:
                meta_extras += f' &middot; <strong>Impact:</strong> {impact}/10'

            return f"""
<div class="finding" id="f{idx}">
  <div class="finding-header sev-{sev}">
    <div class="finding-tags">
      <span class="tag tag-{sev}">{sev.upper()}</span>
      {f'<span class="tag tag-type">{f.get("type","")}</span>' if f.get("type") else ''}
      {f'<span class="tag tag-type">{subcategory}</span>' if subcategory else ''}
      <span class="tag tag-tool">{f.get("tool","")}</span>
      {f'<span class="tag tag-cwe">{f["cwe"]}</span>' if f.get("cwe") else ''}
      {f'<span class="tag tag-history">git history</span>' if f.get("found_in_history") else ''}
    </div>
    <div class="finding-title">{f.get("title", "Finding")}</div>
    <div class="finding-loc">
      <strong>{f.get("file_path","")}</strong> &middot; line {f.get("line_start", 0)}{meta_extras}
    </div>
  </div>
  <div class="finding-body">
    <p class="plain-english">{f.get("plain_english") or f.get("description", "")}</p>
    {f'<div class="why-matters"><strong>Why it matters:</strong> {f["why_it_matters"]}</div>' if f.get("why_it_matters") else ''}
    {commit_html}
    {'<div class="sub-section"><div class="sub-label">What it means</div><ul class="findings-list">' + what_html + '</ul></div>' if what_it_means else ''}
    {'<div class="sub-section"><div class="sub-label">How to fix</div><ol class="fix-list">' + fix_html + '</ol></div>' if how_to_fix else ''}
    {snippet_html}
  </div>
</div>"""

        all_cards = ""
        for section_label, dot_color, section_findings in [
            ("Critical Findings",  "#ef4444", critical_findings),
            ("Warning Findings",   "#f59e0b", warning_findings),
            ("Informational",      "#3b82f6", info_findings),
        ]:
            if not section_findings:
                continue
            all_cards += f'<div class="section-heading"><span class="dot" style="background:{dot_color}"></span>{section_label} <span style="color:#a8a29e;font-weight:400">({len(section_findings)})</span></div>'
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
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=Playfair+Display:wght@700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

  body {{
    font-family: 'DM Sans', system-ui, sans-serif;
    background: #fafaf9;
    color: #1c1917;
    line-height: 1.65;
    font-size: 14px;
    -webkit-font-smoothing: antialiased;
  }}

  /* ── Layout ── */
  .page {{ max-width: 900px; margin: 0 auto; padding: 3rem 2rem 5rem; }}

  /* ── Cover ── */
  .cover {{
    border-bottom: 2px solid #e7e5e4;
    padding-bottom: 2.5rem;
    margin-bottom: 2.5rem;
  }}
  .cover-eyebrow {{
    display: inline-flex; align-items: center; gap: 6px;
    font-size: 11px; font-weight: 700; letter-spacing: .1em;
    text-transform: uppercase; color: #059669;
    background: #ecfdf5; border: 1px solid #a7f3d0;
    padding: 4px 12px; border-radius: 999px; margin-bottom: 1.2rem;
  }}
  .cover-title {{
    font-family: 'Playfair Display', Georgia, serif;
    font-size: 2.4rem; font-weight: 700;
    color: #1c1917; line-height: 1.2; margin-bottom: .6rem;
  }}
  .cover-source {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 13px; color: #78716c;
    word-break: break-all; margin-bottom: 1.5rem;
  }}
  .cover-meta {{
    display: flex; flex-wrap: wrap; gap: .6rem;
  }}
  .meta-pill {{
    font-size: 12px; color: #57534e;
    background: #fff; border: 1px solid #e7e5e4;
    padding: 4px 12px; border-radius: 6px;
  }}

  /* ── Summary grid ── */
  .summary {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1rem;
    margin-bottom: 3rem;
  }}
  .summary-card {{
    background: #fff;
    border: 1px solid #e7e5e4;
    border-radius: 10px;
    padding: 1.25rem 1rem;
    text-align: center;
  }}
  .summary-card .num {{ font-size: 2.6rem; font-weight: 800; line-height: 1; }}
  .summary-card .lbl {{
    font-size: 11px; font-weight: 600; letter-spacing: .08em;
    text-transform: uppercase; color: #a8a29e; margin-top: 6px;
  }}
  .c-total    {{ border-top: 3px solid #a78bfa; }} .c-total    .num {{ color: #7c3aed; }}
  .c-critical {{ border-top: 3px solid #ef4444; }} .c-critical .num {{ color: #dc2626; }}
  .c-warning  {{ border-top: 3px solid #f59e0b; }} .c-warning  .num {{ color: #d97706; }}
  .c-info     {{ border-top: 3px solid #3b82f6; }} .c-info     .num {{ color: #2563eb; }}

  /* ── Section heading ── */
  .section-heading {{
    display: flex; align-items: center; gap: 10px;
    font-size: 1rem; font-weight: 700; color: #292524;
    margin: 2.5rem 0 1rem;
    padding-bottom: .6rem;
    border-bottom: 1px solid #e7e5e4;
  }}
  .section-heading .dot {{
    width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0;
  }}

  /* ── Finding card ── */
  .finding {{
    background: #fff;
    border: 1px solid #e7e5e4;
    border-radius: 10px;
    margin-bottom: .85rem;
    overflow: hidden;
    page-break-inside: avoid;
  }}
  .finding-header {{
    padding: 1rem 1.25rem .85rem;
    border-left: 4px solid #e7e5e4;
  }}
  .finding-header.sev-critical {{ border-left-color: #ef4444; }}
  .finding-header.sev-warning  {{ border-left-color: #f59e0b; }}
  .finding-header.sev-info     {{ border-left-color: #3b82f6; }}

  .finding-tags {{
    display: flex; flex-wrap: wrap; gap: 6px;
    align-items: center; margin-bottom: 7px;
  }}
  .tag {{
    font-size: 11px; font-weight: 600; padding: 2px 8px;
    border-radius: 4px; border: 1px solid;
  }}
  .tag-critical {{ background: #fef2f2; color: #dc2626; border-color: #fecaca; }}
  .tag-warning  {{ background: #fffbeb; color: #d97706; border-color: #fde68a; }}
  .tag-info     {{ background: #eff6ff; color: #2563eb; border-color: #bfdbfe; }}
  .tag-type     {{ background: #f5f5f4; color: #57534e; border-color: #e7e5e4; font-family: 'JetBrains Mono', monospace; }}
  .tag-tool     {{ background: #f0fdf4; color: #059669; border-color: #a7f3d0; font-family: 'JetBrains Mono', monospace; }}
  .tag-cwe      {{ background: #fffbeb; color: #92400e; border-color: #fde68a; font-family: 'JetBrains Mono', monospace; }}
  .tag-history  {{ background: #f5f3ff; color: #7c3aed; border-color: #ddd6fe; }}

  .finding-title {{
    font-size: 15px; font-weight: 600; color: #1c1917; margin-bottom: 5px;
  }}
  .finding-loc {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 11.5px; color: #a8a29e;
  }}
  .finding-loc strong {{ color: #78716c; font-weight: 500; }}

  /* ── Finding body ── */
  .finding-body {{
    padding: 1rem 1.25rem 1.25rem;
    border-top: 1px solid #f5f5f4;
  }}
  .plain-english {{
    font-size: 13.5px; color: #44403c; margin-bottom: .75rem; line-height: 1.7;
  }}
  .why-matters {{
    font-size: 12.5px; color: #92400e;
    background: #fffbeb; border: 1px solid #fde68a;
    border-radius: 6px; padding: .5rem .75rem;
    margin-bottom: .75rem;
  }}
  .commits-box {{
    font-size: 12px; color: #6d28d9;
    background: #f5f3ff; border: 1px solid #ddd6fe;
    border-radius: 6px; padding: .5rem .75rem;
    margin-bottom: .75rem; font-family: 'JetBrains Mono', monospace;
  }}
  .sub-section {{ margin-bottom: .85rem; }}
  .sub-label {{
    font-size: 11px; font-weight: 700; letter-spacing: .07em;
    text-transform: uppercase; color: #a8a29e; margin-bottom: 6px;
  }}
  ul.findings-list, ol.fix-list {{
    padding-left: 1.4rem;
  }}
  ul.findings-list li, ol.fix-list li {{
    font-size: 13px; color: #44403c; margin-bottom: 4px; line-height: 1.6;
  }}
  ol.fix-list {{ counter-reset: fix-counter; list-style: none; padding-left: 0; }}
  ol.fix-list li {{
    display: flex; gap: 10px; align-items: flex-start;
  }}
  ol.fix-list li::before {{
    counter-increment: fix-counter;
    content: counter(fix-counter);
    flex-shrink: 0;
    width: 20px; height: 20px;
    background: #059669; color: #fff;
    font-size: 11px; font-weight: 700;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    margin-top: 2px;
  }}
  .snippet {{
    background: #1c1917; border-radius: 6px;
    padding: .85rem 1rem; overflow-x: auto; margin-top: .5rem;
  }}
  .snippet code {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px; color: #a3e635; white-space: pre;
  }}

  /* ── Empty state ── */
  .empty {{
    text-align: center; padding: 4rem 2rem;
    color: #a8a29e; font-size: 15px;
  }}

  /* ── Footer ── */
  .report-footer {{
    margin-top: 4rem; padding-top: 1.5rem;
    border-top: 1px solid #e7e5e4;
    display: flex; justify-content: space-between; align-items: center;
    font-size: 12px; color: #a8a29e;
  }}

  /* ── Print button ── */
  .print-btn {{
    position: fixed; bottom: 2rem; right: 2rem;
    display: flex; align-items: center; gap: 8px;
    background: #059669; color: #fff;
    font-family: 'DM Sans', sans-serif;
    font-size: 13px; font-weight: 600;
    padding: 10px 20px; border-radius: 999px;
    border: none; cursor: pointer;
    box-shadow: 0 4px 16px rgba(5,150,105,.35);
    transition: background .2s, transform .15s;
    z-index: 999;
  }}
  .print-btn:hover {{ background: #047857; transform: translateY(-1px); }}

  /* ── Print ── */
  @media print {{
    body {{ background: #fff; }}
    .page {{ padding: 1.5rem; }}
    .finding {{ break-inside: avoid; }}
    .print-btn {{ display: none; }}
  }}
</style>
</head>
<body>
<div class="page">

  <!-- Cover -->
  <div class="cover">
    <div class="cover-eyebrow">&#x1F6E1; Trustify Security Report</div>
    <h1 class="cover-title">Security Analysis Report</h1>
    <div class="cover-source">{scan_source}</div>
    <div class="cover-meta">
      <span class="meta-pill">&#x1F4C5; Generated {generated_at}</span>
      <span class="meta-pill">&#x1F527; {tools_used}</span>
      <span class="meta-pill">&#x1F4AC; {langs_used}</span>
      <span class="meta-pill">&#x1F194; {scan_id[:16]}&hellip;</span>
    </div>
  </div>

  <!-- Summary -->
  <div class="summary">
    <div class="summary-card c-total">
      <div class="num">{summary.get('total', 0)}</div>
      <div class="lbl">Total Findings</div>
    </div>
    <div class="summary-card c-critical">
      <div class="num">{summary.get('critical', 0)}</div>
      <div class="lbl">Critical</div>
    </div>
    <div class="summary-card c-warning">
      <div class="num">{summary.get('warning', 0)}</div>
      <div class="lbl">Warning</div>
    </div>
    <div class="summary-card c-info">
      <div class="num">{summary.get('info', 0)}</div>
      <div class="lbl">Info</div>
    </div>
  </div>

  <!-- Findings -->
  {all_cards if all_cards else '<div class="empty">&#x2705; No findings &mdash; clean scan!</div>'}

  <!-- Footer -->
  <div class="report-footer">
    <span>Trustify &mdash; AI-Powered Security Orchestration</span>
    <span>{generated_at}</span>
  </div>

</div>

<button class="print-btn" onclick="window.print()">
  <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 6 2 18 2 18 9"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect x="6" y="14" width="12" height="8"/></svg>
  Download PDF
</button>

</body>
</html>"""

        return Response(
            content=html,
            media_type="text/html",
            headers={
                "Content-Disposition": f'inline; filename="trustify-report-{scan_id[:8]}.html"'
            },
        )

    # ── PDF report ────────────────────────────────────────────────────────────
    if format == "pdf":
        from fpdf import FPDF

        SEV_COLORS = {
            "critical": (220, 38,  38),
            "warning":  (217, 119, 6),
            "info":     (37,  99,  235),
        }

        class ReportPDF(FPDF):
            def header(self):
                self.set_font("Helvetica", "B", 8)
                self.set_text_color(168, 162, 158)
                self.cell(0, 8, "TRUSTIFY SECURITY REPORT", align="R")
                self.ln(2)
                self.set_draw_color(231, 229, 228)
                self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
                self.ln(4)

            def footer(self):
                self.set_y(-14)
                self.set_font("Helvetica", "", 8)
                self.set_text_color(168, 162, 158)
                self.cell(0, 8, f"Page {self.page_no()} — Generated {generated_at}", align="C")

        pdf = ReportPDF(orientation="P", unit="mm", format="A4")
        pdf.set_auto_page_break(auto=True, margin=18)
        pdf.set_margins(18, 18, 18)
        pdf.add_page()

        W = pdf.w - pdf.l_margin - pdf.r_margin  # usable width

        # ── Cover ──────────────────────────────────────────────────────────
        pdf.set_font("Helvetica", "B", 22)
        pdf.set_text_color(28, 25, 23)
        pdf.multi_cell(W, 10, "Security Analysis Report", align="L")
        pdf.ln(2)

        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(120, 113, 108)
        pdf.multi_cell(W, 6, scan_source, align="L")
        pdf.ln(6)

        # meta pills row
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(87, 83, 78)
        pdf.cell(0, 5, f"Generated: {generated_at}   |   Tools: {tools_used}   |   Languages: {langs_used}", align="L")
        pdf.ln(8)

        # divider
        pdf.set_draw_color(231, 229, 228)
        pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
        pdf.ln(8)

        # ── Summary boxes ──────────────────────────────────────────────────
        box_w = (W - 9) / 4
        boxes = [
            (str(summary.get("total",    0)), "TOTAL",    (124, 58, 237)),
            (str(summary.get("critical", 0)), "CRITICAL", (220, 38,  38)),
            (str(summary.get("warning",  0)), "WARNING",  (217, 119,  6)),
            (str(summary.get("info",     0)), "INFO",     (37,  99, 235)),
        ]
        for num, lbl, color in boxes:
            x, y = pdf.get_x(), pdf.get_y()
            pdf.set_fill_color(255, 255, 255)
            pdf.set_draw_color(231, 229, 228)
            pdf.rect(x, y, box_w, 22, style="FD")
            # top accent line
            pdf.set_draw_color(*color)
            pdf.set_line_width(0.8)
            pdf.line(x, y, x + box_w, y)
            pdf.set_line_width(0.2)
            pdf.set_draw_color(231, 229, 228)
            pdf.set_xy(x, y + 3)
            pdf.set_font("Helvetica", "B", 16)
            pdf.set_text_color(*color)
            pdf.cell(box_w, 8, num, align="C")
            pdf.set_xy(x, y + 13)
            pdf.set_font("Helvetica", "", 7)
            pdf.set_text_color(168, 162, 158)
            pdf.cell(box_w, 5, lbl, align="C")
            pdf.set_xy(x + box_w + 3, y)

        pdf.ln(30)

        # ── Findings ───────────────────────────────────────────────────────
        sections = [
            ("Critical Findings", (220, 38,  38), critical_findings),
            ("Warning Findings",  (217, 119,  6), warning_findings),
            ("Informational",     (37,  99, 235), info_findings),
        ]

        for section_title, dot_color, section_findings in sections:
            if not section_findings:
                continue

            # section heading
            pdf.set_font("Helvetica", "B", 12)
            pdf.set_text_color(28, 25, 23)
            pdf.set_fill_color(*dot_color)
            pdf.circle(pdf.get_x() + 2, pdf.get_y() + 3, 2, style="F")
            pdf.set_x(pdf.l_margin + 7)
            pdf.cell(W - 7, 7, f"{section_title} ({len(section_findings)})", align="L")
            pdf.ln(2)
            pdf.set_draw_color(231, 229, 228)
            pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
            pdf.ln(5)

            for f in section_findings:
                sev = f.get("severity", "info")
                sev_rgb = SEV_COLORS.get(sev, (37, 99, 235))

                card_y = pdf.get_y()

                # left severity bar
                pdf.set_fill_color(*sev_rgb)
                pdf.rect(pdf.l_margin, card_y, 2, 999, style="F")  # will be clipped by content

                inner_x = pdf.l_margin + 5
                inner_w = W - 5
                pdf.set_x(inner_x)

                # severity + tool tags
                pdf.set_font("Helvetica", "B", 7)
                pdf.set_text_color(*sev_rgb)
                pdf.cell(18, 5, sev.upper(), border=0)
                pdf.set_text_color(5, 150, 105)
                pdf.cell(22, 5, f.get("tool", ""), border=0)
                if f.get("type"):
                    pdf.set_text_color(87, 83, 78)
                    pdf.cell(30, 5, f.get("type", ""), border=0)
                if f.get("cwe"):
                    pdf.set_text_color(146, 64, 14)
                    pdf.cell(20, 5, f.get("cwe", ""), border=0)
                pdf.ln(6)

                # title
                pdf.set_x(inner_x)
                pdf.set_font("Helvetica", "B", 10)
                pdf.set_text_color(28, 25, 23)
                pdf.multi_cell(inner_w, 6, f.get("title", "Finding"), align="L")

                # file location
                pdf.set_x(inner_x)
                pdf.set_font("Courier", "", 8)
                pdf.set_text_color(120, 113, 108)
                loc = f"{f.get('file_path','')}  :  line {f.get('line_start', 0)}"
                if f.get("impact_score") is not None:
                    loc += f"  |  Impact: {f['impact_score']}/10"
                pdf.multi_cell(inner_w, 5, loc, align="L")
                pdf.ln(2)

                # plain english / description
                text = f.get("plain_english") or f.get("description", "")
                if text:
                    pdf.set_x(inner_x)
                    pdf.set_font("Helvetica", "", 9)
                    pdf.set_text_color(68, 64, 60)
                    pdf.multi_cell(inner_w, 5, text, align="L")
                    pdf.ln(1)

                # why it matters
                if f.get("why_it_matters"):
                    pdf.set_x(inner_x)
                    pdf.set_font("Helvetica", "I", 8.5)
                    pdf.set_text_color(146, 64, 14)
                    pdf.multi_cell(inner_w, 5, f"Why it matters: {f['why_it_matters']}", align="L")
                    pdf.ln(1)

                # what it means
                for point in (f.get("what_it_means") or []):
                    pdf.set_x(inner_x + 3)
                    pdf.set_font("Helvetica", "", 8.5)
                    pdf.set_text_color(68, 64, 60)
                    pdf.multi_cell(inner_w - 3, 5, f"\u2022  {point}", align="L")

                # how to fix
                for i, step in enumerate((f.get("how_to_fix") or []), 1):
                    pdf.set_x(inner_x + 3)
                    pdf.set_font("Helvetica", "", 8.5)
                    pdf.set_text_color(5, 150, 105)
                    pdf.multi_cell(inner_w - 3, 5, f"{i}.  {step}", align="L")

                # draw the left bar to actual card height
                card_h = pdf.get_y() - card_y + 3
                pdf.set_fill_color(*sev_rgb)
                pdf.rect(pdf.l_margin, card_y, 2, card_h, style="F")

                pdf.ln(5)

        import io
        buf = io.BytesIO()
        pdf.output(buf)
        return Response(
            content=buf.getvalue(),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="trustify-report-{scan_id[:8]}.pdf"'
            },
        )

    raise HTTPException(400, "format must be 'json', 'html', or 'pdf'")
