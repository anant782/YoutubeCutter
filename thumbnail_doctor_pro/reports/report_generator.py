"""
Reports Generator for Thumbnail Doctor Pro Ultimate
Exports analysis results to PDF, HTML, and JSON formats
"""
import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from utils.logger import get_logger

logger = get_logger()

class ReportGenerator:
    def __init__(self, output_dir: str = "reports"):
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
    
    def generate_pdf(self, data: Dict[str, Any], filename: Optional[str] = None) -> str:
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib import colors
            from reportlab.lib.units import inch
            
            if filename is None:
                filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            
            filepath = os.path.join(self.output_dir, filename)
            
            doc = SimpleDocTemplate(filepath, pagesize=letter)
            styles = getSampleStyleSheet()
            
            story = []
            
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#4F46E5'),
                spaceAfter=30
            )
            
            story.append(Paragraph("Thumbnail Doctor Pro - Analysis Report", title_style))
            story.append(Spacer(1, 0.2*inch))
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            story.append(Paragraph(f"Generated: {timestamp}", styles['Normal']))
            story.append(Spacer(1, 0.3*inch))
            
            scores = data.get('scores', {})
            score_data = [
                ['Metric', 'Score'],
                ['Overall', f"{scores.get('overall', 0):.1f}"],
                ['Quality', f"{scores.get('code_quality', scores.get('color', 0)):.1f}"],
                ['Security', f"{scores.get('security', 0):.1f}"],
                ['Performance', f"{scores.get('performance', 0):.1f}"],
                ['Maintainability', f"{scores.get('maintainability', 0):.1f}"]
            ]
            
            score_table = Table(score_data)
            score_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4F46E5')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(score_table)
            story.append(Spacer(1, 0.3*inch))
            
            recommendations = data.get('recommendations', [])
            if recommendations:
                story.append(Paragraph("Recommendations", styles['Heading2']))
                story.append(Spacer(1, 0.2*inch))
                
                for rec in recommendations:
                    priority = rec.get('priority', 'medium')
                    priority_color = colors.red if priority == 'critical' else colors.orange if priority == 'high' else colors.green
                    story.append(Paragraph(
                        f"<b>{rec.get('title', '')}</b> <font color='{priority_color.hexvals()}'>[{priority.upper()}]</font>",
                        styles['Normal']
                    ))
                    story.append(Paragraph(rec.get('description', ''), styles['Normal']))
                    story.append(Spacer(1, 0.1*inch))
            
            doc.build(story)
            logger.info(f"PDF report generated: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"PDF generation failed: {e}")
            raise e
    
    def generate_html(self, data: Dict[str, Any], filename: Optional[str] = None) -> str:
        if filename is None:
            filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        
        filepath = os.path.join(self.output_dir, filename)
        
        scores = data.get('scores', {})
        recommendations = data.get('recommendations', [])
        
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Analysis Report - Thumbnail Doctor Pro</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: #0F0F0F;
            color: #FFFFFF;
            margin: 0;
            padding: 40px;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
        }}
        h1 {{
            color: #818CF8;
            border-bottom: 2px solid #4F46E5;
            padding-bottom: 15px;
        }}
        .score-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        .score-card {{
            background: linear-gradient(135deg, #2D2D2D, #1A1A1A);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            border-left: 4px solid #4F46E5;
        }}
        .score-value {{
            font-size: 36px;
            font-weight: bold;
            color: #818CF8;
        }}
        .score-label {{
            color: #B0B0B0;
            margin-top: 8px;
        }}
        .recommendations {{
            margin-top: 40px;
        }}
        .recommendation {{
            background-color: #1E1E1E;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 15px;
        }}
        .recommendation h3 {{
            margin-top: 0;
            color: #FFFFFF;
        }}
        .priority-high {{
            border-left: 4px solid #EF4444;
        }}
        .priority-medium {{
            border-left: 4px solid #F59E0B;
        }}
        .priority-low {{
            border-left: 4px solid #10B981;
        }}
        .timestamp {{
            color: #666;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Analysis Report</h1>
        <p class="timestamp">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <div class="score-grid">
            <div class="score-card">
                <div class="score-value">{scores.get('overall', 0):.0f}</div>
                <div class="score-label">Overall Score</div>
            </div>
            <div class="score-card">
                <div class="score-value">{scores.get('code_quality', scores.get('color', 0)):.0f}</div>
                <div class="score-label">Quality</div>
            </div>
            <div class="score-card">
                <div class="score-value">{scores.get('security', 0):.0f}</div>
                <div class="score-label">Security</div>
            </div>
            <div class="score-card">
                <div class="score-value">{scores.get('performance', 0):.0f}</div>
                <div class="score-label">Performance</div>
            </div>
            <div class="score-card">
                <div class="score-value">{scores.get('maintainability', 0):.0f}</div>
                <div class="score-label">Maintainability</div>
            </div>
        </div>
        
        <div class="recommendations">
            <h2>💡 Recommendations</h2>
"""
        
        for rec in recommendations:
            priority = rec.get('priority', 'medium')
            html_content += f"""
            <div class="recommendation priority-{priority}">
                <h3>{rec.get('title', '')}</h3>
                <p><strong>Priority:</strong> {priority.upper()}</p>
                <p>{rec.get('description', '')}</p>
                <p><em>Action: {rec.get('action', '')}</em></p>
            </div>
"""
        
        html_content += """
        </div>
    </div>
</body>
</html>"""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"HTML report generated: {filepath}")
        return filepath
    
    def generate_json(self, data: Dict[str, Any], filename: Optional[str] = None) -> str:
        if filename is None:
            filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        filepath = os.path.join(self.output_dir, filename)
        
        report_data = {
            'generated_at': datetime.now().isoformat(),
            'application': 'Thumbnail Doctor Pro Ultimate',
            'version': '1.0.0',
            **data
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        logger.info(f"JSON report generated: {filepath}")
        return filepath
    
    def generate_all(self, data: Dict[str, Any], base_filename: Optional[str] = None) -> Dict[str, str]:
        return {
            'pdf': self.generate_pdf(data, base_filename + '.pdf' if base_filename else None),
            'html': self.generate_html(data, base_filename + '.html' if base_filename else None),
            'json': self.generate_json(data, base_filename + '.json' if base_filename else None)
        }
