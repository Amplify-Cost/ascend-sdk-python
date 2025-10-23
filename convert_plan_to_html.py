"""
Convert Enterprise Rebuild Plan to styled HTML
"""
import markdown
from pathlib import Path

# Read the markdown file
md_path = Path('/mnt/user-data/outputs/ENTERPRISE_REBUILD_PLAN.md')
with open(md_path, 'r') as f:
    md_content = f.read()

# Convert to HTML with extensions
html_content = markdown.markdown(
    md_content,
    extensions=[
        'tables',
        'fenced_code',
        'codehilite',
        'toc',
        'attr_list'
    ]
)

# Add CSS styling
html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OW-AI Enterprise Rebuild Plan</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            border-radius: 8px;
        }}
        
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            margin-bottom: 30px;
            font-size: 2.5em;
        }}
        
        h2 {{
            color: #34495e;
            margin-top: 40px;
            margin-bottom: 20px;
            font-size: 2em;
            border-left: 4px solid #3498db;
            padding-left: 15px;
        }}
        
        h3 {{
            color: #555;
            margin-top: 30px;
            margin-bottom: 15px;
            font-size: 1.5em;
        }}
        
        h4 {{
            color: #666;
            margin-top: 20px;
            margin-bottom: 10px;
        }}
        
        p {{
            margin-bottom: 15px;
        }}
        
        code {{
            background: #f8f8f8;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            color: #e74c3c;
        }}
        
        pre {{
            background: #2c3e50;
            color: #ecf0f1;
            padding: 20px;
            border-radius: 5px;
            overflow-x: auto;
            margin: 20px 0;
        }}
        
        pre code {{
            background: transparent;
            color: #ecf0f1;
            padding: 0;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        
        th {{
            background: #3498db;
            color: white;
            font-weight: bold;
        }}
        
        tr:nth-child(even) {{
            background: #f9f9f9;
        }}
        
        ul, ol {{
            margin: 15px 0 15px 30px;
        }}
        
        li {{
            margin-bottom: 8px;
        }}
        
        blockquote {{
            border-left: 4px solid #3498db;
            padding-left: 20px;
            margin: 20px 0;
            color: #555;
            font-style: italic;
        }}
        
        .toc {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 30px;
        }}
        
        .toc h2 {{
            margin-top: 0;
        }}
        
        .success {{
            color: #27ae60;
            font-weight: bold;
        }}
        
        .warning {{
            color: #f39c12;
            font-weight: bold;
        }}
        
        .error {{
            color: #e74c3c;
            font-weight: bold;
        }}
        
        .highlight {{
            background: #fff3cd;
            padding: 15px;
            border-left: 4px solid #ffc107;
            margin: 20px 0;
        }}
        
        @media print {{
            body {{
                background: white;
                padding: 0;
            }}
            
            .container {{
                box-shadow: none;
                padding: 20px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏢 OW-AI Enterprise Governance System</h1>
            <h2 style="color: #3498db; border: none; margin-top: 0;">Complete Rebuild Implementation Plan</h2>
            <p><strong>Date:</strong> October 22, 2025</p>
            <p><strong>Status:</strong> <span class="success">✅ Ready for Implementation</span></p>
            <p><strong>Timeline:</strong> 14 Days</p>
        </div>
        
        <hr style="margin: 30px 0; border: none; border-top: 2px solid #eee;">
        
        {html_content}
        
        <hr style="margin: 30px 0; border: none; border-top: 2px solid #eee;">
        
        <footer style="text-align: center; color: #999; margin-top: 40px;">
            <p>Generated on {Path.ctime(md_path)}</p>
            <p>OW-AI Enterprise Platform - Internal Documentation</p>
        </footer>
    </div>
</body>
</html>
"""

# Save HTML file
output_path = Path('/mnt/user-data/outputs/ENTERPRISE_REBUILD_PLAN.html')
with open(output_path, 'w') as f:
    f.write(html_template)

print(f"✅ HTML file created: {output_path}")
print(f"   File size: {output_path.stat().st_size / 1024:.1f} KB")
