from typing import Dict, List
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from datetime import datetime
import os
from loguru import logger

class PDFGenerator:
    """Generate PDF documentation from Figma design data"""
    
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        self.styles.add(ParagraphStyle(
            name='Heading1',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceAfter=20
        ))
        self.styles.add(ParagraphStyle(
            name='Heading2',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=15
        ))
        self.styles.add(ParagraphStyle(
            name='Normal',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=10
        ))
    
    def generate_pdf(self, stories: List[Dict], epics: List[Dict]) -> str:
        """
        Generate PDF documentation from stories and epics
        
        Args:
            stories: List of story dictionaries
            epics: List of epic dictionaries
            
        Returns:
            Path to generated PDF file
        """
        try:
            # Create output directory if it doesn't exist
            os.makedirs(self.output_dir, exist_ok=True)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(self.output_dir, f"figma_stories_{timestamp}.pdf")
            
            # Create PDF document
            doc = SimpleDocTemplate(
                filename,
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )
            
            # Build content
            content = []
            
            # Add title
            content.append(Paragraph("Figma Design Documentation", self.styles['Title']))
            content.append(Spacer(1, 20))
            
            # Add epics section
            content.extend(self._generate_epics_section(epics))
            content.append(Spacer(1, 20))
            
            # Add stories section
            content.extend(self._generate_stories_section(stories))
            
            # Build PDF
            doc.build(content)
            logger.info(f"Generated PDF documentation: {filename}")
            
            return filename
            
        except Exception as e:
            logger.error(f"Error generating PDF: {e}")
            raise
    
    def _generate_epics_section(self, epics: List[Dict]) -> List:
        """Generate content for epics section"""
        content = []
        
        content.append(Paragraph("Epics", self.styles['Heading1']))
        content.append(Spacer(1, 10))
        
        for epic in epics:
            # Epic title
            content.append(Paragraph(epic['summary'], self.styles['Heading2']))
            
            # Epic description
            content.append(Paragraph(epic['description'], self.styles['Normal']))
            
            # Epic stories table
            if epic.get('stories'):
                story_data = [[
                    Paragraph("Story", self.styles['Normal']),
                    Paragraph("Type", self.styles['Normal']),
                    Paragraph("Priority", self.styles['Normal']),
                    Paragraph("Points", self.styles['Normal'])
                ]]
                
                for story in epic['stories']:
                    story_data.append([
                        Paragraph(story['summary'], self.styles['Normal']),
                        Paragraph(story['issue_type'], self.styles['Normal']),
                        Paragraph(story['priority'], self.styles['Normal']),
                        str(story['story_points'])
                    ])
                
                table = Table(story_data, colWidths=[4*inch, 1*inch, 1*inch, 0.5*inch])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                content.append(table)
            
            content.append(Spacer(1, 20))
        
        return content
    
    def _generate_stories_section(self, stories: List[Dict]) -> List:
        """Generate content for stories section"""
        content = []
        
        content.append(Paragraph("Detailed Stories", self.styles['Heading1']))
        content.append(Spacer(1, 10))
        
        for story in stories:
            # Story title
            content.append(Paragraph(story['summary'], self.styles['Heading2']))
            
            # Story details
            content.append(Paragraph(f"Type: {story['issue_type']}", self.styles['Normal']))
            content.append(Paragraph(f"Priority: {story['priority']}", self.styles['Normal']))
            content.append(Paragraph(f"Story Points: {story['story_points']}", self.styles['Normal']))
            
            # User story
            if story.get('description'):
                content.append(Paragraph("Description:", self.styles['Normal']))
                content.append(Paragraph(story['description'], self.styles['Normal']))
            
            # Acceptance criteria
            if story.get('acceptance_criteria'):
                content.append(Paragraph("Acceptance Criteria:", self.styles['Normal']))
                for criterion in story['acceptance_criteria']:
                    content.append(Paragraph(f"• {criterion}", self.styles['Normal']))
            
            # Technical requirements
            if story.get('technical_requirements'):
                content.append(Paragraph("Technical Requirements:", self.styles['Normal']))
                for req in story['technical_requirements']:
                    content.append(Paragraph(f"• {req}", self.styles['Normal']))
            
            content.append(Spacer(1, 20))
        
        return content 