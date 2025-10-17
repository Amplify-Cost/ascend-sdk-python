#!/bin/bash

echo "======================================================"
echo "📄 CONVERTING REVIEWS TO HTML & PDF"
echo "======================================================"
echo ""

# Install pandoc if not installed
if ! command -v pandoc &> /dev/null; then
    echo "📦 Installing pandoc..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install pandoc
    else
        sudo apt-get update && sudo apt-get install -y pandoc
    fi
fi

# Install wkhtmltopdf for PDF conversion
if ! command -v wkhtmltopdf &> /dev/null; then
    echo "📦 Installing wkhtmltopdf..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install --cask wkhtmltopdf
    else
        sudo apt-get install -y wkhtmltopdf
    fi
fi

# Create output directories
mkdir -p html-reports/{css,frontend,evidence}
mkdir -p pdf-reports

echo "✅ Tools installed"
echo ""

# Create professional CSS for review reports
cat > html-reports/css/review-style.css << 'CSS'
/* OW-AI Platform Review Reports - Professional Styling */
:root {
    --primary: #2563eb;
    --success: #10b981;
    --warning: #f59e0b;
    --danger: #ef4444;
    --dark: #1f2937;
    --light: #f9fafb;
    --border: #e5e7eb;
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    line-height: 1.6;
    color: var(--dark);
    background: #ffffff;
    padding: 40px;
    max-width: 1200px;
    margin: 0 auto;
}

/* Header */
header {
    background: linear-gradient(135deg, var(--primary), #7c3aed);
    color: white;
    padding: 50px;
    border-radius: 10px;
    margin-bottom: 40px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
}

header h1 {
    font-size: 2.8em;
    margin-bottom: 15px;
    text-shadow: 0 2px 4px rgba(0,0,0,0.2);
}

header .subtitle {
    font-size: 1.3em;
    opacity: 0.95;
}

header .meta {
    margin-top: 20px;
    font-size: 0.95em;
    opacity: 0.85;
}

/* Score Badge */
.score-badge {
    display: inline-block;
    background: rgba(255,255,255,0.2);
    padding: 15px 30px;
    border-radius: 50px;
    font-size: 2em;
    font-weight: bold;
    margin: 20px 0;
    backdrop-filter: blur(10px);
}

/* Headings */
h1, h2, h3, h4, h5, h6 {
    margin-top: 1.5em;
    margin-bottom: 0.8em;
    font-weight: 600;
    line-height: 1.3;
}

h1 {
    font-size: 2.5em;
    color: var(--primary);
    border-bottom: 3px solid var(--primary);
    padding-bottom: 15px;
}

h2 {
    font-size: 2em;
    color: var(--dark);
    border-bottom: 2px solid var(--border);
    padding-bottom: 10px;
}

h3 {
    font-size: 1.5em;
    color: var(--primary);
}

h4 {
    font-size: 1.25em;
    color: var(--dark);
}

/* Paragraphs */
p {
    margin-bottom: 1.2em;
    line-height: 1.8;
}

/* Lists */
ul, ol {
    margin-left: 30px;
    margin-bottom: 1.5em;
}

li {
    margin-bottom: 0.8em;
    line-height: 1.7;
}

/* Status Icons */
li:before {
    font-weight: bold;
    margin-right: 8px;
}

/* Code Blocks */
code {
    background: var(--light);
    padding: 3px 8px;
    border-radius: 4px;
    font-family: 'Monaco', 'Courier New', monospace;
    font-size: 0.9em;
    color: #c7254e;
}

pre {
    background: #2d2d2d;
    color: #f8f8f2;
    padding: 25px;
    border-radius: 8px;
    overflow-x: auto;
    margin: 1.5em 0;
    border-left: 4px solid var(--primary);
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

pre code {
    background: none;
    padding: 0;
    color: #f8f8f2;
}

/* Tables */
table {
    width: 100%;
    border-collapse: collapse;
    margin: 2em 0;
    box-shadow: 0 2px 10px rgba(0,0,0,0.08);
    border-radius: 8px;
    overflow: hidden;
}

th {
    background: var(--primary);
    color: white;
    padding: 15px;
    text-align: left;
    font-weight: 600;
    text-transform: uppercase;
    font-size: 0.9em;
    letter-spacing: 0.5px;
}

td {
    padding: 15px;
    border-bottom: 1px solid var(--border);
}

tr:hover {
    background: var(--light);
}

tr:last-child td {
    border-bottom: none;
}

/* Blockquotes */
blockquote {
    border-left: 4px solid var(--primary);
    padding-left: 25px;
    margin: 2em 0;
    color: #6b7280;
    font-style: italic;
    background: var(--light);
    padding: 20px 25px;
    border-radius: 0 8px 8px 0;
}

/* Status Badges */
.badge {
    display: inline-block;
    padding: 6px 16px;
    border-radius: 20px;
    font-size: 0.85em;
    font-weight: 600;
    margin: 0 5px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.badge-pass, .badge-success {
    background: var(--success);
    color: white;
}

.badge-fail, .badge-danger {
    background: var(--danger);
    color: white;
}

.badge-warning {
    background: var(--warning);
    color: white;
}

.badge-info {
    background: var(--primary);
    color: white;
}

/* Alert Boxes */
.alert {
    padding: 20px 25px;
    border-radius: 8px;
    margin: 2em 0;
    border-left: 5px solid;
}

.alert-success {
    background: #d1fae5;
    border-color: var(--success);
    color: #065f46;
}

.alert-warning {
    background: #fef3c7;
    border-color: var(--warning);
    color: #92400e;
}

.alert-danger {
    background: #fee2e2;
    border-color: var(--danger);
    color: #991b1b;
}

.alert-info {
    background: #dbeafe;
    border-color: var(--primary);
    color: #1e3a8a;
}

/* Horizontal Rules */
hr {
    border: none;
    border-top: 2px solid var(--border);
    margin: 3em 0;
}

/* Links */
a {
    color: var(--primary);
    text-decoration: none;
    border-bottom: 1px solid transparent;
    transition: all 0.3s;
}

a:hover {
    border-bottom: 1px solid var(--primary);
}

/* Stats Grid */
.stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 20px;
    margin: 2em 0;
}

.stat-card {
    background: var(--light);
    padding: 25px;
    border-radius: 8px;
    text-align: center;
    border: 2px solid var(--border);
    transition: all 0.3s;
}

.stat-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
}

.stat-number {
    font-size: 3em;
    font-weight: bold;
    color: var(--primary);
    line-height: 1;
}

.stat-label {
    font-size: 0.9em;
    color: #6b7280;
    margin-top: 10px;
}

/* Table of Contents */
nav#TOC {
    background: var(--light);
    padding: 25px;
    border-radius: 8px;
    margin: 2em 0;
    border: 2px solid var(--border);
}

