cd ~/OW_AI_Project/codebase-review

cat > DEMO-PREPARATION-PROMPT.md << 'EOF'
# OW-AI Platform Demo Preparation - Complete Context

## 🎯 MY GOAL
I need to record a professional demo video of my OW-AI Platform showing it working in a production-like environment. I have zero technical experience, so I need step-by-step instructions explained in simple terms.

## 📋 WHAT IS OW-AI PLATFORM?

**OW-AI Platform** is an enterprise AI governance and authorization system that monitors and controls AI agents and MCP (Model Context Protocol) servers in real-time.

### What It Does
- **Intercepts** AI agent actions before they execute
- **Evaluates** them against security policies using RBAC (Role-Based Access Control)
- **Approves or blocks** actions based on risk level
- **Generates smart rules** using AI to automatically create security policies
- **Manages alerts** when suspicious activity is detected
- **Provides real-time monitoring** dashboard

### Real-World Use Case
Imagine a company using AI agents to help employees. The OW-AI Platform sits in the middle and ensures:
- Agents can't access sensitive data without approval
- High-risk actions (like deleting files) require human approval
- Suspicious behavior triggers automatic alerts
- All actions are logged for compliance

## 🏗️ SYSTEM ARCHITECTURE

### Backend (FastAPI/Python)
- **Location:** `~/OW_AI_Project/ow-ai-backend`
- **Database:** AWS RDS PostgreSQL (production database)
- **API:** 167 REST endpoints
- **Status:** 100% functional (27/27 critical endpoints working)

### Frontend (React)
- **Location:** `~/OW_AI_Project/ow-ai-frontend`
- **Components:** 52 React components
- **Features:** Dashboard, Authorization Center, Alert Management, Smart Rules UI

### Key Features to Demo
1. **Authorization Center** - Real-time policy evaluation and approval workflows
2. **Smart Rules Engine** - AI-powered rule generation from natural language
3. **Alert Management System** - Real-time alert processing and actions
4. **RBAC System** - Role-based access control (Admin, Security Analyst, Approver, Viewer)

## 📊 CURRENT STATUS

**Platform Health:** 100% ✅  
**Last Updated:** October 12, 2025  
**Recent Fixes:** All 3 minor issues resolved in 1.5 hours
- ✅ Database tables created
- ✅ Smart rules optimization working
- ✅ Analytics endpoints enabled

**Documentation Available:**
- Complete platform review (93% → 100% health score)
- Comprehensive test results (27 endpoints tested)
- Fix instructions and evidence
- Frontend/backend analysis reports

**Location of Documentation:**
~/OW_AI_Project/codebase-review/
├── html-reports/          # HTML versions of all reports
├── pdf-reports/           # PDF versions
├── FIXES-APPLIED.md       # Recent fixes documentation
└── test-evidence/         # API test results

## 🎬 WHAT I NEED FOR THE DEMO

### 1. Clean Demo Environment
- Clear existing data from database (old test data)
- Create fresh demo data that shows realistic scenarios
- Set up demo users with different roles (Admin, Analyst, etc.)
- Populate demo alerts showing security events
- Create sample policies for authorization testing

### 2. Production-Like Test Scenario
I need the platform to work as if it's in a real company:
- Simulate MCP servers or AI agents trying to perform actions
- Show interception - the platform catching these actions
- Show evaluation - checking against policies in real-time
- Show decision - approve/block/require approval
- Show alerts - when suspicious activity happens

### 3. Demo Flow (What to Show)

**Scenario:** A company monitors AI agents helping employees

**Part 1: Authorization Center (5 min)**
- AI agent tries to access customer database
- Platform intercepts the request
- Shows real-time policy evaluation
- Risk score calculated
- Approval workflow triggered
- Admin approves/denies the request

**Part 2: Smart Rules Engine (3 min)**
- Admin types: "Block any file deletion on production servers"
- AI generates a smart rule automatically
- Shows the rule in natural language + technical condition
- Applies the rule
- Tests it working

