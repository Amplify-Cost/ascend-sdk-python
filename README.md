# OW-AI Enterprise Frontend

Enterprise-grade React application for the OW-AI Platform, providing real-time authorization management, alert monitoring, and governance controls.

## Table of Contents

- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Features](#features)
- [Documentation](#documentation)
- [Development](#development)
- [Production Deployment](#production-deployment)
- [Testing](#testing)

## Quick Start

### Prerequisites

- Node.js 18+ and npm 9+
- Access to OW-AI Backend API
- Environment variables configured

### Installation

```bash
# Install dependencies
npm install

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Start development server
npm run dev
```

The application will be available at `http://localhost:5173`

### Environment Variables

```env
VITE_API_URL=https://pilot.owkai.app
VITE_API_VERSION=v1
VITE_ENABLE_ANALYTICS=true
VITE_ENVIRONMENT=production
```

## Architecture

### Technology Stack

- **Framework:** React 18+ with Vite
- **Styling:** Tailwind CSS
- **State Management:** React Context API + Custom Hooks
- **HTTP Client:** Fetch API with enterprise error handling
- **Authentication:** JWT Bearer Tokens + Cookie-based auth
- **Build Tool:** Vite 5+

### Project Structure

```
owkai-pilot-frontend/
├── docs/                    # Documentation
│   ├── architecture/        # Architecture diagrams and decisions
│   ├── components/          # Component documentation
│   ├── guides/             # Developer guides
│   └── api/                # API integration guides
├── public/                 # Static assets
├── src/
│   ├── assets/            # Images, fonts, icons
│   ├── components/        # React components
│   ├── config/            # Configuration files
│   ├── context/           # React context providers
│   ├── hooks/             # Custom React hooks
│   ├── services/          # API services
│   ├── utils/             # Utility functions
│   ├── App.jsx            # Root component
│   └── main.jsx           # Application entry point
├── .env                   # Environment variables
├── package.json           # Dependencies and scripts
├── vite.config.js         # Vite configuration
└── README.md              # This file
```

## Features

### 1. Authorization Management
- Real-time action approval workflows
- Multi-level authorization (1-5 approval levels)
- Risk-based routing (0-100 risk scoring)
- Enterprise audit trails
- Compliance mapping (SOX, PCI-DSS, HIPAA, GDPR)

### 2. Alert Management
- Real-time alert monitoring
- AI-powered threat intelligence
- Alert correlation and grouping
- Performance metrics dashboard
- Automated response capabilities

### 3. Smart Rules Engine
- Natural language rule creation
- AI-powered rule optimization
- Performance analytics
- Rule suggestions based on ML patterns

### 4. Governance & Compliance
- Policy management dashboard
- NIST/MITRE framework integration
- Unified governance controls
- Data rights management

### 5. Enterprise Features
- User management and RBAC
- SSO integration support
- Security reports and analytics
- Audit log visualization

## Documentation

### For Developers

- [Architecture Overview](./docs/architecture/OVERVIEW.md) - System architecture and design decisions
- [Component Library](./docs/components/README.md) - Comprehensive component documentation
- [Development Guide](./docs/guides/DEVELOPMENT.md) - Setup and development workflow
- [API Integration](./docs/api/INTEGRATION.md) - Backend API integration guide
- [Testing Guide](./docs/guides/TESTING.md) - Testing strategies and examples

### For Engineers

- [Frontend Architecture](./docs/architecture/FRONTEND-ARCHITECTURE.md) - Detailed technical architecture
- [State Management](./docs/architecture/STATE-MANAGEMENT.md) - How data flows through the application
- [Performance Optimization](./docs/guides/PERFORMANCE.md) - Performance best practices
- [Security Guidelines](./docs/guides/SECURITY.md) - Frontend security considerations

## Development

### Available Scripts

```bash
# Development server with hot reload
npm run dev

# Production build
npm run build

# Preview production build
npm run preview

# Run linter
npm run lint

# Fix linting issues
npm run lint:fix

# Run tests
npm test

# Run tests with coverage
npm run test:coverage
```

### Code Style

This project follows:
- ESLint configuration for code quality
- Prettier for code formatting
- React best practices and hooks rules
- Tailwind CSS utility-first approach

### Adding New Features

1. Create component in `src/components/`
2. Add corresponding tests in `src/components/__tests__/`
3. Update documentation in `docs/components/`
4. Follow naming conventions: PascalCase for components
5. Use functional components with hooks

## Production Deployment

### Build for Production

```bash
# Create optimized production build
npm run build

# Output will be in dist/ directory
# Deploy dist/ to your hosting provider
```

### Deployment Checklist

- [ ] Environment variables configured
- [ ] API endpoints point to production
- [ ] Analytics tracking enabled
- [ ] Error reporting configured
- [ ] Security headers configured
- [ ] Performance monitoring enabled
- [ ] CDN configured for assets

### Hosting Providers

Recommended hosting providers:
- **Railway** (Current production)
- Vercel
- Netlify
- AWS Amplify
- Azure Static Web Apps

## Testing

### Running Tests

```bash
# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Generate coverage report
npm run test:coverage
```

### Test Structure

- Unit tests for utilities: `src/utils/__tests__/`
- Component tests: `src/components/__tests__/`
- Integration tests: `src/test/integration/`
- E2E tests: `src/test/e2e/`

## Performance

### Optimization Features

- Code splitting and lazy loading
- Asset optimization (images, fonts)
- Tree shaking for minimal bundle size
- Service worker for offline capability
- CDN integration for static assets

### Current Metrics

- **Bundle Size:** ~995 kB (target: <500 kB)
- **First Contentful Paint:** <2s
- **Time to Interactive:** <3s
- **Lighthouse Score:** 85+

## Security

### Security Features

- JWT authentication with secure storage
- CSRF protection
- XSS prevention
- Content Security Policy headers
- Secure cookie handling
- Input sanitization
- Rate limiting on client side

### Security Best Practices

- Never commit `.env` files
- Rotate JWT tokens regularly
- Validate all user inputs
- Use HTTPS in production
- Keep dependencies updated
- Follow OWASP guidelines

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Contributing

1. Create feature branch from `main`
2. Make changes with clear commit messages
3. Add tests for new features
4. Update documentation
5. Submit pull request

### Commit Message Format

```
type(scope): description

feat(auth): add SSO integration
fix(alerts): resolve null check error
docs(api): update integration guide
```

## Troubleshooting

### Common Issues

**Issue:** `npm install` fails
- **Solution:** Clear npm cache: `npm cache clean --force`

**Issue:** Development server won't start
- **Solution:** Check port 5173 is not in use: `lsof -ti:5173`

**Issue:** API calls fail with CORS error
- **Solution:** Verify `VITE_API_URL` in `.env` matches backend CORS configuration

**Issue:** Build fails with memory error
- **Solution:** Increase Node memory: `NODE_OPTIONS=--max-old-space-size=4096 npm run build`

## License

Proprietary - OW-AI Enterprise Platform

## Support

- **Documentation:** [https://docs.owkai.app](https://docs.owkai.app)
- **API Reference:** [https://pilot.owkai.app/docs](https://pilot.owkai.app/docs)
- **Issues:** Contact engineering team

---

**Version:** 2.0.0
**Last Updated:** 2025-10-29
**Maintained by:** OW-AI Engineering Team
