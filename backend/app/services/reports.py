import io
import datetime
from typing import List, Optional
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from app.models.models import Survey, Parcel, CadastralFeature, BoundaryChange

def generate_survey_pdf_report(
    survey: Survey,
    parcels: List[Parcel],
    features: List[CadastralFeature],
    discrepancies: List[BoundaryChange]
) -> bytes:
    """
    Generates an official Government of India styled Cadastral Survey Dossier PDF
    using ReportLab.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    
    # Custom styles
    header_title_style = ParagraphStyle(
        "GovHeaderTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0f172a"),
        alignment=1 # Center
    )
    
    header_sub_style = ParagraphStyle(
        "GovHeaderSub",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#475569"),
        alignment=1 # Center
    )

    section_heading = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#1e3a8a"),
        spaceBefore=12,
        spaceAfter=6
    )

    body_text = ParagraphStyle(
        "ReportBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#334155")
    )

    badge_style = ParagraphStyle(
        "BadgeText",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        textColor=colors.HexColor("#065f46")
    )

    elements = []

    # 1. Header Banner
    elements.append(Paragraph("GOVERNMENT OF INDIA • MINISTRY OF RURAL DEVELOPMENT", header_sub_style))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph("BHOOMI-AI CADASTRAL SURVEY AUDIT DOSSIER", header_title_style))
    elements.append(Paragraph("From Drone Imagery to Verified Digital Land Maps • SIH26012", header_sub_style))
    elements.append(Spacer(1, 8))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#1e3a8a"), spaceAfter=12))

    # 2. Survey Administration Metadata
    elements.append(Paragraph("1. ADMINISTRATIVE SURVEY RECORD", section_heading))
    
    meta_data = [
        [
            Paragraph("<b>Survey Name:</b>", body_text), Paragraph(survey.name, body_text),
            Paragraph("<b>Survey ID:</b>", body_text), Paragraph(f"SRV-{survey.id:04d}", body_text)
        ],
        [
            Paragraph("<b>Village:</b>", body_text), Paragraph(survey.village, body_text),
            Paragraph("<b>Mandal / Tehsil:</b>", body_text), Paragraph(survey.mandal, body_text)
        ],
        [
            Paragraph("<b>District:</b>", body_text), Paragraph(survey.district, body_text),
            Paragraph("<b>State:</b>", body_text), Paragraph(survey.state, body_text)
        ],
        [
            Paragraph("<b>Survey Date:</b>", body_text), Paragraph(survey.survey_date, body_text),
            Paragraph("<b>Survey Officer:</b>", body_text), Paragraph(survey.survey_officer, body_text)
        ],
        [
            Paragraph("<b>Processing Status:</b>", body_text), Paragraph(survey.status.upper(), badge_style),
            Paragraph("<b>Generated On:</b>", body_text), Paragraph(datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"), body_text)
        ]
    ]
    meta_table = Table(meta_data, colWidths=[110, 150, 110, 150])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 12))

    # 3. Key Executive Metrics Summary
    elements.append(Paragraph("2. KEY SURVEY & FEATURE METRICS", section_heading))
    total_area_acres = sum(p.area_acres for p in parcels)
    total_area_sqm = sum(p.area for p in parcels)
    verified_parcels = sum(1 for p in parcels if p.status == "verified")
    pending_parcels = sum(1 for p in parcels if p.status in ["pending_review", "flagged_discrepancy"])
    building_count = sum(1 for f in features if f.feature_type == "building")
    road_count = sum(1 for f in features if f.feature_type in ["road", "pathway"])
    water_count = sum(1 for f in features if f.feature_type == "water_body")

    kpi_data = [
        ["Total Drone Mapped Area", f"{total_area_acres:.2f} Acres ({total_area_sqm:,.0f} m²)"],
        ["Total AI Parcels Segmented", str(len(parcels))],
        ["Officer Verified Parcels", f"{verified_parcels} ({round((verified_parcels/max(len(parcels),1))*100,1)}%)"],
        ["Parcels Requiring Adjudication", str(pending_parcels)],
        ["Potential Discrepancies Flagged", str(len(discrepancies))],
        ["Detected Buildings / Habitation", str(building_count)],
        ["Transport Lines / Village Roads", str(road_count)],
        ["Surface Water Bodies / Canals", str(water_count)]
    ]
    kpi_table = Table(kpi_data, colWidths=[260, 260])
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor("#f1f5f9")),
        ('BACKGROUND', (1, 0), (1, -1), colors.white),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(kpi_table)
    elements.append(Spacer(1, 12))

    # 4. Cadastral Boundary Discrepancies Table
    elements.append(Paragraph("3. CADASTRAL SCREENING & BOUNDARY DISCREPANCIES", section_heading))
    elements.append(Paragraph(
        "<i>Disclaimer: AI discrepancy screening identifies spatial variances between legacy revenue maps and high-resolution drone orthomosaics for officer verification. It does not constitute a final legal title determination.</i>",
        body_text
    ))
    elements.append(Spacer(1, 6))

    disc_rows = [
        ["Parcel ID", "Legacy Area", "Drone Area", "Area Delta", "Max Shift (m)", "Screening Status"]
    ]
    for d in discrepancies[:10]:
        p = next((x for x in parcels if x.id == d.parcel_id), None)
        p_id = p.parcel_id if p else f"P-{d.parcel_id}"
        disc_rows.append([
            p_id,
            f"{d.difference_acres + (p.area_acres if p else 1.0):.2f} ac",
            f"{(p.area_acres if p else 1.0):.2f} ac",
            f"{d.difference_percentage:.1f}%",
            f"{d.difference_distance:.1f} m",
            d.status.replace("_", " ").upper()
        ])

    if len(disc_rows) == 1:
        disc_rows.append(["None", "-", "-", "-", "-", "ALL CONFORMING"])

    disc_table = Table(disc_rows, colWidths=[80, 85, 85, 75, 85, 110])
    disc_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1e3a8a")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(disc_table)
    elements.append(Spacer(1, 14))

    # 5. Parcel Inventory Table
    elements.append(Paragraph("4. PARCEL INVENTORY & VERIFICATION AUDIT", section_heading))
    p_rows = [
        ["Parcel ID", "Area (Acres)", "Area (m²)", "Land Use", "AI Conf.", "Status"]
    ]
    for p in parcels[:15]:
        p_rows.append([
            p.parcel_id,
            f"{p.area_acres:.3f}",
            f"{p.area:,.1f}",
            p.land_use,
            f"{round(p.confidence * 100)}%",
            p.status.upper()
        ])

    p_table = Table(p_rows, colWidths=[90, 85, 85, 100, 70, 90])
    p_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#334155")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    elements.append(p_table)
    elements.append(Spacer(1, 18))

    # 6. Official Signatures
    elements.append(Paragraph("5. STATUTORY VERIFICATION & ENDORSEMENT", section_heading))
    sig_data = [
        [
            Paragraph("<b>Surveying Official:</b><br/><br/><br/>_______________________<br/>Field Survey Inspector", body_text),
            Paragraph("<b>Revenue Department:</b><br/><br/><br/>_______________________<br/>Tahsildar / Mandal Revenue Officer", body_text),
            Paragraph("<b>Digital Seal:</b><br/><br/><br/>[ BHOOMI-AI VERIFIED ]<br/>Survey Directorate", body_text)
        ]
    ]
    sig_table = Table(sig_data, colWidths=[170, 170, 180])
    sig_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(sig_table)

    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
