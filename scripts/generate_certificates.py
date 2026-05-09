"""Generate synthetic Texas exemption certificate PDFs for all 10 eval scenarios."""

from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.lib import colors

_OUTPUT_DIR = Path(__file__).parent.parent / "data" / "certificates"
_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _build_cert(
    filename: str,
    form_title: str,
    buyer_name: str,
    buyer_address: str,
    buyer_taxpayer_id: str,
    seller_name: str,
    description_of_property: str,
    reason_for_exemption: str,
    date: str,
    include_signature: bool = True,
) -> None:
    path = _OUTPUT_DIR / filename
    doc = SimpleDocTemplate(
        str(path),
        pagesize=letter,
        leftMargin=1 * inch,
        rightMargin=1 * inch,
        topMargin=1 * inch,
        bottomMargin=1 * inch,
    )
    styles = getSampleStyleSheet()
    elements = []

    title_style = styles["Heading1"]
    elements.append(Paragraph("STATE OF TEXAS", title_style))
    elements.append(Paragraph(form_title, title_style))
    elements.append(Spacer(1, 0.2 * inch))
    elements.append(Paragraph(
        "Form 01-339 | Texas Sales and Use Tax Exemption Certificate",
        styles["Normal"],
    ))
    elements.append(Spacer(1, 0.3 * inch))

    fields = [
        ["Buyer Legal Name:", buyer_name],
        ["Buyer Address:", buyer_address],
        ["Texas Taxpayer ID:", buyer_taxpayer_id],
        ["Seller / Vendor Name:", seller_name],
        ["Description of Property/Items:", description_of_property],
        ["Reason for Exemption:", reason_for_exemption],
        ["Certificate Date:", date],
    ]

    table = Table(fields, colWidths=[2.2 * inch, 4.0 * inch])
    table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.whitesmoke, colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 0.4 * inch))

    elements.append(Paragraph(
        "Certification: I, the purchaser named above, claim an exemption from payment of sales and use "
        "taxes for the purchase of taxable items described above or on the attached order or invoice from:",
        styles["Normal"],
    ))
    elements.append(Spacer(1, 0.15 * inch))
    elements.append(Paragraph(f"Seller: {seller_name}", styles["Normal"]))
    elements.append(Spacer(1, 0.3 * inch))

    if include_signature:
        sig_data = [
            ["Authorized Signature:", "________________________________"],
            ["Printed Name:", "Authorized Representative"],
            ["Title:", "Tax Compliance Officer"],
        ]
        sig_table = Table(sig_data, colWidths=[2.2 * inch, 4.0 * inch])
        sig_table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        elements.append(sig_table)
    else:
        elements.append(Paragraph(
            "Authorized Signature: [SIGNATURE FIELD LEFT BLANK]",
            styles["Normal"],
        ))
        elements.append(Paragraph(
            "NOTE: This certificate is submitted without an authorized signature.",
            styles["Normal"],
        ))

    elements.append(Spacer(1, 0.4 * inch))
    elements.append(Paragraph(
        "This certificate is issued for the purpose of claiming a sales tax exemption. "
        "Fraudulent use of this certificate may result in penalties under Texas Tax Code Section 151.705.",
        styles["Italic"],
    ))

    doc.build(elements)
    print(f"Generated: {path}")


