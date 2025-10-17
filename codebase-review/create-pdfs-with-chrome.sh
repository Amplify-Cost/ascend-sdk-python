#!/bin/bash

echo "======================================================"
echo "📑 CREATING PDFs WITH CHROME"
echo "======================================================"
echo ""

# Chrome path
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

if [ ! -f "$CHROME" ]; then
    echo "❌ Google Chrome not found at expected location"
    exit 1
fi

mkdir -p pdf-reports

echo "Converting HTML reports to PDF..."
echo ""

# Function to convert with Chrome
convert_with_chrome() {
    local html_file=$1
    local pdf_file=$2
    local full_html_path="file://$(pwd)/$html_file"
    
    echo "📄 Converting: $(basename $html_file)"
    
    "$CHROME" --headless --disable-gpu --print-to-pdf="$pdf_file" "$full_html_path" 2>/dev/null
    
    if [ -f "$pdf_file" ]; then
        echo "  ✅ Created: $(basename $pdf_file)"
    else
        echo "  ❌ Failed: $(basename $pdf_file)"
    fi
}

# Convert all reports
convert_with_chrome "html-reports/COMPLETE-PLATFORM-REVIEW.html" "pdf-reports/01-Complete-Platform-Review.pdf"
convert_with_chrome "html-reports/COMPREHENSIVE-REVIEW-REPORT.html" "pdf-reports/02-Comprehensive-Review-Report.pdf"
convert_with_chrome "html-reports/FINDINGS-AND-EVIDENCE.html" "pdf-reports/03-Findings-and-Evidence.pdf"
convert_with_chrome "html-reports/FIX-INSTRUCTIONS.html" "pdf-reports/04-Fix-Instructions.pdf"
convert_with_chrome "html-reports/FEATURE-INVENTORY.html" "pdf-reports/05-Feature-Inventory.pdf"
convert_with_chrome "html-reports/API-ENDPOINTS.html" "pdf-reports/06-API-Endpoints.pdf"
convert_with_chrome "html-reports/frontend/FRONTEND-ANALYSIS-REPORT.html" "pdf-reports/07-Frontend-Analysis-Report.pdf"
convert_with_chrome "html-reports/frontend/FRONTEND-COMPONENT-INVENTORY.html" "pdf-reports/08-Frontend-Component-Inventory.pdf"

echo ""
echo "======================================================"
echo "✅ PDF CREATION COMPLETE"
echo "======================================================"
echo ""
echo "PDFs saved to: pdf-reports/"
ls -lh pdf-reports/*.pdf 2>/dev/null | awk '{print "  " $9 " - " $5}'
echo ""
echo "Open folder:"
echo "  open pdf-reports/"
echo ""