nav#TOC ul {
    list-style: none;
    margin: 0;
    padding: 0;
}

nav#TOC li {
    margin: 10px 0;
}

nav#TOC a {
    color: var(--dark);
    font-weight: 500;
}

/* Print Styles */
@media print {
    body {
        max-width: 100%;
        padding: 20px;
    }
    
    header {
        background: var(--primary);
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
    }
    
    pre, table, .stat-card {
        page-break-inside: avoid;
    }
    
    h1, h2, h3 {
        page-break-after: avoid;
    }
    
    nav#TOC {
        display: none;
    }
}

/* Responsive */
@media (max-width: 768px) {
    body {
        padding: 20px;
    }
    
    header {
        padding: 30px 20px;
    }
    
    header h1 {
        font-size: 2em;
    }
    
    .stats-grid {
        grid-template-columns: 1fr;
    }
}

/* Special Highlights */
.highlight {
    background: #fef08a;
    padding: 2px 6px;
    border-radius: 3px;
}

.critical {
    color: var(--danger);
    font-weight: bold;
}

.success {
    color: var(--success);
    font-weight: bold;
}

/* Footer */
footer {
    margin-top: 60px;
    padding-top: 40px;
    border-top: 2px solid var(--border);
    text-align: center;
    color: #6b7280;
}

footer p {
    margin: 10px 0;
}
CSS

echo "✅ CSS stylesheet created"
echo ""

# Function to convert markdown to HTML
convert_to_html() {
    local input_file=$1
    local output_file=$2
    local title=$3
    
    echo "📄 Converting: $(basename $input_file) → $(basename $output_file)"
    
    pandoc "$input_file" \
        -f markdown \
        -t html5 \
        --standalone \
        --css="css/review-style.css" \
        --toc \
        --toc-depth=3 \
        --metadata title="$title" \
        --metadata date="$(date '+%B %d, %Y')" \
        -o "$output_file" 2>/dev/null || echo "  ⚠️  File not found: $input_file"
}

# Function to convert HTML to PDF
convert_to_pdf() {
    local html_file=$1
    local pdf_file=$2
    
    if [ -f "$html_file" ]; then
        echo "📑 Converting: $(basename $html_file) → $(basename $pdf_file)"
        wkhtmltopdf \
            --enable-local-file-access \
            --print-media-type \
            --page-size Letter \
            --margin-top 20mm \
            --margin-bottom 20mm \
            --margin-left 20mm \
            --margin-right 20mm \
            "$html_file" "$pdf_file" 2>/dev/null
    fi
}

