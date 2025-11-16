# Browser Testing Guide - PDF Generation

**Test Environment:** http://localhost:5174
**Backend:** http://localhost:8000
**Status:** ✅ Both servers running

---

## Pre-Test Checklist

- ✅ Backend running on port 8000
- ✅ Frontend running on port 5174
- ✅ Browser opened to http://localhost:5174
- ✅ pdfmake library installed
- ✅ Build completed successfully
- ✅ Database migration applied

---

## Test Plan: Phase 1.6

### Test 1: Login and Navigation
**Objective:** Verify you can access the Reports tab

**Steps:**
1. Open http://localhost:5174 in browser
2. Login with credentials (admin@owkai.com / password)
3. Navigate to "Reports" tab in the sidebar
4. Verify reports are loaded from backend

**Expected Result:**
- ✅ Reports tab displays
- ✅ Reports library section visible
- ✅ Reports loaded from `/api/enterprise-users/reports/library`
- ✅ Each report shows: title, classification, author, date, download count

---

### Test 2: PDF Download - SOX Report
**Objective:** Download a SOX Compliance Report and verify real data

**Steps:**
1. Find a report with "SOX" or "Compliance" in the title
2. Click the "📥 Download" or "📖 View Report" button
3. Wait for PDF generation (should be < 2 seconds)
4. Check Downloads folder for new PDF file
5. Open the PDF file

**Expected Result:**
- ✅ Alert message shows: "✅ [Title] downloaded successfully!"
- ✅ Alert shows LIVE DATA:
  - Security Score: 92.5%
  - Total Users: 156 (or your actual user count)
  - SOX Compliance: 94.2%
- ✅ PDF file downloaded to ~/Downloads/
- ✅ Filename format: `SOX_Compliance_Report_[timestamp].pdf`

**PDF Content to Verify:**
- ✅ Title page with classification badge
- ✅ Watermark visible (diagonal classification text)
- ✅ Header on every page (company name + page numbers)
- ✅ Footer on every page (timestamp + classification)
- ✅ Executive Summary section
- ✅ KPI table with real numbers (not 94.2, 87.6 hardcoded values)
- ✅ Compliance Status table (SOX, HIPAA, PCI, ISO27001)
- ✅ Department Distribution table
- ✅ Recommendations section
- ✅ Report Metadata section
- ✅ Certification Statement at end

---

### Test 3: PDF Download - Risk Assessment Report
**Objective:** Download a Risk Assessment Report

**Steps:**
1. Find a report with "Risk" in the title
2. Click "📥 Download" button
3. Open the downloaded PDF

**Expected Result:**
- ✅ PDF generated successfully
- ✅ Different layout than SOX report
- ✅ Risk Distribution table visible
- ✅ Large security score displayed (48pt font)
- ✅ High/Medium/Low risk users shown
- ✅ Red watermark if "Highly Confidential"

---

### Test 4: Classification Watermarks
**Objective:** Verify all 5 classification levels render correctly

