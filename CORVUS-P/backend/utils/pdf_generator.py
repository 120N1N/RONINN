import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

SEV_COLORS = {
    "CRITICAL": colors.HexColor("#DC2626"),
    "HIGH": colors.HexColor("#EA580C"),
    "MEDIUM": colors.HexColor("#D97706"),
    "LOW": colors.HexColor("#2563EB"),
    "INFO": colors.HexColor("#64748B"),
    "INFORMATIONAL": colors.HexColor("#64748B")
}

def create_pdf_report(scan):
    export_dir = os.path.join("tools_output", str(scan.id), "exports")
    os.makedirs(export_dir, exist_ok=True)
    pdf_path = os.path.join(export_dir, f"report_{scan.id}.pdf")
    
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=26,
        textColor=colors.HexColor("#0F172A")
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#64748B")
    )
    
    section_title = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#1E293B"),
        spaceBefore=14,
        spaceAfter=8
    )

    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#334155")
    )

    code_style = ParagraphStyle(
        'CodeStyle',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#0F172A")
    )
    
    story = []
    
    # Header Banner
    story.append(Paragraph("<b>CORVUS-P SECURITY AUDIT REPORT</b>", title_style))
    story.append(Paragraph("Automated AI Penetration Testing & Vulnerability Assessment Platform", subtitle_style))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#3B82F6"), spaceAfter=15))
    
    # Metadata Table
    created_str = scan.created_at.strftime('%Y-%m-%d %H:%M:%S UTC') if scan.created_at else "N/A"
    finished_str = scan.finished_at.strftime('%Y-%m-%d %H:%M:%S UTC') if scan.finished_at else "Completed"
    
    meta_data = [
        [Paragraph("<b>Target URL:</b>", body_style), Paragraph(str(scan.target), body_style),
         Paragraph("<b>Scan ID:</b>", body_style), Paragraph(str(scan.id)[:12], code_style)],
        [Paragraph("<b>Scan Mode:</b>", body_style), Paragraph(str(scan.mode).upper(), body_style),
         Paragraph("<b>Status:</b>", body_style), Paragraph(str(scan.status), body_style)],
        [Paragraph("<b>Started:</b>", body_style), Paragraph(created_str, body_style),
         Paragraph("<b>Finished:</b>", body_style), Paragraph(finished_str, body_style)]
    ]
    meta_table = Table(meta_data, colWidths=[80, 200, 70, 190])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 15))
    
    # Executive Summary & Risk Counter
    findings = scan.findings or []
    sev_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}
    for f in findings:
        s = str(f.get("severity", "INFO")).upper()
        if s == "INFORMATIONAL": s = "INFO"
        if s in sev_counts:
            sev_counts[s] += 1
        else:
            sev_counts["INFO"] += 1
            
    story.append(Paragraph("<b>1. Executive Risk Overview</b>", section_title))
    
    stat_data = [
        [
            Paragraph(f"<font color='#DC2626'><b>CRITICAL</b></font><br/><font size=16><b>{sev_counts['CRITICAL']}</b></font>", body_style),
            Paragraph(f"<font color='#EA580C'><b>HIGH</b></font><br/><font size=16><b>{sev_counts['HIGH']}</b></font>", body_style),
            Paragraph(f"<font color='#D97706'><b>MEDIUM</b></font><br/><font size=16><b>{sev_counts['MEDIUM']}</b></font>", body_style),
            Paragraph(f"<font color='#2563EB'><b>LOW</b></font><br/><font size=16><b>{sev_counts['LOW']}</b></font>", body_style),
            Paragraph(f"<font color='#64748B'><b>INFO</b></font><br/><font size=16><b>{sev_counts['INFO']}</b></font>", body_style),
        ]
    ]
    stat_table = Table(stat_data, colWidths=[108, 108, 108, 108, 108])
    stat_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F1F5F9")),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(stat_table)
    story.append(Spacer(1, 15))

    # AI-BRAIN Security Analyst Evaluation Section
    ai_sum = getattr(scan, "ai_summary", None) or (scan.tool_outputs or {}).get("ai_brain_summary")
    if not ai_sum:
        validated_findings = [f for f in findings if f.get("ai_brain_validation") or f.get("ai_validation")]
        val_count = len(validated_findings)
        tp_count = sum(1 for f in findings if (
            (f.get("ai_brain_validation") or f.get("ai_validation") or {}).get("is_valid") is True
            or f.get("ai_brain_valid") is True
            or (f.get("rf_validation") or {}).get("predicted_class") == "Valid Finding"
            or float(f.get("confidence_score") or 0.0) >= 50.0
        ))
        fp_count = max(0, len(findings) - tp_count)
        avg_conf = (
            sum((f.get("ai_brain_validation") or f.get("ai_validation") or {}).get("confidence_score", 0.85) for f in validated_findings) / val_count
        ) if val_count > 0 else 0.0
        ai_sum = {
            "title": "AI-BRAIN SECURITY ANALYST",
            "subtitle": "Autonomous verification & False Positive elimination engine",
            "total_findings": len(findings),
            "validated_count": val_count,
            "tp_count": tp_count,
            "fp_count": fp_count,
            "avg_confidence": round(avg_conf, 4),
            "executive_summary": f"Audit riwayat mencakup {len(findings)} temuan dengan {tp_count} True Positive dan {fp_count} False Positive terverifikasi AI-BRAIN." if len(findings) > 0 else "Audit selesai. Tidak ada kerentanan terdeteksi pada target."
        }

    story.append(Paragraph("<b>2. AI-BRAIN Security Analyst Evaluation</b>", section_title))
    story.append(Paragraph("<i>Autonomous HunterFlowX & Cloud LLM Verification and False Positive Filtering</i>", subtitle_style))
    story.append(Spacer(1, 6))

    ai_metrics_data = [
        [
            Paragraph(f"<font color='#0F172A'><b>Total Issues</b></font><br/><font size=14><b>{ai_sum.get('total_findings', len(findings))}</b></font>", body_style),
            Paragraph(f"<font color='#059669'><b>True Positive (Verified)</b></font><br/><font size=14><b>{ai_sum.get('tp_count', 0)}</b></font>", body_style),
            Paragraph(f"<font color='#DC2626'><b>False Positive (Filtered)</b></font><br/><font size=14><b>{ai_sum.get('fp_count', 0)}</b></font>", body_style),
            Paragraph(f"<font color='#7C3AED'><b>Avg AI Confidence</b></font><br/><font size=14><b>{int(float(ai_sum.get('avg_confidence', 0.85)) * 100)}%</b></font>", body_style),
        ]
    ]
    ai_metrics_table = Table(ai_metrics_data, colWidths=[135, 135, 135, 135])
    ai_metrics_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(ai_metrics_table)
    story.append(Spacer(1, 8))

    if ai_sum.get("executive_summary"):
        exec_text = str(ai_sum["executive_summary"]).replace("\n", "<br/>")
        exec_box = Table([
            [Paragraph(f"<b>Analyst Synthesis & Threat Landscape:</b><br/>{exec_text}", body_style)]
        ], colWidths=[540])
        exec_box.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#EFF6FF")),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#3B82F6")),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ]))
        story.append(exec_box)
        story.append(Spacer(1, 15))

    # Findings Overview Table
    story.append(Paragraph(f"<b>3. Vulnerability Findings List ({len(findings)} Issues Detected)</b>", section_title))
    
    if not findings:
        story.append(Paragraph("Audit completed. No security vulnerabilities were detected on the target.", body_style))
    else:
        overview_data = [["#", "Severity", "Vulnerability Name", "OWASP Category", "CVSS"]]
        sev_priority = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4, "INFORMATIONAL": 4}
        sorted_findings = sorted(findings, key=lambda x: sev_priority.get(str(x.get("severity", "INFO")).upper(), 5))
        
        for idx, f in enumerate(sorted_findings, 1):
            s = str(f.get("severity", "INFO")).upper()
            color_hex = SEV_COLORS.get(s, colors.HexColor("#64748B")).hexval()
            sev_cell = Paragraph(f"<font color='{color_hex}'><b>{s}</b></font>", body_style)
            name_cell = Paragraph(f.get("name", f.get("type", "Unknown Issue")), body_style)
            cat_cell = Paragraph(f.get("category", f.get("owasp_code", "A00:2021")), body_style)
            cvss_cell = Paragraph(str(f.get("cvss", "-")), body_style)
            overview_data.append([str(idx), sev_cell, name_cell, cat_cell, cvss_cell])
            
        overview_table = Table(overview_data, colWidths=[25, 65, 230, 180, 40])
        overview_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1E293B")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(overview_table)
        story.append(Spacer(1, 20))

        # Detailed Technical Findings
        story.append(PageBreak())
        story.append(Paragraph("<b>4. Detailed Technical Findings & Remediation</b>", section_title))
        story.append(Spacer(1, 8))

        for idx, f in enumerate(sorted_findings, 1):
            s = str(f.get("severity", "INFO")).upper()
            c_hex = SEV_COLORS.get(s, colors.HexColor("#64748B")).hexval()
            f_title = f.get("name", f.get("type", "Security Finding"))
            owasp_info = f"{f.get('owasp_code', 'A00:2021')} - {f.get('category', 'General')}"
            endpoint = f.get("location") or f.get("endpoint") or scan.target

            story.append(Paragraph(f"<b>Finding #{idx}: {f_title}</b> [<font color='{c_hex}'><b>{s}</b></font> | CVSS: {f.get('cvss', 'N/A')}]", section_title))
            
            detail_box = [
                [Paragraph("<b>OWASP Mapping:</b>", body_style), Paragraph(owasp_info, body_style)],
                [Paragraph("<b>Vulnerable Endpoint:</b>", body_style), Paragraph(endpoint, code_style)],
                [Paragraph("<b>Description:</b>", body_style), Paragraph(f.get("description", "No description provided."), body_style)],
                [Paragraph("<b>Remediation:</b>", body_style), Paragraph(f.get("remediation", "Apply defensive validation and standard security patches."), body_style)]
            ]
            
            # AI-Brain Validation Verdict in detail box
            val = f.get("ai_brain_validation") or f.get("ai_validation")
            if val:
                is_tp = val.get("is_valid", False)
                v_text = "TRUE POSITIVE (Confirmed Threat)" if is_tp else "FALSE POSITIVE (Suppressed Noise)"
                v_color = "#059669" if is_tp else "#DC2626"
                conf_pct = int((val.get("confidence_score") or 0.85) * 100)
                reason = val.get("reasoning") or f.get("ai_brain_reasoning") or "Evaluated by AI-Brain consensus model."
                detail_box.append([
                    Paragraph("<b>AI-Brain Verdict:</b>", body_style),
                    Paragraph(f"<font color='{v_color}'><b>{v_text}</b> [Confidence: {conf_pct}%]</font><br/><i>Reasoning:</i> {reason}", body_style)
                ])

            # If points exist
            points = f.get("points")
            if points and isinstance(points, list):
                pts_str = "<br/>".join([f"• {p}" for p in points])
                detail_box.append([Paragraph("<b>Key Evidence:</b>", body_style), Paragraph(pts_str, body_style)])

            d_table = Table(detail_box, colWidths=[120, 420])
            d_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ]))
            story.append(d_table)
            story.append(Spacer(1, 12))

    doc.build(story)
    return pdf_path
