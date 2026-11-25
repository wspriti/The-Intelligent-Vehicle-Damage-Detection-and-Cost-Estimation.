from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

# -------------------------------
# 🎨 Severity Color Logic
# -------------------------------
def get_severity_color(severity):
    if severity == "Severe":
        return colors.red
    elif severity == "Moderate":
        return colors.orange
    elif severity == "Minor":
        return colors.green
    return colors.black

# -------------------------------
# 📄 MAIN REPORT FUNCTION
# -------------------------------
def generate_report(results_data, path, user_info=None, engine_damage=None, total_cost=0):

    doc = SimpleDocTemplate(path, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    # -------------------------------
    # 🧾 HEADER
    # -------------------------------
    elements.append(Paragraph("<b>VEHICLE DAMAGE REPORT</b>", styles["Title"]))
    elements.append(Paragraph("AI-Based Inspection System", styles["Normal"]))
    elements.append(Spacer(1, 15))

    # -------------------------------
    # 👤 USER INFO
    # -------------------------------
    if user_info:
        elements.append(Paragraph("<b>User Details</b>", styles["Heading2"]))
        elements.append(Paragraph(f"Name: {user_info.get('name')}", styles["Normal"]))
        elements.append(Paragraph(f"Email: {user_info.get('email')}", styles["Normal"]))
        elements.append(Paragraph(f"Phone: {user_info.get('contact_number')}", styles["Normal"]))
        elements.append(Spacer(1, 10))

        elements.append(Paragraph("<b>Vehicle Details</b>", styles["Heading2"]))
        elements.append(Paragraph(f"Vehicle ID: {user_info.get('vehicle_id')}", styles["Normal"]))
        elements.append(Paragraph(f"Brand: {user_info.get('car_brand')}", styles["Normal"]))
        elements.append(Paragraph(f"Model: {user_info.get('model')}", styles["Normal"]))
        elements.append(Spacer(1, 15))

    # -------------------------------
    # 📊 SUMMARY BOX
    # -------------------------------
    if engine_damage:
        summary_data = [
            ["Total Cost", f"₹{total_cost}"],
            ["Engine Risk", engine_damage.get("status")],
            ["Engine Cost", f"₹{engine_damage.get('cost')}"]
        ]

        summary_table = Table(summary_data, colWidths=[180, 180])
        summary_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.lightgrey),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold")
        ]))

        elements.append(Paragraph("<b>Summary</b>", styles["Heading2"]))
        elements.append(summary_table)
        elements.append(Spacer(1, 20))

    # -------------------------------
    # 🔍 DAMAGE TABLE
    # -------------------------------
    table_data = [["Side", "Part", "Damage", "Severity", "Cost"]]

    for side, data in results_data.items():
        severity = data.get("severity", "-")

        for d in data.get("details", []):
            table_data.append([
                side.capitalize(),
                d.get("part"),
                d.get("label"),
                severity,
                f"₹{d.get('cost')}"
            ])

    table = Table(table_data, repeatRows=1)

    # Base styling
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ]))

    # Apply severity colors row-wise
    for i in range(1, len(table_data)):
        severity = table_data[i][3]
        color = get_severity_color(severity)

        table.setStyle([
            ("TEXTCOLOR", (3, i), (3, i), color)
        ])

    elements.append(Paragraph("<b>Damage Details</b>", styles["Heading2"]))
    elements.append(table)
    elements.append(Spacer(1, 20))

    # -------------------------------
    # 📌 SIDE-WISE SUMMARY
    # -------------------------------
    side_data = [["Side", "Total Cost"]]

    for side, data in results_data.items():
        side_data.append([side.capitalize(), f"₹{data['cost']}"])

    side_table = Table(side_data)
    side_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]))

    elements.append(Paragraph("<b>Side-wise Damage Summary</b>", styles["Heading2"]))
    elements.append(side_table)
    elements.append(Spacer(1, 20))

    # -------------------------------
    # 🚨 ENGINE DAMAGE
    # -------------------------------
    if engine_damage:
        elements.append(Paragraph("<b>Engine Damage Assessment</b>", styles["Heading2"]))
        elements.append(Paragraph(f"Risk Level: {engine_damage.get('status')}", styles["Normal"]))
        elements.append(Paragraph(f"Estimated Cost: ₹{engine_damage.get('cost')}", styles["Normal"]))
        elements.append(Spacer(1, 20))

    # -------------------------------
    # 💰 FINAL COST
    # -------------------------------
    elements.append(Paragraph(
        f"<b><font size=16>Total Estimated Cost: ₹{total_cost}</font></b>",
        styles["Normal"]
    ))

    # -------------------------------
    # 📎 FOOTER
    # -------------------------------
    elements.append(Spacer(1, 30))
    elements.append(Paragraph(
        "Generated by AI Vehicle Inspection System",
        styles["Italic"]
    ))

    # Build PDF
    doc.build(elements)