**Test Each Classification:**
1. **Highly Confidential** - Red watermark (#DC2626)
2. **Confidential** - Orange watermark (#EA580C)
3. **For Official Use Only** - Amber watermark (#D97706)
4. **Internal** - Blue watermark (#2563EB)
5. **Public** - Green watermark (#059669)

**Expected Result:**
- ✅ Watermark visible on every page
- ✅ Diagonal orientation (~45 degrees)
- ✅ Correct color for classification level
- ✅ Appropriate opacity (red = 30%, green = 10%)
- ✅ Text matches classification level

---

### Test 5: Real Data Verification
**Objective:** Confirm NO hardcoded mock data appears

**What to Check in PDF:**
1. Open any downloaded PDF
2. Look at the "Key Performance Indicators" table
3. Check the "Total Users" value

**Expected Result:**
- ✅ Total Users = YOUR actual user count (from backend)
- ✅ NOT the hardcoded value "156" (unless you actually have 156 users)
- ✅ Security Score changes based on real data
- ✅ Compliance percentages reflect real calculations

**How to Verify:**
```bash
# Check actual user count in database
psql -h localhost -U mac_001 -d owkai_pilot -c "SELECT COUNT(*) FROM users;"

# The PDF should show this count, NOT a hardcoded number
```

---

### Test 6: Download Count Tracking
**Objective:** Verify download count increments in database

**Steps:**
1. Note the download count for a specific report (e.g., "5 downloads")
2. Click "Download" button for that report
3. After successful download, refresh the page
4. Check the download count again

**Expected Result:**
- ✅ Download count increased by 1
- ✅ Database updated: `UPDATE enterprise_reports SET download_count = download_count + 1`
- ✅ UI shows new count without page reload

---

### Test 7: Error Handling (Backend Offline)
**Objective:** Verify fallback behavior when backend unavailable

**Steps:**
1. Stop the backend server: `lsof -ti:8000 | xargs kill -9`
2. Try to download a report
3. Check the PDF that downloads

**Expected Result:**
- ✅ Alert shows: "⚠️ PDF downloaded with sample data (backend unavailable)"
- ✅ PDF still downloads (doesn't crash)
- ✅ PDF uses default analytics data (safe fallback)
- ✅ No JavaScript errors in browser console

**Cleanup:**
```bash
# Restart backend
cd /Users/mac_001/OW_AI_Project/ow-ai-backend
python3 main.py &
```

---

### Test 8: Browser Console Check
**Objective:** Verify no errors in browser console

**Steps:**
1. Open browser DevTools (F12 or Cmd+Opt+I)
2. Go to Console tab
3. Download a report
4. Check for errors

**Expected Result:**
- ✅ No red errors in console
- ✅ Console log: "📄 Generating PDF report: [template name]"
- ✅ Console log: "📥 Downloading PDF: [filename]"
- ✅ All imports loaded successfully
- ✅ No "module not found" errors

---

### Test 9: Network Tab Verification
**Objective:** Verify correct API calls are made

**Steps:**
1. Open DevTools → Network tab
2. Filter by "XHR" or "Fetch"
3. Click "Download" button
4. Watch network requests

**Expected Result:**
- ✅ POST request to `/api/enterprise-users/reports/download/{id}`
- ✅ Response status: 200 OK
- ✅ Response includes `live_data` object with:
  - `total_users`
  - `current_security_score`
  - `compliance_status` (SOX, HIPAA, PCI)
- ✅ No 404 errors
- ✅ No 500 errors

---

### Test 10: Multiple Reports in Sequence
**Objective:** Test downloading multiple reports rapidly

**Steps:**
1. Download 3 different reports in quick succession
2. Check Downloads folder
3. Verify all 3 PDFs are unique

**Expected Result:**
- ✅ All 3 PDFs downloaded successfully
- ✅ Each has unique filename (different timestamps)
- ✅ Each has correct content (not duplicates)
- ✅ No race conditions or crashes
- ✅ Download counts updated for all 3

---

## Known Issues to Test For

### Issue 1: pdfmake Not Loading
**Symptom:** Error in console: "Cannot find module 'pdfmake'"
**Fix:** Verify `npm install pdfmake` completed successfully
**Check:** Look in `node_modules/pdfmake/build/` for pdfmake.js

### Issue 2: Fonts Not Rendering
**Symptom:** PDF opens but has no text
**Fix:** pdfmake includes default fonts, should work out of box
**Check:** Verify `pdfmake/build/vfs_fonts.js` exists

### Issue 3: Watermark Not Visible
**Symptom:** PDF has no diagonal classification text
**Fix:** Check classification value is one of: "Highly Confidential", "Confidential", "For Official Use Only", "Internal", "Public"
**Check:** Inspect report.classification in React DevTools

### Issue 4: Hardcoded Data Appears
**Symptom:** PDF shows 156 users but you have different count
**Fix:** Backend not returning live_data correctly
**Check:** Test endpoint directly:
```bash
curl -X POST "http://localhost:8000/api/enterprise-users/reports/download/RPT-001" \
  -H "Cookie: session=test" \
  -H "Content-Type: application/json"
```

---

## Success Criteria

For Phase 1.6 to be marked as COMPLETE, all of the following must pass:

- ✅ Login and navigate to Reports tab successfully
- ✅ Download button generates actual PDF file
- ✅ PDF appears in Downloads folder
- ✅ PDF opens and displays correctly
- ✅ Watermark visible on all pages
- ✅ Headers and footers on every page
- ✅ Real data from backend appears (not hardcoded)
- ✅ Download count increments in database
- ✅ No errors in browser console
- ✅ Network requests return 200 OK
- ✅ All 5 classification levels work
- ✅ Both SOX and Risk templates work
- ✅ Fallback works when backend offline

---

## Testing Shortcuts

### Quick Test (5 minutes)
```
1. Login → Reports tab
2. Download any report
3. Open PDF
4. Verify watermark + real data
5. Check console for errors
✅ PASS if all 5 work
```

### Full Test (20 minutes)
```
Run all 10 tests above
Document results
Take screenshots of successful PDFs
✅ PASS if 10/10 tests pass
```

---

## What to Do If Tests Fail

### If PDF doesn't download:
1. Check browser console for errors
2. Verify pdfmake is installed: `ls node_modules/pdfmake`
3. Check handleDownloadReport function is called (add console.log)

### If PDF is blank:
1. Check analyticsData is populated (console.log before generateReportPDF)
2. Verify pdfmake fonts loaded (check pdfMake.vfs exists)
3. Test with minimal PDF to isolate issue

### If backend errors appear:
1. Check backend logs: `tail -f /tmp/backend.log`
2. Verify endpoint exists: `curl http://localhost:8000/api/enterprise-users/reports/library`
3. Check database has reports: `psql -c "SELECT * FROM enterprise_reports;"`

---

## After Testing Complete

Once all tests pass, create final evidence:

1. **Take Screenshots:**
   - Reports tab loaded
   - Download success alert
   - PDF opened in Preview/Acrobat
   - Watermark visible
   - Real data in tables

2. **Create Evidence File:**
   - Document all test results
   - Include screenshots
   - Note any issues found and resolved
   - Mark Phase 1.6 as COMPLETE

3. **Update Todo List:**
   - Mark Phase 1.6 as completed
   - Move to Phase 2 (Priority 2 features)

---

**Testing Started:** [Your timestamp here]
**Testing Completed:** [To be filled]
**Status:** ⏳ IN PROGRESS
**Tester:** User
**Environment:** Local Development

---

## Quick Reference Commands

```bash
# Check if backend is running
curl http://localhost:8000/health

# Check if frontend is running
curl http://localhost:5174

# View backend logs
tail -f /Users/mac_001/OW_AI_Project/ow-ai-backend/logs/*.log

# Check database reports
psql -h localhost -U mac_001 -d owkai_pilot -c "SELECT id, title, download_count FROM enterprise_reports;"

# Restart backend if needed
cd /Users/mac_001/OW_AI_Project/ow-ai-backend
lsof -ti:8000 | xargs kill -9
python3 main.py &

# Restart frontend if needed
cd /Users/mac_001/OW_AI_Project/owkai-pilot-frontend
lsof -ti:5174 | xargs kill -9
npm run dev &
```

---

**Ready to Test!** 🧪

Open http://localhost:5174 and begin testing!
