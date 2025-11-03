"""Convert markdown to styled HTML"""
import subprocess
import sys

try:
    import markdown
except ImportError:
    print("Installing markdown...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "markdown", "-q"])
    import markdown

from pathlib import Path
from datetime import datetime

# Read markdown
md_path = Path('ENTERPRISE_REBUILD_PLAN.md')
with open(md_path, 'r') as f:
    md_content = f.read()

# Convert to HTML
html_body = markdown.markdown(
    md_content,
    extensions=['tables', 'fenced_code', 'codehilite', 'toc']
)

# Full HTML with styling
html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OW-AI Enterprise Rebuild Plan</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 40px;
            background: #f5f5f5;
        }}
        .container {{
            background: white;
            padding: 40px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            border-radius: 8px;
        }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; margin-top: 40px; border-left: 4px solid #3498db; padding-left: 15px; }}
        h3 {{ color: #555; margin-top: 30px; }}
        code {{ background: #f8f8f8; padding: 2px 6px; border-radius: 3px; color: #e74c3c; }}
        pre {{ background: #2c3e50; color: #ecf0f1; padding: 20px; border-radius: 5px; overflow-x: auto; }}
        pre code {{ background: transparent; color: #ecf0f1; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background: #3498db; color: white; }}
        tr:nth-child(even) {{ background: #f9f9f9; }}
        ul, ol {{ margin-left: 30px; }}
        li {{ margin-bottom: 8px; }}
    </style>
</head>
<body>
    <div class="container">
        <div style="text-align: center; margin-bottom: 40px;">
            <h1>🏢 OW-AI Enterprise Governance System</h1>
            <h2 style="color: #3498db; border: none;">Complete Rebuild Implementation Plan</h2>
            <p><strong>Generated:</strong> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
        </div>
        
        {html_body}
        
        <hr style="margin: 40px 0; border: none; border-top: 2px solid #eee;">
        <footer style="text-align: center; color: #999;">
            <p>OW-AI Enterprise Platform - Internal Documentation</p>
            <p>Ready for Phase 1 Implementation</p>
        </footer>
    </div>
</body>
</html>"""

# Save HTML
output_path = Path('ENTERPRISE_REBUILD_PLAN.html')
with open(output_path, 'w') as f:
    f.write(html_content)

print(f"✅ HTML file created: {output_path.absolute()}")
print(f"   File size: {output_path.stat().st_size / 1024:.1f} KB")
print(f"\n📂 Saved to: {output_path.absolute()}")