echo "======================================================"
echo "📄 CONVERTING TO HTML..."
echo "======================================================"
echo ""

# Convert main reports
convert_to_html \
    "COMPLETE-PLATFORM-REVIEW.md" \
    "html-reports/COMPLETE-PLATFORM-REVIEW.html" \
    "OW-AI Platform - Complete Platform Review"

convert_to_html \
    "COMPREHENSIVE-REVIEW-REPORT.md" \
    "html-reports/COMPREHENSIVE-REVIEW-REPORT.html" \
    "OW-AI Platform - Comprehensive Review Report"

convert_to_html \
    "FINDINGS-AND-EVIDENCE.md" \
    "html-reports/FINDINGS-AND-EVIDENCE.html" \
    "OW-AI Platform - Findings and Evidence"

convert_to_html \
    "FIX-INSTRUCTIONS.md" \
    "html-reports/FIX-INSTRUCTIONS.html" \
    "OW-AI Platform - Fix Instructions"

convert_to_html \
    "README.md" \
    "html-reports/README.html" \
    "OW-AI Platform - Review Summary"

convert_to_html \
    "FEATURE-INVENTORY.md" \
    "html-reports/FEATURE-INVENTORY.html" \
    "OW-AI Platform - Feature Inventory"

convert_to_html \
    "API-ENDPOINTS.md" \
    "html-reports/API-ENDPOINTS.html" \
    "OW-AI Platform - API Endpoints"

# Convert frontend reports
convert_to_html \
    "frontend/FRONTEND-ANALYSIS-REPORT.md" \
    "html-reports/frontend/FRONTEND-ANALYSIS-REPORT.html" \
    "OW-AI Platform - Frontend Analysis Report"

convert_to_html \
    "frontend/FRONTEND-COMPONENT-INVENTORY.md" \
    "html-reports/frontend/FRONTEND-COMPONENT-INVENTORY.html" \
    "OW-AI Platform - Frontend Component Inventory"

convert_to_html \
    "frontend/README.md" \
    "html-reports/frontend/README.html" \
    "OW-AI Platform - Frontend Summary"

echo ""
echo "======================================================"
echo "📑 CONVERTING TO PDF..."
echo "======================================================"
echo ""

# Convert HTMLs to PDFs
convert_to_pdf \
    "html-reports/COMPLETE-PLATFORM-REVIEW.html" \
    "pdf-reports/01-Complete-Platform-Review.pdf"

convert_to_pdf \
    "html-reports/COMPREHENSIVE-REVIEW-REPORT.html" \
    "pdf-reports/02-Comprehensive-Review-Report.pdf"

convert_to_pdf \
    "html-reports/FINDINGS-AND-EVIDENCE.html" \
    "pdf-reports/03-Findings-and-Evidence.pdf"

convert_to_pdf \
    "html-reports/FIX-INSTRUCTIONS.html" \
    "pdf-reports/04-Fix-Instructions.pdf"

convert_to_pdf \
    "html-reports/FEATURE-INVENTORY.html" \
    "pdf-reports/05-Feature-Inventory.pdf"

convert_to_pdf \
    "html-reports/API-ENDPOINTS.html" \
    "pdf-reports/06-API-Endpoints.pdf"

convert_to_pdf \
    "html-reports/frontend/FRONTEND-ANALYSIS-REPORT.html" \
    "pdf-reports/07-Frontend-Analysis-Report.pdf"

convert_to_pdf \
    "html-reports/frontend/FRONTEND-COMPONENT-INVENTORY.html" \
    "pdf-reports/08-Frontend-Component-Inventory.pdf"

# Create index page
cat > html-reports/index.html << 'HTML'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OW-AI Platform - Review Reports</title>
    <link rel="stylesheet" href="css/review-style.css">
