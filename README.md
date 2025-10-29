# OW-AI Enterprise Platform

Enterprise-grade AI authorization and governance platform providing real-time policy evaluation, multi-level approval workflows, and comprehensive security controls.

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Documentation](#documentation)
- [Development](#development)
- [Deployment](#deployment)
- [Security](#security)

## 🎯 Overview

The OW-AI Platform is an enterprise authorization and governance system that provides:

- **Real-time Authorization Management** - Multi-level approval workflows with risk-based routing
- **AI-Powered Alert System** - Intelligent threat detection and automated response
- **Smart Rules Engine** - Natural language rule creation with ML optimization
- **Governance & Compliance** - SOX, PCI-DSS, HIPAA, GDPR compliance mapping
- **Enterprise Security** - JWT authentication, RBAC, audit trails, and SSO support

### Key Features

✅ Multi-level authorization workflows (1-5 approval levels)
✅ Real-time risk assessment (0-100 scoring)
✅ AI-powered threat intelligence
✅ Natural language policy creation
✅ Comprehensive audit trails
✅ Enterprise SSO integration
✅ NIST/MITRE framework mapping
✅ Real-time performance analytics

## 🏗️ Architecture

### System Components

```
ow-ai-platform/
├── ow-ai-backend/          # FastAPI backend
├── owkai-pilot-frontend/    # React frontend
└── enterprise-docs/         # Comprehensive documentation
```

### Technology Stack

**Backend:**
- Python 3.13+ with FastAPI
- PostgreSQL 14+ database
- Alembic for migrations
- JWT authentication (RS256)
- OpenAI integration for ML features

**Frontend:**
- React 18+ with Vite
- Tailwind CSS for styling
- Context API for state management
- Fetch API for HTTP requests

**Infrastructure:**
- AWS (ECS, RDS, Secrets Manager) for deployment
- PostgreSQL on AWS RDS for data persistence
- AWS Secrets Manager for credentials management

## 🚀 Quick Start

### Prerequisites

- Python 3.13+
- Node.js 18+
- PostgreSQL 14+
- Git

### Backend Setup

```bash
# Navigate to backend
cd ow-ai-backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Run database migrations
alembic upgrade head

# Start development server
python main.py
```

Backend will be available at `http://localhost:8000`
API documentation: `http://localhost:8000/docs`

### Frontend Setup

```bash
# Navigate to frontend
cd owkai-pilot-frontend

# Install dependencies
npm install

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Start development server
npm run dev
```

Frontend will be available at `http://localhost:5173`

### Default Credentials

```
Email: admin@owkai.com
Password: OWAdmin2024!Secure
```

**⚠️ Change these credentials immediately in production!**

## 📁 Project Structure

```
OW_AI_Project/
│
├── ow-ai-backend/                  # Backend Application
│   ├── routes/                     # API route handlers
│   ├── models/                     # Database models
│   ├── schemas/                    # Pydantic schemas
│   ├── services/                   # Business logic
│   ├── core/                       # Core utilities
│   ├── security/                   # Security modules
│   ├── enterprise-docs/            # API documentation
│   ├── alembic/                    # Database migrations
│   ├── main.py                     # Application entry point
│   └── requirements.txt            # Python dependencies
│
├── owkai-pilot-frontend/           # Frontend Application
│   ├── src/
│   │   ├── components/            # React components (60+)
│   │   ├── services/              # API services
│   │   ├── hooks/                 # Custom React hooks
│   │   ├── context/               # Context providers
│   │   └── utils/                 # Utility functions
│   ├── docs/                      # Frontend documentation
│   ├── public/                    # Static assets
│   └── package.json               # Dependencies
│
└── enterprise-docs/                # Project-wide Documentation
    ├── ENTERPRISE_REBUILD_PLAN.md
    └── INTEGRATION_REPORT.md
```

## 📖 Documentation

### Backend Documentation

- [API Reference](./ow-ai-backend/enterprise-docs/api/API-REFERENCE.md) - Complete API documentation
- [Architecture Overview](./ow-ai-backend/docs/architecture/ENTERPRISE_DOCUMENTATION.md)
- [Database Schema](./ow-ai-backend/docs/architecture/DATABASE_SCHEMA.md)

### Frontend Documentation

- [README](./owkai-pilot-frontend/README.md) - Frontend overview
- [API Integration](./owkai-pilot-frontend/docs/api/INTEGRATION.md) - Backend integration guide
- [Component Library](./owkai-pilot-frontend/docs/components/README.md) - Component documentation

### Project Reports

- [Enterprise Rebuild Plan](./ENTERPRISE_REBUILD_PLAN.md)
- [Integration Report](./INTEGRATION_REPORT_EXECUTIVE_SUMMARY.md)
- [Security Audit](./ENTERPRISE_SECURITY_AUDIT_FINAL_2025-10-24.md)

## 💻 Development

### Backend Development

```bash
cd ow-ai-backend
python main.py                      # Run development server
pytest                              # Run tests
alembic revision --autogenerate     # Create migration
alembic upgrade head                # Run migrations
```

### Frontend Development

```bash
cd owkai-pilot-frontend
npm run dev        # Development server
npm run build      # Production build
npm test           # Run tests
npm run lint:fix   # Lint and fix
```

### Git Workflow

```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Make changes and commit
git add .
git commit -m "feat(scope): description"

# Push to remote
git push origin feature/your-feature-name
```

## 🚢 Deployment

### Production URLs

- **Frontend:** https://pilot.owkai.app
- **Backend API:** https://pilot.owkai.app (AWS ECS)
- **API Docs:** https://pilot.owkai.app/docs

### Environment Variables

**Backend (.env):**
```env
DATABASE_URL=postgresql://user:pass@host:5432/dbname
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ALLOWED_ORIGINS=https://pilot.owkai.app
OPENAI_API_KEY=your-openai-key
```

**Frontend (.env):**
```env
VITE_API_URL=https://pilot.owkai.app
VITE_API_VERSION=v1
VITE_ENVIRONMENT=production
```

## 🔒 Security

### Authentication & Authorization

- JWT tokens with RS256 algorithm
- Cookie-based session management
- Role-Based Access Control (RBAC)
- Multi-factor authentication support

### Compliance

- SOX compliance controls
- PCI-DSS data handling
- HIPAA-compliant audit trails
- GDPR data rights management

### Security Best Practices

✅ Never commit `.env` files
✅ Rotate secrets regularly
✅ Use AWS Secrets Manager for production
✅ Keep dependencies updated
✅ Follow OWASP Top 10 guidelines
✅ Implement rate limiting
✅ Enable security headers
✅ Regular security audits

## 🧪 Testing

### Backend Tests

```bash
cd ow-ai-backend
pytest --cov=. --cov-report=html
```

### Frontend Tests

```bash
cd owkai-pilot-frontend
npm test -- --coverage
```

## 📝 License

Proprietary - OW-AI Enterprise Platform

## 🆘 Support

### Documentation

- [API Reference](./ow-ai-backend/enterprise-docs/api/API-REFERENCE.md)
- [Frontend Docs](./owkai-pilot-frontend/README.md)

### Contact

- **Engineering Team:** Contact via internal channels
- **Bug Reports:** Create issue in repository

## 🔄 Recent Updates

**2025-10-29**
- ✅ ARCH-002: API routing standardization complete
- ✅ Fixed all /api/* prefix issues
- ✅ Updated comprehensive documentation
- ✅ Enhanced alert AI endpoints

---

**Version:** 2.0.0
**Last Updated:** 2025-10-29
**Maintained by:** OW-AI Engineering Team
