import json
import re
import statistics
from collections import Counter
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.legends import Legend
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Enhanced report generator with charts, executive summary, and structured formatting"""

    def __init__(self):
        # Report configuration
        self.page_size = letter
        self.margin = 0.75 * inch

        # Color scheme
        self.colors = {
            "primary": colors.HexColor("#2563eb"),  # Blue
            "secondary": colors.HexColor("#7c3aed"),  # Purple
            "success": colors.HexColor("#059669"),  # Green
            "warning": colors.HexColor("#d97706"),  # Orange
            "danger": colors.HexColor("#dc2626"),  # Red
            "neutral": colors.HexColor("#6b7280"),  # Gray
            "light_bg": colors.HexColor("#f8fafc"),  # Light gray
            "header_bg": colors.HexColor("#e2e8f0"),  # Header gray
        }

        # Risk color mapping
        self.risk_colors = {
            "high": self.colors["danger"],
            "medium": self.colors["warning"],
            "low": self.colors["success"],
        }

        # Initialize custom styles
        self.styles = self._create_custom_styles()

    def _create_custom_styles(self) -> Dict[str, ParagraphStyle]:
        """Create custom paragraph styles for the report"""
        base_styles = getSampleStyleSheet()

        custom_styles = {
            "ReportTitle": ParagraphStyle(
                "ReportTitle",
                parent=base_styles["Title"],
                fontSize=22,
                spaceAfter=30,
                textColor=self.colors["primary"],
                alignment=1,  # Center alignment
            ),
            "SectionHeader": ParagraphStyle(
                "SectionHeader",
                parent=base_styles["Heading1"],
                fontSize=18,  # Increased font size
                spaceBefore=20,
                spaceAfter=12,
                textColor=self.colors["primary"],
                borderWidth=1,
                borderColor=self.colors["primary"],
                borderPadding=8,
                backColor=colors.HexColor("#f1f5f9"),
            ),
            "SubHeader": ParagraphStyle(
                "SubHeader",
                parent=base_styles["Heading2"],
                fontSize=14,
                spaceBefore=15,
                spaceAfter=8,
                textColor=self.colors["secondary"],
            ),
            "ExecutiveSummary": ParagraphStyle(
                "ExecutiveSummary",
                parent=base_styles["Normal"],
                fontSize=11,
                leading=16,
                spaceBefore=10,
                spaceAfter=10,
                backColor=self.colors["light_bg"],
                borderWidth=1,
                borderColor=self.colors["neutral"],
                borderPadding=12,
                leftIndent=10,
                rightIndent=10,
            ),
            "ClauseContent": ParagraphStyle(
                "ClauseContent",
                parent=base_styles["Normal"],
                fontSize=10,
                leading=14,
                leftIndent=15,
                spaceBefore=5,
                spaceAfter=8,
            ),
            "RiskBadge": ParagraphStyle(
                "RiskBadge",
                parent=base_styles["Normal"],
                fontSize=12,
                alignment=1,
                textColor=colors.white,
            ),
            "RiskMarker": ParagraphStyle(
                "RiskMarker",
                parent=base_styles["Normal"],
                fontSize=14,
                textColor=colors.red,
                alignment=1,
                spaceBefore=10,
                spaceAfter=10,
            ),
        }

        return custom_styles

    def _bold_keywords(self, text: str) -> str:
        keywords = ["Termination", "Payment", "Confidentiality"]
        for keyword in keywords:
            pattern = rf"\b({re.escape(keyword)})\b"
            text = re.sub(pattern, r"<b>\1</b>", text, flags=re.IGNORECASE)
        return text

    def export_as_json(self, analysis: Dict[str, Any], original_filename: str) -> str:
        """Export the analysis result as JSON with enhanced metadata"""
        try:
            # Add export metadata
            export_data = {
                "export_info": {
                    "generated_at": datetime.now().isoformat(),
                    "original_filename": original_filename,
                    "export_format": "json",
                    "version": "1.0",
                },
                "analysis": analysis,
                "statistics": self._generate_statistics(analysis),
            }

            json_content = json.dumps(
                export_data, indent=2, default=str, ensure_ascii=False
            )

            file_path = (
                f"exports/{self._sanitize_filename(original_filename)}_analysis.json"
            )
            with open(file_path, "w") as f:
                f.write(json_content)

            return file_path
        except Exception as e:
            logger.error(f"JSON export failed: {e}")
            raise

    def export_as_pdf(self, analysis: Dict[str, Any], original_filename: str) -> str:
        """Export the analysis result as a comprehensive PDF report"""
        try:
            file_path = (
                f"exports/{self._sanitize_filename(original_filename)}_report.pdf"
            )
            doc = SimpleDocTemplate(
                file_path,
                pagesize=self.page_size,
                rightMargin=self.margin,
                leftMargin=self.margin,
                topMargin=self.margin,
                bottomMargin=self.margin,
            )

            story = []

            # Build report sections
            story.extend(self._build_header_section(analysis, original_filename))
            story.extend(self._build_executive_summary(analysis))
            story.extend(self._build_metadata_section(analysis))
            story.extend(self._build_visual_insights_section(analysis))
            story.extend(self._build_key_clauses_section(analysis))
            story.extend(self._build_risk_assessment_section(analysis))
            story.extend(self._build_appendix_section(analysis))

            # Build PDF
            doc.build(story)

            return file_path
        except Exception as e:
            logger.error(f"PDF export failed: {e}")
            raise

    def _build_header_section(
        self, analysis: Dict[str, Any], original_filename: str
    ) -> List[Any]:
        """Build the report header with title and document info"""
        elements = []

        # Main title
        elements.append(
            Paragraph("Legal Document Analysis Report", self.styles["ReportTitle"])
        )
        elements.append(Spacer(1, 20))

        # Document info table
        doc_info = [
            ["Document Name", original_filename],
            ["Analysis Date", datetime.now().strftime("%B %d, %Y at %I:%M %p")],
            ["Document Type", analysis.get("document_type", "Unknown")],
            ["Analysis Confidence", f"{analysis.get('confidence', 0) * 100:.1f}%"],
        ]

        info_table = Table(doc_info, colWidths=[2 * inch, 4 * inch])
        info_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), self.colors["header_bg"]),
                    ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 1, self.colors["neutral"]),
                ]
            )
        )

        elements.append(info_table)
        elements.append(Spacer(1, 30))

        return elements

    def _build_executive_summary(self, analysis: Dict[str, Any]) -> List[Any]:
        """Build executive summary section with key insights"""
        elements = []

        elements.append(Paragraph("Executive Summary", self.styles["SectionHeader"]))

        # Main summary
        summary_text = analysis.get("summary", "No summary available.")
        sentences = re.split(r"(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s", summary_text)

        para = ""
        for i, sentence in enumerate(sentences):
            para += sentence + " "
            if (i + 1) % 4 == 0:
                elements.append(
                    Paragraph(
                        self._bold_keywords(para), self.styles["ExecutiveSummary"]
                    )
                )
                para = ""
        if para:
            elements.append(
                Paragraph(self._bold_keywords(para), self.styles["ExecutiveSummary"])
            )

        elements.append(Spacer(1, 15))

        # Key insights bullets
        insights = self._generate_key_insights(analysis)
        if insights:
            elements.append(Paragraph("Key Insights:", self.styles["SubHeader"]))

            for insight in insights:
                bullet_text = f"• {insight}"
                elements.append(Paragraph(bullet_text, self.styles["ClauseContent"]))

            elements.append(Spacer(1, 20))

        return elements

    def _build_metadata_section(self, analysis: Dict[str, Any]) -> List[Any]:
        """Build document metadata and statistics section"""
        elements = []

        elements.append(Paragraph("Document Overview", self.styles["SectionHeader"]))

        # Statistics table
        stats = self._generate_statistics(analysis)
        stats_data = [
            ["Metric", "Value"],
            ["Total Pages", analysis.get("total_pages", "N/A")],
            ["Total Clauses Identified", len(analysis.get("key_clauses", []))],
            ["High Importance Clauses", stats["importance_counts"].get("high", 0)],
            ["Medium Importance Clauses", stats["importance_counts"].get("medium", 0)],
            ["Low Importance Clauses", stats["importance_counts"].get("low", 0)],
            ["Most Common Clause Type", stats["most_common_type"]],
        ]

        stats_table = Table(stats_data, colWidths=[3 * inch, 2 * inch])
        stats_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), self.colors["primary"]),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [colors.white, self.colors["light_bg"]],
                    ),
                ]
            )
        )

        elements.append(stats_table)
        elements.append(Spacer(1, 20))

        return elements

    def _build_visual_insights_section(self, analysis: Dict[str, Any]) -> List[Any]:
        """Build visual insights section with charts"""
        elements = []

        elements.append(Paragraph("Visual Insights", self.styles["SectionHeader"]))

        clauses = analysis.get("key_clauses", [])
        if len(clauses) > 0:
            high_importance_clauses = [
                c for c in clauses if c.get("importance") == "high"
            ]
            if len(high_importance_clauses) / len(clauses) > 0.5:
                elements.append(
                    Paragraph("⚠ HIGH RISK DOCUMENT", self.styles["RiskMarker"])
                )

        if len(clauses) > 2:  # Only create charts if we have sufficient data
            # Average Risk Score Gauge
            avg_risk_score = self._calculate_average_risk_score(clauses)
            if avg_risk_score is not None:
                elements.append(
                    Paragraph("Average Risk Score", self.styles["SubHeader"])
                )
                elements.append(
                    self._create_gauge_chart(
                        avg_risk_score, 1, 10, width=400, height=40
                    )
                )
                elements.append(Spacer(1, 15))

            # Importance Distribution Pie Chart
            importance_chart = self._create_importance_pie_chart(clauses)
            if importance_chart:
                elements.append(
                    Paragraph(
                        "Clause Importance Distribution", self.styles["SubHeader"]
                    )
                )
                elements.append(importance_chart)
                elements.append(Spacer(1, 15))

            # Clause Type Distribution Bar Chart
            if len(clauses) > 4:  # Only for more complex documents
                type_chart = self._create_clause_type_bar_chart(clauses)
                if type_chart:
                    elements.append(
                        Paragraph("Clause Types Distribution", self.styles["SubHeader"])
                    )
                    elements.append(type_chart)
                    elements.append(Spacer(1, 20))
        else:
            elements.append(
                Paragraph(
                    "Insufficient data for visual analysis.",
                    self.styles["ClauseContent"],
                )
            )
            elements.append(Spacer(1, 20))

        return elements

    def _build_key_clauses_section(self, analysis: Dict[str, Any]) -> List[Any]:
        """Build detailed key clauses section"""
        elements = []

        elements.append(Paragraph("Key Clauses Analysis", self.styles["SectionHeader"]))

        clauses = analysis.get("key_clauses", [])
        if not clauses:
            elements.append(
                Paragraph("No key clauses identified.", self.styles["ClauseContent"])
            )
            return elements

        # Sort clauses by importance and type
        sorted_clauses = sorted(
            clauses,
            key=lambda x: (
                {"high": 0, "medium": 1, "low": 2}.get(
                    x.get("importance", "low").lower(), 2
                ),
                x.get("type", "Unknown"),
            ),
        )

        for i, clause in enumerate(sorted_clauses, 1):
            clause_elements = []

            # Clause header with importance badge
            importance = clause.get("importance", "low").lower()
            clause_type = clause.get("type", "Unknown")
            page_info = (
                f" (Page {clause.get('page', 'N/A')})" if clause.get("page") else ""
            )

            header_text = f"<b>{i}. {clause_type}</b>{page_info}"
            clause_elements.append(Paragraph(header_text, self.styles["SubHeader"]))

            # Importance and risk badges
            badges_data = [
                [
                    f"Importance: {importance.capitalize()}",
                    f"Risk: {clause.get('risk_level', 'N/A')}",
                ]
            ]

            badges_table = Table(badges_data, colWidths=[2.5 * inch, 2.5 * inch])
            badges_table.setStyle(
                TableStyle(
                    [
                        (
                            "BACKGROUND",
                            (0, 0),
                            (0, 0),
                            self.risk_colors.get(importance, self.colors["neutral"]),
                        ),
                        (
                            "BACKGROUND",
                            (1, 0),
                            (1, 0),
                            self.risk_colors.get(
                                clause.get("risk_level", "low").lower(),
                                self.colors["neutral"],
                            ),
                        ),
                        ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 9),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ]
                )
            )

            clause_elements.append(badges_table)
            clause_elements.append(Spacer(1, 8))

            # Clause content
            content = clause.get("content", "No content available.")
            if len(content) > 500:
                content = content[:500] + "..."
            clause_elements.append(
                Paragraph(
                    self._bold_keywords(f"<b>Content:</b> {content}"),
                    self.styles["ClauseContent"],
                )
            )

            # Explanation if available
            explanation = clause.get("explanation", "")
            if explanation:
                clause_elements.append(
                    Paragraph(
                        self._bold_keywords(f"<b>Analysis:</b> {explanation}"),
                        self.styles["ClauseContent"],
                    )
                )

            clause_elements.append(Spacer(1, 15))

            # Keep clause together on one page
            elements.append(KeepTogether(clause_elements))

        return elements

    def _build_risk_assessment_section(self, analysis: Dict[str, Any]) -> List[Any]:
        """Build risk assessment section"""
        elements = []

        elements.append(Paragraph("Risk Assessment", self.styles["SectionHeader"]))

        # Overall risk indicator
        risk_level = analysis.get("risk_assessment", {}).get("overall_risk", "Medium")
        risk_color = self.risk_colors.get(risk_level.lower(), self.colors["neutral"])

        risk_header = f"<para align=center backColor={risk_color} fontSize=14 textColor=white>Overall Risk Level: {risk_level.upper()}</para>"
        elements.append(Paragraph(risk_header, self.styles["RiskBadge"]))
        elements.append(Spacer(1, 15))

        # Key concerns
        concerns = analysis.get("risk_assessment", {}).get("key_concerns", [])
        if concerns:
            elements.append(Paragraph(f"• {concerns[0]}", self.styles["ClauseContent"]))
            elements.append(Spacer(1, 10))

        # Recommendations
        recommendations = analysis.get("risk_assessment", {}).get("recommendations", [])
        if recommendations:
            elements.append(
                Paragraph(f"• {recommendations[0]}", self.styles["ClauseContent"])
            )

        elements.append(Spacer(1, 20))
        return elements

    def _build_appendix_section(self, analysis: Dict[str, Any]) -> List[Any]:
        """Build appendix with technical details"""
        elements = []

        elements.append(PageBreak())
        elements.append(Paragraph("Appendix", self.styles["SectionHeader"]))

        # Technical details
        tech_details = [
            ["Analysis Engine", "OpenRouter (GPT-4-mini)"],
            ["Processing Date", datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")],
            ["Confidence Score", f"{analysis.get('confidence', 0):.3f}"],
            ["Total Clauses Processed", str(len(analysis.get("key_clauses", [])))],
            ["Document Pages", str(analysis.get("total_pages", "N/A"))],
        ]

        tech_table = Table(tech_details, colWidths=[2.5 * inch, 3 * inch])
        tech_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), self.colors["header_bg"]),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("GRID", (0, 0), (-1, -1), 1, self.colors["neutral"]),
                ]
            )
        )

        elements.append(tech_table)
        elements.append(Spacer(1, 20))

        # Disclaimer
        disclaimer = """
        <b>Disclaimer:</b> This analysis is generated by artificial intelligence and should be reviewed by qualified legal professionals. 
        The AI may miss important clauses or misinterpret legal language. This report is for informational purposes only and does not constitute legal advice.
        """
        elements.append(Paragraph(disclaimer, self.styles["ClauseContent"]))

        return elements

    def _create_gauge_chart(
        self, value: float, min_val: int, max_val: int, width: int, height: int
    ) -> Drawing:
        d = Drawing(width, height)
        # Background
        d.add(Rect(0, 0, width, height, fillColor=colors.lightgrey, strokeColor=None))
        # Value bar
        bar_width = (value - min_val) / (max_val - min_val) * width
        bar_color = colors.green
        if value > 7:
            bar_color = colors.red
        elif value > 4:
            bar_color = colors.orange
        d.add(Rect(0, 0, bar_width, height, fillColor=bar_color, strokeColor=None))
        # Text
        d.add(
            String(
                width / 2,
                height / 2,
                f"{value:.2f}",
                textAnchor="middle",
                fillColor=colors.white,
            )
        )
        return d

    def _calculate_average_risk_score(
        self, clauses: List[Dict[str, Any]]
    ) -> Optional[float]:
        risk_scores = [clause.get("risk_score", 0) for clause in clauses]
        if not risk_scores:
            return None
        return statistics.mean(risk_scores)

    def _create_importance_pie_chart(
        self, clauses: List[Dict[str, Any]]
    ) -> Optional[Drawing]:
        """Create pie chart for clause importance distribution"""
        try:
            # Count importance levels
            importance_counts = Counter(
                clause.get("importance", "low").lower() for clause in clauses
            )
            total_clauses = len(clauses)

            # Prepare data
            data = []
            labels = []
            colors_list = []

            for importance in ["high", "medium", "low"]:
                count = importance_counts.get(importance, 0)
                if count > 0:
                    data.append(count)
                    percentage = (count / total_clauses) * 100
                    labels.append(f"{importance.capitalize()}\n({percentage:.1f}%)")
                    colors_list.append(
                        self.risk_colors.get(importance, self.colors["neutral"])
                    )

            if not data:
                return None

            # Create drawing
            drawing = Drawing(400, 200)

            # Create pie chart
            pie = Pie()
            pie.x = 50
            pie.y = 50
            pie.width = 150
            pie.height = 150
            pie.data = data
            pie.labels = labels
            pie.slices.strokeWidth = 1
            pie.slices.strokeColor = colors.white

            # Set colors
            for i, color in enumerate(colors_list):
                if i < len(pie.slices):
                    pie.slices[i].fillColor = color

            # Add legend
            legend = Legend()
            legend.x = 220
            legend.y = 100
            legend.dx = 8
            legend.dy = 8
            legend.fontName = "Helvetica"
            legend.fontSize = 10
            legend.boxAnchor = "w"
            legend.columnMaximum = 3
            legend.colorNamePairs = [
                (colors_list[i], labels[i]) for i in range(len(labels))
            ]

            drawing.add(pie)
            drawing.add(legend)

            return drawing
        except Exception as e:
            logger.error(f"Pie chart creation failed: {e}")
            return None

    def _create_clause_type_bar_chart(
        self, clauses: List[Dict[str, Any]]
    ) -> Optional[Drawing]:
        """Create bar chart for clause types distribution"""
        try:
            # Count clause types
            type_counts = Counter(clause.get("type", "Unknown") for clause in clauses)

            # Get top 6 most common types
            top_types = type_counts.most_common(6)
            if not top_types:
                return None

            # Prepare data
            data = [[count for _, count in top_types]]
            labels = [
                type_name[:15] + "..." if len(type_name) > 15 else type_name
                for type_name, _ in top_types
            ]

            # Create drawing
            drawing = Drawing(500, 250)

            # Create bar chart
            bc = VerticalBarChart()
            bc.x = 50
            bc.y = 50
            bc.height = 150
            bc.width = 400
            bc.data = data
            bc.strokeColor = colors.black
            bc.valueAxis.valueMin = 0
            bc.valueAxis.valueMax = max(count for _, count in top_types) + 1
            bc.valueAxis.valueStep = 1
            bc.categoryAxis.categoryNames = labels
            bc.categoryAxis.labels.angle = 45
            bc.categoryAxis.labels.fontSize = 8
            bc.bars[0].fillColor = self.colors["primary"]

            drawing.add(bc)

            return drawing
        except Exception as e:
            logger.error(f"Bar chart creation failed: {e}")
            return None

    def _generate_statistics(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate statistical summary of the analysis"""
        clauses = analysis.get("key_clauses", [])

        # Count importance levels
        importance_counts = Counter(
            clause.get("importance", "low").lower() for clause in clauses
        )

        # Count clause types
        type_counts = Counter(clause.get("type", "Unknown") for clause in clauses)
        most_common_type = type_counts.most_common(1)[0][0] if type_counts else "N/A"

        # Calculate risk distribution
        risk_counts = Counter(
            clause.get("risk_level", "low").lower() for clause in clauses
        )

        return {
            "total_clauses": len(clauses),
            "importance_counts": dict(importance_counts),
            "risk_counts": dict(risk_counts),
            "type_counts": dict(type_counts),
            "most_common_type": most_common_type,
            "unique_types": len(type_counts),
        }

    def _generate_key_insights(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate key insights from the analysis"""
        insights = []
        clauses = analysis.get("key_clauses", [])
        stats = self._generate_statistics(analysis)

        # High importance insights
        high_importance = stats["importance_counts"].get("high", 0)
        if high_importance > 0:
            insights.append(
                f"Found {high_importance} high-importance clause{'s' if high_importance != 1 else ''} requiring attention"
            )

        # Risk insights
        high_risk = stats["risk_counts"].get("high", 0)
        if high_risk > 0:
            insights.append(
                f"Identified {high_risk} high-risk clause{'s' if high_risk != 1 else ''} that may need legal review"
            )

        # Complexity insights
        if len(clauses) > 10:
            insights.append("This is a complex document with numerous legal provisions")
        elif len(clauses) < 3:
            insights.append("This appears to be a relatively simple document")

        # Type diversity insights
        if stats["unique_types"] > 5:
            insights.append(
                "Document contains diverse clause types indicating comprehensive coverage"
            )

        # Confidence insights
        confidence = analysis.get("confidence", 0)
        if confidence < 0.7:
            insights.append(
                "Analysis confidence is moderate - manual review recommended"
            )
        elif confidence > 0.9:
            insights.append("High confidence analysis with clear document structure")

        return insights[:5]  # Limit to top 5 insights

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe export"""
        # Remove extension and sanitize
        base_name = filename.rsplit(".", 1)[0] if "." in filename else filename
        # Replace problematic characters
        safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
        sanitized = "".join(c if c in safe_chars else "_" for c in base_name)
        return sanitized[:50]  # Limit length


# Convenience functions for backward compatibility
def export_as_json(analysis: Dict[str, Any], original_filename: str) -> str:
    """Export analysis as JSON (backward compatibility)"""
    generator = ReportGenerator()
    return generator.export_as_json(analysis, original_filename)


def export_as_pdf(analysis: Dict[str, Any], original_filename: str) -> str:
    """Export analysis as PDF (backward compatibility)"""
    generator = ReportGenerator()
    return generator.export_as_pdf(analysis, original_filename)