def generate_all() -> None:
    seller = "Vertex Inc. (Seller Placeholder)"

    _build_cert(
        filename="C_001_resale_aligned.pdf",
        form_title="Texas Sales and Use Tax Resale Certificate",
        buyer_name="Acme Office Supplies LLC",
        buyer_address="1234 Commerce Blvd, Austin, TX 78701",
        buyer_taxpayer_id="TX-12345678",
        seller_name=seller,
        description_of_property="Office products including pens, paper, binders, desk accessories, and small electronics purchased for resale to commercial customers",
        reason_for_exemption="Resale — items purchased will be resold to end customers in the ordinary course of our business as a registered retailer",
        date="2026-04-15",
    )

    _build_cert(
        filename="C_002_mfg_consulting.pdf",
        form_title="Texas Sales and Use Tax Manufacturing Exemption Certificate",
        buyer_name="Lighthouse Software Consulting",
        buyer_address="5678 Tech Park Dr, Dallas, TX 75201",
        buyer_taxpayer_id="TX-23456789",
        seller_name=seller,
        description_of_property="Computer equipment, servers, and technology hardware claimed as exempt manufacturing equipment",
        reason_for_exemption="Manufacturing exemption — equipment used in the manufacturing and production of software solutions",
        date="2026-04-10",
    )

    _build_cert(
        filename="C_003_agricultural_aligned.pdf",
        form_title="Texas Agricultural and Timber Exemption Certificate",
        buyer_name="Hill Country Farm Equipment",
        buyer_address="789 Ranch Road 12, Kerrville, TX 78028",
        buyer_taxpayer_id="TX-34567890",
        seller_name=seller,
        description_of_property="Tractors, agricultural implements, irrigation equipment, and farm machinery parts used directly in agricultural production",
        reason_for_exemption="Agricultural exemption — equipment used exclusively in the production of agricultural products for sale per Texas Tax Code Section 151.316",
        date="2026-04-12",
    )

    _build_cert(
        filename="C_004_resale_restaurant.pdf",
        form_title="Texas Sales and Use Tax Resale Certificate",
        buyer_name="Brisket Barons Restaurants",
        buyer_address="321 BBQ Way, San Antonio, TX 78205",
        buyer_taxpayer_id="TX-45678901",
        seller_name=seller,
        description_of_property="Food items, kitchen supplies, and restaurant equipment claimed as exempt purchases for resale",
        reason_for_exemption="Resale — food and supplies purchased for resale to restaurant customers",
        date="2026-04-08",
    )

    _build_cert(
        filename="C_005_mfg_aligned.pdf",
        form_title="Texas Sales and Use Tax Manufacturing Exemption Certificate",
        buyer_name="Steel & Stone Industrial Mfg",
        buyer_address="456 Industrial Pkwy, Houston, TX 77001",
        buyer_taxpayer_id="TX-56789012",
        seller_name=seller,
        description_of_property="Raw steel, machine parts, industrial chemicals, lubricants, and manufacturing equipment used directly in the production of structural steel components",
        reason_for_exemption="Manufacturing exemption — raw materials and equipment incorporated into manufactured goods for sale per Texas Tax Code Section 151.318",
        date="2026-04-20",
    )

    _build_cert(
        filename="C_006_resale_mixed.pdf",
        form_title="Texas Sales and Use Tax Resale Certificate",
        buyer_name="Acme Office Supplies LLC",
        buyer_address="1234 Commerce Blvd, Austin, TX 78701",
        buyer_taxpayer_id="TX-12345678",
        seller_name=seller,
        description_of_property="Office products and furniture including items for resale and items for business use",
        reason_for_exemption="Resale — office supplies and products purchased for resale to commercial customers",
        date="2026-03-01",
    )

    _build_cert(
        filename="C_007_mfg_no_signature.pdf",
        form_title="Texas Sales and Use Tax Manufacturing Exemption Certificate",
        buyer_name="Steel & Stone Industrial Mfg",
        buyer_address="456 Industrial Pkwy, Houston, TX 77001",
        buyer_taxpayer_id="TX-56789012",
        seller_name=seller,
        description_of_property="Raw steel, machine parts, and manufacturing equipment used in production",
        reason_for_exemption="Manufacturing exemption — materials and equipment used in production of structural steel components",
        date="2026-04-18",
        include_signature=False,
    )

    _build_cert(
        filename="C_008_agricultural_retailer.pdf",
        form_title="Texas Agricultural and Timber Exemption Certificate",
        buyer_name="Acme Office Supplies LLC",
        buyer_address="1234 Commerce Blvd, Austin, TX 78701",
        buyer_taxpayer_id="TX-12345678",
        seller_name=seller,
        description_of_property="Office supplies and products claimed as agricultural production supplies",
        reason_for_exemption="Agricultural exemption — supplies used in agricultural operations",
        date="2026-04-05",
    )

    _build_cert(
        filename="C_009_resale_new_customer.pdf",
        form_title="Texas Sales and Use Tax Resale Certificate",
        buyer_name="New Customer Inc",
        buyer_address="100 Main Street, Houston, TX 77002",
        buyer_taxpayer_id="TX-90123456",
        seller_name=seller,
        description_of_property="General merchandise and consumer goods for resale",
        reason_for_exemption="Resale — goods purchased for resale in the ordinary course of business",
        date="2026-05-01",
    )

    _build_cert(
        filename="C_010_resale_edge.pdf",
        form_title="Texas Sales and Use Tax Resale Certificate",
        buyer_name="Acme Office Supplies LLC",
        buyer_address="1234 Commerce Blvd, Austin, TX 78701",
        buyer_taxpayer_id="TX-12345678",
        seller_name=seller,
        description_of_property="Office supplies, paper products, and office accessories for resale to commercial customers",
        reason_for_exemption="Resale — items purchased will be resold to end customers in the ordinary course of our business",
        date="2026-04-25",
    )

    print("\nAll 10 certificates generated successfully.")


if __name__ == "__main__":
    generate_all()
