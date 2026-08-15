import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

def create_pdf_report(scan):
    # Ensure export directory exists
    export_dir = os.path.join("tools_output", str(scan.id), "exports")
    os.makedirs(export_dir, exist_ok=True)
    pdf_path = os.path.join(export_dir, f"report_{scan.id}.pdf")
    
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    story.append(Paragraph(f"Corvus Security Scan Report", styles['Title']))
    story.append(Spacer(1, 12))
    
    # Details
    story.append(Paragraph(f"<b>Target:</b> {scan.target}", styles['Normal']))
    story.append(Paragraph(f"<b>Scan Mode:</b> {scan.mode.upper()}", styles['Normal']))
    story.append(Paragraph(f"<b>Date:</b> {scan.created_at.strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    story.append(Spacer(1, 24))
    
    # Findings Summary Section
    story.append(Paragraph("<b>Vulnerability Findings</b>", styles['Heading2']))
    story.append(Spacer(1, 12))
    
    if not scan.findings:
        story.append(Paragraph("No vulnerabilities were found during this scan.", styles['Normal']))
    else:
        # Table Header
        data = [["No", "Severity", "Type", "Endpoint", "CVSS"]]
        
        # Sort findings by severity
        severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}
        sorted_findings = sorted(scan.findings, key=lambda x: severity_order.get(str(x.get("severity")).upper(), 5))
        
        for idx, finding in enumerate(sorted_findings, 1):
            sev = str(finding.get("severity", "INFO")).upper()
            cvss = finding.get("cvss", "-")
            typ = finding.get("type", "Unknown")[:30] # trim long strings
            endpoint = finding.get("endpoint", "")[:40]
            data.append([str(idx), sev, typ, endpoint, str(cvss)])
            
        table = Table(data, colWidths=[30, 60, 150, 210, 40])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        story.append(table)
    
    doc.build(story)
    return pdf_path