**Part 3: Alert Management (3 min)**
- Unusual activity detected (e.g., agent accessing files at 3 AM)
- Alert automatically generated
- Shows in dashboard
- Admin reviews and acknowledges
- Shows correlation with other alerts

**Part 4: RBAC Demo (2 min)**
- Login as different users (Admin vs Analyst)
- Show different permissions
- Admin can approve, Analyst can only view
- Shows audit trail of who did what

## 🛠️ TECHNICAL DETAILS YOU NEED TO KNOW

### Backend Server
- **Port:** 8000
- **Start command:** `uvicorn main:app --reload --host 0.0.0.0 --port 8000`
- **Location:** `~/OW_AI_Project/ow-ai-backend`
- **Status check:** `curl http://localhost:8000/health`

### Frontend App
- **Port:** 3000 (typically)
- **Start command:** `npm start` or `yarn start`
- **Location:** `~/OW_AI_Project/ow-ai-frontend`

### Database
- **Type:** PostgreSQL on AWS RDS
- **Connection:** Configured in `.env` file
- **Admin user:** admin@owkai.com / admin123

### Key API Endpoints
- `POST /auth/token` - Login
- `POST /api/authorization/policies/evaluate-realtime` - Policy evaluation
- `GET /alerts` - Get alerts
- `POST /api/smart-rules/generate-from-nl` - Generate rules from text
- `POST /alerts/{id}/acknowledge` - Acknowledge alert

## 📁 WHERE TO FIND CODE/INFO

**If you need to understand how something works:**
1. Backend code: `~/OW_AI_Project/ow-ai-backend/`
   - Routes: `routes/` folder
   - Models: `models.py`
   - Main app: `main.py`

2. Frontend code: `~/OW_AI_Project/ow-ai-frontend/src/`
   - Components: `components/` folder
   - Pages: `pages/` folder

3. Documentation: `~/OW_AI_Project/codebase-review/`
   - All reports in HTML/PDF format
   - Test evidence for each endpoint
   - Complete feature inventory

## 🎯 WHAT I NEED FROM YOU

1. **Step-by-step setup instructions** in simple terms
   - How to clear the database for fresh demo
   - How to create demo data (users, policies, alerts)
   - How to start both backend and frontend
   - How to verify everything is working

2. **Demo script** with exact steps to follow
   - What to click
   - What to type
   - What to show
   - What to explain

3. **Troubleshooting guide** in case something doesn't work
   - Common issues and fixes
   - How to restart services
   - How to check logs

4. **Test scenario setup**
   - How to simulate an MCP server/agent making requests
   - How to trigger alerts
   - How to show the interception working

## ⚠️ IMPORTANT NOTES

- I'm on macOS
- Backend server runs on port 8000
- I can run terminal commands but need them explained
- I have Python, Node.js, and PostgreSQL tools installed
- The platform is currently 100% functional
- All code and documentation is available for review

## 🎥 RECORDING REQUIREMENTS

- Need to record ~15 minutes
- Should look professional for potential clients
- Must show all 4 key features clearly
- Should demonstrate real-world use case
- Need clean, fresh data (no test junk)

## 💭 QUESTIONS TO ADDRESS

1. How do I create a realistic demo environment?
2. How do I simulate AI agents making requests?
3. What demo data makes the most sense?
4. How do I make alerts appear at the right time?
5. What's the best order to demonstrate features?
6. How do I reset if something goes wrong during recording?

---

**READY TO START:** Please provide detailed, beginner-friendly instructions to prepare and record this demo. Assume I know nothing about web development, APIs, or databases. Explain everything step-by-step like I'm learning for the first time!
EOF

echo "✅ Demo preparation prompt created!"
echo ""
echo "📋 File location: ~/OW_AI_Project/codebase-review/DEMO-PREPARATION-PROMPT.md"
echo ""
echo "Now copying to clipboard..."
cat DEMO-PREPARATION-PROMPT.md | pbcopy
echo "✅ Copied to clipboard!"
echo ""
echo "📌 Next steps:"
echo "1. The file is created and saved"
echo "2. The content is in your clipboard"
echo "3. Ready to proceed with demo preparation!"

exit

q