</head>
<body>
    <header>
        <h1>🎯 OW-AI Platform Review Reports</h1>
        <p class="subtitle">Comprehensive Codebase Analysis</p>
        <p class="meta">Generated: October 2025 | Platform Health: 93%</p>
    </header>

    <main>
        <section>
            <h2>📊 Executive Reports</h2>
            
            <div style="background: #f9fafb; padding: 25px; border-radius: 8px; margin: 20px 0;">
                <h3><a href="COMPLETE-PLATFORM-REVIEW.html">Complete Platform Review</a></h3>
                <p>Executive summary of the entire platform with overall health score and final verdict.</p>
                <span class="badge badge-success">93% Health Score</span>
                <span class="badge badge-info">Production Ready</span>
            </div>

            <div style="background: #f9fafb; padding: 25px; border-radius: 8px; margin: 20px 0;">
                <h3><a href="COMPREHENSIVE-REVIEW-REPORT.html">Comprehensive Review Report</a></h3>
                <p>Detailed backend analysis including all API endpoints, security, and performance testing.</p>
                <span class="badge badge-success">24/27 Endpoints Pass</span>
            </div>
        </section>

        <section style="margin-top: 40px;">
            <h2>🔍 Technical Analysis</h2>
            
            <div style="background: #f9fafb; padding: 25px; border-radius: 8px; margin: 20px 0;">
                <h3><a href="FINDINGS-AND-EVIDENCE.html">Findings and Evidence</a></h3>
                <p>Complete technical findings with test evidence, API responses, and database queries.</p>
            </div>

            <div style="background: #f9fafb; padding: 25px; border-radius: 8px; margin: 20px 0;">
                <h3><a href="FIX-INSTRUCTIONS.html">Fix Instructions</a></h3>
                <p>Step-by-step instructions to fix the 3 minor issues identified (1.5 hours total).</p>
                <span class="badge badge-warning">3 Minor Issues</span>
            </div>
        </section>

        <section style="margin-top: 40px;">
            <h2>🎨 Frontend Reports</h2>
            
            <div style="background: #f9fafb; padding: 25px; border-radius: 8px; margin: 20px 0;">
                <h3><a href="frontend/FRONTEND-ANALYSIS-REPORT.html">Frontend Analysis Report</a></h3>
                <p>Complete frontend component analysis covering all 52 React components.</p>
                <span class="badge badge-success">94% Health Score</span>
            </div>

            <div style="background: #f9fafb; padding: 25px; border-radius: 8px; margin: 20px 0;">
                <h3><a href="frontend/FRONTEND-COMPONENT-INVENTORY.html">Frontend Component Inventory</a></h3>
                <p>Detailed catalog of all frontend components with purpose and status.</p>
                <span class="badge badge-info">52 Components</span>
            </div>
        </section>

        <section style="margin-top: 40px;">
            <h2>📋 Reference Documentation</h2>
            
            <div style="background: #f9fafb; padding: 25px; border-radius: 8px; margin: 20px 0;">
                <h3><a href="FEATURE-INVENTORY.html">Feature Inventory</a></h3>
                <p>Complete list of all platform features across all systems.</p>
            </div>

            <div style="background: #f9fafb; padding: 25px; border-radius: 8px; margin: 20px 0;">
                <h3><a href="API-ENDPOINTS.html">API Endpoints</a></h3>
                <p>All 167 API endpoints documented with test results.</p>
                <span class="badge badge-info">167 Endpoints</span>
            </div>
        </section>

        <section style="margin-top: 40px; padding: 30px; background: linear-gradient(135deg, #e0e7ff, #fae8ff); border-radius: 8px;">
            <h2>📊 Quick Statistics</h2>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-number">93%</div>
                    <div class="stat-label">Overall Health</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">89%</div>
                    <div class="stat-label">API Success Rate</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">52</div>
                    <div class="stat-label">Components Tested</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">1.5</div>
                    <div class="stat-label">Hours to Fix</div>
                </div>
            </div>
        </section>
    </main>

    <footer>
        <p><strong>OW-AI Platform</strong> - Enterprise AI Governance</p>
        <p>Review Generated: October 2025</p>
        <p>Platform Version: 2.0 Enterprise</p>
    </footer>
</body>
</html>
HTML

echo ""
echo "======================================================"
echo "✅ CONVERSION COMPLETE!"
echo "======================================================"
echo ""
echo "📁 HTML Reports: html-reports/"
echo "📁 PDF Reports: pdf-reports/"
echo ""
echo "HTML Files Created:"
ls -lh html-reports/*.html 2>/dev/null | awk '{print "  📄 " $9}'
ls -lh html-reports/frontend/*.html 2>/dev/null | awk '{print "  📄 " $9}'
echo ""
echo "PDF Files Created:"
ls -lh pdf-reports/*.pdf 2>/dev/null | awk '{print "  📑 " $9}'
echo ""
echo "======================================================"
echo "🌐 OPEN IN BROWSER:"
echo "======================================================"
echo ""
echo "  open html-reports/index.html"
echo ""
echo "Or open PDFs:"
echo "  open pdf-reports/"
echo ""
echo "======================================================"

