#!/bin/bash

echo "======================================================"
echo "📄 CONVERTING DOCUMENTATION TO HTML"
echo "======================================================"
echo ""

# Install pandoc if not already installed (for converting markdown to HTML)
if ! command -v pandoc &> /dev/null; then
    echo "📦 Installing pandoc..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        brew install pandoc
    else
        # Linux
        sudo apt-get update && sudo apt-get install -y pandoc
    fi
fi

# Create HTML output directory
mkdir -p enterprise-docs/html/{architecture,api,technical,deployment,user-guides}
mkdir -p enterprise-docs/html/css

# Create beautiful CSS stylesheet
cat > enterprise-docs/html/css/style.css << 'CSS'
/* Enterprise Documentation Styles */
:root {
    --primary-color: #2563eb;
    --secondary-color: #7c3aed;
    --text-color: #1f2937;
    --bg-color: #ffffff;
    --code-bg: #f3f4f6;
    --border-color: #e5e7eb;
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
    line-height: 1.6;
    color: var(--text-color);
    background: var(--bg-color);
    padding: 20px;
    max-width: 1200px;
    margin: 0 auto;
}

header {
    background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
    color: white;
    padding: 40px;
    border-radius: 10px;
    margin-bottom: 40px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

header h1 {
    font-size: 2.5em;
    margin-bottom: 10px;
}

header p {
    font-size: 1.2em;
    opacity: 0.9;
}

nav {
    background: #f9fafb;
    padding: 20px;
    border-radius: 8px;
    margin-bottom: 30px;
    border: 1px solid var(--border-color);
}

nav ul {
    list-style: none;
    display: flex;
    gap: 20px;
    flex-wrap: wrap;
}

nav a {
    color: var(--primary-color);
    text-decoration: none;
    font-weight: 500;
    padding: 8px 16px;
    border-radius: 5px;
    transition: all 0.3s;
}

nav a:hover {
    background: var(--primary-color);
    color: white;
}

main {
    background: white;
    padding: 40px;
    border-radius: 8px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

h1, h2, h3, h4, h5, h6 {
    margin-top: 1.5em;
    margin-bottom: 0.5em;
    color: var(--text-color);
    font-weight: 600;
}

h1 { font-size: 2.5em; border-bottom: 3px solid var(--primary-color); padding-bottom: 10px; }
h2 { font-size: 2em; border-bottom: 2px solid var(--border-color); padding-bottom: 8px; }
h3 { font-size: 1.5em; color: var(--primary-color); }
h4 { font-size: 1.25em; }

p {
    margin-bottom: 1em;
}

code {
    background: var(--code-bg);
    padding: 2px 6px;
    border-radius: 3px;
    font-family: 'Monaco', 'Courier New', monospace;
    font-size: 0.9em;
}

pre {
    background: var(--code-bg);
    padding: 20px;
    border-radius: 8px;
    overflow-x: auto;
    margin: 1.5em 0;
    border-left: 4px solid var(--primary-color);
}

pre code {
    background: none;
    padding: 0;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin: 1.5em 0;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

th, td {
    padding: 12px;
    text-align: left;
    border-bottom: 1px solid var(--border-color);
}

th {
    background: var(--primary-color);
    color: white;
    font-weight: 600;
}

tr:hover {
    background: #f9fafb;
}

ul, ol {
    margin-left: 30px;
    margin-bottom: 1em;
}

li {
    margin-bottom: 0.5em;
}

blockquote {
    border-left: 4px solid var(--primary-color);
    padding-left: 20px;
    margin: 1.5em 0;
    color: #6b7280;
    font-style: italic;
}

.badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.85em;
    font-weight: 600;
    margin: 0 5px;
}

.badge-success { background: #10b981; color: white; }
.badge-warning { background: #f59e0b; color: white; }
.badge-danger { background: #ef4444; color: white; }
.badge-info { background: #3b82f6; color: white; }

footer {
    text-align: center;
    padding: 40px 20px;
    color: #6b7280;
    border-top: 1px solid var(--border-color);
    margin-top: 60px;
}

@media print {
    body { max-width: 100%; }
    nav { display: none; }
    header { page-break-after: avoid; }
    h1, h2, h3 { page-break-after: avoid; }
    pre, table { page-break-inside: avoid; }
}
CSS

echo "✅ Created CSS stylesheet"

# Function to convert markdown to HTML with custom template
convert_to_html() {
    local input_file=$1
    local output_file=$2
    local title=$3
    
    echo "📄 Converting: $(basename $input_file)"
    
    pandoc "$input_file" \
        -f markdown \
        -t html5 \
        --standalone \
        --css="../css/style.css" \
        --toc \
        --toc-depth=3 \
        --metadata title="$title" \
        -o "$output_file"
}

# Convert all documentation files
echo ""
echo "Converting documentation files..."
echo ""

convert_to_html \
    "enterprise-docs/architecture/SYSTEM-ARCHITECTURE.md" \
    "enterprise-docs/html/architecture/system-architecture.html" \
    "OW-AI Platform - System Architecture"

convert_to_html \
    "enterprise-docs/api/API-REFERENCE.md" \
    "enterprise-docs/html/api/api-reference.html" \
    "OW-AI Platform - API Reference"

convert_to_html \
    "enterprise-docs/technical/TECHNICAL-SPECS.md" \
    "enterprise-docs/html/technical/technical-specs.html" \
    "OW-AI Platform - Technical Specifications"

convert_to_html \
    "enterprise-docs/technical/CODE-REVIEW.md" \
    "enterprise-docs/html/technical/code-review.html" \
    "OW-AI Platform - Code Review Report"

convert_to_html \
    "enterprise-docs/deployment/DEPLOYMENT-GUIDE.md" \
    "enterprise-docs/html/deployment/deployment-guide.html" \
    "OW-AI Platform - Deployment Guide"

convert_to_html \
    "enterprise-docs/user-guides/USER-MANUAL.md" \
    "enterprise-docs/html/user-guides/user-manual.html" \
    "OW-AI Platform - User Manual"

# Create main index page
cat > enterprise-docs/html/index.html << 'HTML'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OW-AI Platform - Enterprise Documentation</title>
    <link rel="stylesheet" href="css/style.css">
</head>
<body>
    <header>
        <h1>🚀 OW-AI Platform</h1>
        <p>Enterprise AI Governance Documentation Suite</p>
    </header>

    <main>
        <section>
            <h2>📚 Documentation Library</h2>
            <p>Welcome to the comprehensive OW-AI Platform documentation. This suite provides everything needed for enterprise deployment, integration, and operations.</p>
        </section>

        <section style="margin-top: 40px;">
            <h3>🏗️ Architecture & Design</h3>
            <div style="background: #f9fafb; padding: 20px; border-radius: 8px; margin-top: 10px;">
                <h4><a href="architecture/system-architecture.html">System Architecture</a></h4>
                <p>Complete technical architecture, component diagrams, data flows, and scalability design. Essential reading for architects and technical decision-makers.</p>
                <span class="badge badge-info">1,984 words</span>
                <span class="badge badge-success">Updated Oct 2025</span>
            </div>
        </section>

        <section style="margin-top: 40px;">
            <h3>🔌 API Documentation</h3>
            <div style="background: #f9fafb; padding: 20px; border-radius: 8px; margin-top: 10px;">
                <h4><a href="api/api-reference.html">API Reference</a></h4>
                <p>Complete documentation of 140+ REST API endpoints with request/response examples, authentication details, and code samples.</p>
                <span class="badge badge-info">2,205 words</span>
                <span class="badge badge-warning">140+ Endpoints</span>
            </div>
        </section>

        <section style="margin-top: 40px;">
            <h3>⚙️ Technical Specifications</h3>
            <div style="background: #f9fafb; padding: 20px; border-radius: 8px; margin-top: 10px;">
                <h4><a href="technical/technical-specs.html">Technical Specifications</a></h4>
                <p>System requirements, database schema, security specifications, performance benchmarks, and compliance certifications.</p>
                <span class="badge badge-info">3,049 words</span>
                <span class="badge badge-success">NIST 800-53</span>
                <span class="badge badge-success">SOC 2</span>
            </div>

            <div style="background: #f9fafb; padding: 20px; border-radius: 8px; margin-top: 10px;">
                <h4><a href="technical/code-review.html">Code Review Report</a></h4>
                <p>Professional code analysis with quality metrics, security assessment, and improvement recommendations.</p>
                <span class="badge badge-info">2,172 words</span>
                <span class="badge badge-success">Grade A - 92/100</span>
            </div>
        </section>

        <section style="margin-top: 40px;">
            <h3>🚀 Deployment & Operations</h3>
            <div style="background: #f9fafb; padding: 20px; border-radius: 8px; margin-top: 10px;">
                <h4><a href="deployment/deployment-guide.html">Deployment Guide</a></h4>
                <p>Step-by-step AWS deployment procedures, environment configuration, database setup, and rollback procedures.</p>
                <span class="badge badge-info">2,699 words</span>
                <span class="badge badge-warning">AWS Ready</span>
            </div>
        </section>

        <section style="margin-top: 40px;">
            <h3>👥 User Guides</h3>
            <div style="background: #f9fafb; padding: 20px; border-radius: 8px; margin-top: 10px;">
                <h4><a href="user-guides/user-manual.html">User Manual</a></h4>
                <p>Complete end-user documentation covering all features, workflows, troubleshooting, and FAQs for all user roles.</p>
                <span class="badge badge-info">3,402 words</span>
                <span class="badge badge-success">All Roles</span>
            </div>
        </section>

        <section style="margin-top: 40px; padding: 30px; background: linear-gradient(135deg, #e0e7ff, #fae8ff); border-radius: 8px;">
            <h3>📊 Documentation Statistics</h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-top: 20px;">
                <div style="text-align: center;">
                    <h2 style="color: #2563eb; margin: 0;">15,511</h2>
                    <p>Total Words</p>
                </div>
                <div style="text-align: center;">
                    <h2 style="color: #7c3aed; margin: 0;">31</h2>
                    <p>Pages</p>
                </div>
                <div style="text-align: center;">
                    <h2 style="color: #10b981; margin: 0;">6</h2>
                    <p>Documents</p>
                </div>
                <div style="text-align: center;">
                    <h2 style="color: #f59e0b; margin: 0;">140+</h2>
                    <p>API Endpoints</p>
                </div>
            </div>
        </section>
    </main>

    <footer>
        <p><strong>OW-AI Platform</strong> - Enterprise AI Governance</p>
        <p>Documentation Generated: October 2025</p>
        <p>Platform Version: 2.0 Enterprise</p>
    </footer>
</body>
</html>
HTML

echo ""
echo "======================================================"
echo "✅ HTML CONVERSION COMPLETE!"
echo "======================================================"
echo ""
echo "📁 HTML Documentation Location:"
echo "   enterprise-docs/html/"
echo ""
echo "📄 Files Created:"
echo "   ✅ index.html (main portal)"
echo "   ✅ architecture/system-architecture.html"
echo "   ✅ api/api-reference.html"
echo "   ✅ technical/technical-specs.html"
echo "   ✅ technical/code-review.html"
echo "   ✅ deployment/deployment-guide.html"
echo "   ✅ user-guides/user-manual.html"
echo "   ✅ css/style.css (professional styling)"
echo ""
echo "🌐 Open in Browser:"
echo "   open enterprise-docs/html/index.html"
echo ""
echo "Or navigate to:"
echo "   file://$(pwd)/enterprise-docs/html/index.html"
echo ""
echo "======================================================"

