import os
from datetime import datetime

print("Generating OW-KAI documentation...")
os.makedirs("enterprise-docs", exist_ok=True)

html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>OW-KAI Technologies</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            padding: 60px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }}
        h1 {{ color: #667eea; font-size: 3em; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 OW-KAI Technologies</h1>
        <h2>Enterprise AI Agent Governance Platform</h2>
        <p><strong>Company:</strong> OW-KAI Technologies, Inc. (Delaware C-Corporation)</p>
        <p><strong>Platform:</strong> <a href="https://pilot.owkai.app">https://pilot.owkai.app</a></p>
        <p><strong>Status:</strong> 95% Enterprise-Ready</p>
        <p>Generated: {datetime.now().strftime("%B %d, %Y")}</p>
    </div>
</body>
</html>'''

with open("enterprise-docs/index.html", "w") as f:
    f.write(html)

print("✅ Done! Opening documentation...")
