import datetime
import json
from visualization import interpret_score

class ReportGenerator:
    """Generate analysis reports in various formats."""
    
    def __init__(self, analyzer, mesh_info=None):
        self.analyzer = analyzer
        self.mesh_info = mesh_info
        
    def generate_html_report(self, visualization_fig=None, summary_chart_base64=None):
        """Generate comprehensive HTML report."""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        score = self.analyzer.calculate_score()
        interpretation = interpret_score(score)
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>CNC Manufacturability Report</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background-color: #2c3e50;
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }}
        .section {{
            background-color: white;
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        .score-box {{
            font-size: 48px;
            font-weight: bold;
            text-align: center;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
        }}
        .excellent {{ background-color: #2ecc71; color: white; }}
        .good {{ background-color: #3498db; color: white; }}
        .fair {{ background-color: #f39c12; color: white; }}
        .difficult {{ background-color: #e74c3c; color: white; }}
        .problem-item {{
            background-color: #f8f9fa;
            padding: 15px;
            margin: 10px 0;
            border-left: 5px solid #e74c3c;
            border-radius: 5px;
        }}
        .no-problem {{
            border-left-color: #2ecc71;
        }}
        .recommendation {{
            background-color: #e8f4f8;
            padding: 15px;
            border-left: 5px solid #3498db;
            margin: 10px 0;
            border-radius: 5px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #34495e;
            color: white;
        }}
        .chart-container {{
            text-align: center;
            margin: 20px 0;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>CNC Manufacturability Analysis Report</h1>
        <p>Generated: {timestamp}</p>
    </div>
    
    <div class="section">
        <h2>Overall Score</h2>
        <div class="score-box {self._get_score_class(score)}">
            {score:.1f} / 100
        </div>
        <p style="text-align: center; font-size: 20px;">{interpretation}</p>
    </div>
"""
        
        # Add summary chart if available
        if summary_chart_base64:
            html += f"""
    <div class="section">
        <h2>Analysis Summary</h2>
        <div class="chart-container">
            <img src="data:image/png;base64,{summary_chart_base64}" alt="Summary Chart" style="max-width: 100%;">
        </div>
    </div>
"""
        
        # Mesh information
        if self.mesh_info:
            html += f"""
    <div class="section">
        <h2>Mesh Information</h2>
        <table>
            <tr><th>Property</th><th>Value</th></tr>
            <tr><td>Vertices</td><td>{self.mesh_info.get('vertices', 'N/A')}</td></tr>
            <tr><td>Faces</td><td>{self.mesh_info.get('faces', 'N/A')}</td></tr>
            <tr><td>Volume</td><td>{self.mesh_info.get('volume', 0):.2f} mm³</td></tr>
            <tr><td>Watertight</td><td>{'Yes' if self.mesh_info.get('is_watertight', False) else 'No'}</td></tr>
        </table>
    </div>
"""
        
        # Detailed analysis results
        html += """
    <div class="section">
        <h2>Detailed Analysis Results</h2>
"""
        
        for function_name, results in self.analyzer.results.items():
            problem_name = function_name.replace('_', ' ').title()
            has_problem = results.get('has_problem', results.get('count', 0) > 0 or results.get('severity', 0) > 0)
            
            html += f"""
        <div class="problem-item {'no-problem' if not has_problem else ''}">
            <h3>{problem_name}</h3>
"""
            
            if 'error' in results:
                html += f"<p style='color: red;'>Error: {results['error']}</p>"
            else:
                if has_problem:
                    if 'count' in results:
                        html += f"<p><strong>Found:</strong> {results['count']} problematic faces</p>"
                    if 'severity' in results:
                        html += f"<p><strong>Severity:</strong> {['None', 'Minor', 'Major'][results['severity']]}</p>"
                    if 'recommendation' in results:
                        html += f"<div class='recommendation'><strong>Recommendation:</strong> {results['recommendation']}</div>"
                else:
                    html += "<p style='color: green;'><strong>✓ No issues detected</strong></p>"
                
                # Add specific details
                if 'data' in results and isinstance(results['data'], dict):
                    html += "<p><strong>Details:</strong></p><ul>"
                    for key, value in results['data'].items():
                        if key != 'error' and not key.startswith('_'):
                            html += f"<li>{key.replace('_', ' ').title()}: {value}</li>"
                    html += "</ul>"
            
            html += "</div>"
        
        html += """
    </div>
    
    <div class="section">
        <h2>Recommendations</h2>
"""
        
        recommendations = self._generate_recommendations()
        for rec in recommendations:
            html += f"<div class='recommendation'>{rec}</div>"
        
        html += """
    </div>
</body>
</html>
"""
        return html
    
    def generate_json_report(self):
        """Generate JSON report for programmatic use."""
        score = self.analyzer.calculate_score()
        
        report = {
            'timestamp': datetime.datetime.now().isoformat(),
            'score': score,
            'interpretation': interpret_score(score),
            'mesh_info': self.mesh_info,
            'analysis_results': self.analyzer.results,
            'problem_regions': [
                {'name': name, 'face_count': len(indices)}
                for name, indices in self.analyzer.get_problem_regions()
            ],
            'recommendations': self._generate_recommendations()
        }
        
        return json.dumps(report, indent=2)
    
    def generate_markdown_report(self):
        """Generate Markdown report."""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        score = self.analyzer.calculate_score()
        interpretation = interpret_score(score)
        
        md = f"""# CNC Manufacturability Analysis Report

Generated: {timestamp}

## Overall Score: {score:.1f} / 100

**Assessment:** {interpretation}

## Mesh Information

"""
        if self.mesh_info:
            md += f"""- **Vertices:** {self.mesh_info.get('vertices', 'N/A')}
- **Faces:** {self.mesh_info.get('faces', 'N/A')}
- **Volume:** {self.mesh_info.get('volume', 0):.2f} mm³
- **Watertight:** {'Yes' if self.mesh_info.get('is_watertight', False) else 'No'}

"""
        
        md += "## Analysis Results\n\n"
        
        for function_name, results in self.analyzer.results.items():
            problem_name = function_name.replace('_', ' ').title()
            md += f"### {problem_name}\n\n"
            
            if 'error' in results:
                md += f"❌ **Error:** {results['error']}\n\n"
            else:
                has_problem = results.get('has_problem', results.get('count', 0) > 0 or results.get('severity', 0) > 0)
                
                if has_problem:
                    md += "⚠️ **Issues Detected**\n\n"
                    if 'count' in results:
                        md += f"- **Count:** {results['count']} problematic faces\n"
                    if 'severity' in results:
                        md += f"- **Severity:** {['None', 'Minor', 'Major'][results['severity']]}\n"
                    if 'recommendation' in results:
                        md += f"- **Recommendation:** {results['recommendation']}\n"
                else:
                    md += "✅ **No issues detected**\n"
                # Add specific details if present
                if 'data' in results and isinstance(results['data'], dict):
                    md += "\n**Details:**\n"
                    for key, value in results['data'].items():
                        if key != 'error' and not key.startswith('_'):
                            md += f"- {key.replace('_', ' ').title()}: {value}\n"
            md += "\n"

        # Recommendations section
        md += "## Recommendations\n\n"
        recommendations = self._generate_recommendations()
        for rec in recommendations:
            md += f"- {rec}\n"

        return md
        
    def _get_score_class(self, score):
        """Return CSS class for score box based on score."""
        if score >= 90:
            return "excellent"
        elif score >= 80:
            return "good"
        elif score >= 70:
            return "fair"
        else:
            return "difficult"

    def _generate_recommendations(self):
        """Generate recommendations based on analysis results."""
        recs = []
        for function_name, results in self.analyzer.results.items():
            if 'recommendation' in results and results['recommendation']:
                recs.append(results['recommendation'])
        if not recs:
            recs.append("No major manufacturability issues detected. Design is CNC-friendly.")
        return recs