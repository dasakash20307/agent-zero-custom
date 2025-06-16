"""
Report Formatter module for handling report formatting and styling.
"""
from typing import Dict, List, Any
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

class ReportFormatter:
    """Handles formatting and styling of report content"""
    
    def __init__(self):
        self.style_config = {
            'title': {
                'font': 'Helvetica-Bold',
                'size': 24,
                'margin_top': 72,
                'margin_bottom': 36
            },
            'section_title': {
                'font': 'Helvetica-Bold',
                'size': 16,
                'margin_top': 24,
                'margin_bottom': 12
            },
            'body_text': {
                'font': 'Helvetica',
                'size': 12,
                'margin_top': 12,
                'margin_bottom': 12
            }
        }
    
    def format_text(self, text: str, style_type: str = 'body_text') -> Dict[str, Any]:
        """Format text according to style configuration"""
        style = self.style_config.get(style_type, self.style_config['body_text'])
        return {
            'text': text,
            'font': style['font'],
            'size': style['size'],
            'margin_top': style['margin_top'],
            'margin_bottom': style['margin_bottom']
        }
    
    def create_visualization(self, data: pd.DataFrame, viz_type: str, title: str, output_path: str) -> str:
        """Create and save visualization"""
        plt.figure(figsize=(10, 6))
        
        if viz_type == "line_chart":
            data.plot(kind='line')
        elif viz_type == "bar_chart":
            data.plot(kind='bar')
        elif viz_type == "scatter_plot":
            data.plot(kind='scatter', x=data.columns[0], y=data.columns[1])
        elif viz_type == "pie_chart":
            data.plot(kind='pie', y=data.columns[0])
        else:
            raise ValueError(f"Unsupported visualization type: {viz_type}")
        
        plt.title(title)
        plt.tight_layout()
        
        # Ensure output directory exists
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save visualization
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return output_path
    
    def wrap_text(self, text: str, width: float, font_size: int = 12) -> List[str]:
        """Wrap text to fit within specified width"""
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            current_line.append(word)
            line = " ".join(current_line)
            if len(line) * font_size * 0.6 > width:  # Approximate character width
                current_line.pop()
                lines.append(" ".join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(" ".join(current_line))
        
        return lines
    
    def format_table(self, data: pd.DataFrame) -> str:
        """Format DataFrame as a table string"""
        return data.to_string(index=False)
    
    def format_list(self, items: List[str], list_type: str = 'bullet') -> str:
        """Format list items"""
        if list_type == 'bullet':
            return '\n'.join(f'• {item}' for item in items)
        elif list_type == 'numbered':
            return '\n'.join(f'{i+1}. {item}' for i, item in enumerate(items))
        else:
            raise ValueError(f"Unsupported list type: {list_type}")
    
    def format_code(self, code: str, language: str = '') -> str:
        """Format code blocks"""
        if language:
            return f'```{language}\n{code}\n```'
        return f'```\n{code}\n```'
    
    def format_quote(self, text: str) -> str:
        """Format block quotes"""
        return '\n'.join(f'> {line}' for line in text.split('\n'))
    
    def format_metadata(self, metadata: Dict[str, Any]) -> str:
        """Format metadata as a string"""
        formatted = []
        for key, value in metadata.items():
            formatted.append(f'{key}: {value}')
        return '\n'.join(formatted) 