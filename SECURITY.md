# Security & Privacy

This document outlines the security measures and privacy considerations for ZiggyAI.

## Security Overview

### Authentication

**Current Implementation**: Mock Authentication (Development/Demo Mode)

- Uses local storage for session management
- No real user data is stored on servers
- Admin-only access by default (registration disabled)
- Mock credentials for development:
  - Admin: `admin@ziggyclean.com` / `admin`
  - Dev User: `user` / `user`

**Important Notes**:

- This is a **development/demo system** only
- Real production deployment requires proper authentication backend
- Passwords are not transmitted over network (mock system only)
- No sensitive user data is stored

### Data Protection

#### What is NOT Exposed

- ✅ No API keys in frontend code
- ✅ No secrets or credentials committed to repository
- ✅ .gitignore properly configured to exclude:
  - `.env` and `.env.*` files
  - `*.pem`, `*.key`, `*.p12` certificate files
  - Database files
  - Cache and temporary files

#### What Users Can See

- ✅ Portfolio data (only their own)
- ✅ Market quotes (public data)
- ✅ Trading signals generated for their portfolio
- ✅ News feed (public data)
- ✅ AI insights and recommendations

#### What Users Cannot See

- ✅ Other users' portfolios or data
- ✅ Backend API keys or credentials
- ✅ Server-side configuration
- ✅ Database contents outside their scope

### Privacy Considerations

#### Local Storage

The application stores the following in browser local storage:

- User session token (mock auth)
- User preferences (theme, sidebar state)
- Watchlist symbols
- Portfolio data cache

**User Control**:

- Users can clear this data by logging out
- Browser privacy settings control local storage
- No tracking cookies used

#### Data Collection

**What We Collect**:

- Portfolio positions (stored locally and on backend for authenticated users)
- Trading signals and preferences
- User feedback for AI improvement (optional)

**What We DON'T Collect**:

- Personal identifying information beyond email (in mock auth)
- Browsing history
- Third-party tracking data
- Financial account credentials

### Network Security

#### API Communication

- All API calls go through `/api` routes in Next.js
- Backend URL configurable via environment variables
- Default: `http://localhost:8000` (development)
- Production should use HTTPS

#### WebSocket Connections

- Real-time data via WebSocket (`ws://` in dev, `wss://` in production)
- Automatic reconnection on disconnect
- No sensitive data transmitted over WebSocket

### Environment Variables

**Frontend** (`.env.local`):

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
NEXT_PUBLIC_AUTH_PROVIDER=mock
NEXT_PUBLIC_DEV_BYPASS_AUTH=true  # Dev mode only
```

**Backend**:
See `backend/.env.example` for backend configuration

⚠️ **Never commit `.env` files to the repository**

### Access Control

#### Role-Based Access

- **Admin Role**: Full access including paper trading
- **User Role**: Standard access to portfolio, signals, market data
- **Unauthenticated**: Limited to public market data only

#### Paper Trading

- Only accessible to admin users
- Prevents accidental real money trading
- Practice mode for testing strategies

### Security Best Practices for Users

#### For Beginners

1. **Use Strong Passwords**: Even in dev mode, use secure passwords
2. **Log Out**: Always log out when using shared computers
3. **Private Browsing**: Consider using private/incognito mode
4. **Verify URLs**: Ensure you're on the correct domain (when deployed)

#### For Developers

1. **Environment Variables**: Never commit secrets to git
2. **API Keys**: Store in environment variables, not in code
3. **Dependencies**: Regularly update and audit npm packages
4. **HTTPS**: Always use HTTPS in production
5. **Rate Limiting**: Backend has rate limiting enabled
6. **Input Validation**: All user inputs are validated

### Vulnerability Reporting

If you discover a security vulnerability:

1. **Do NOT** open a public GitHub issue
2. Contact the administrator directly
3. Provide details:
   - Description of vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

### Compliance & Regulations

#### Financial Data

- Market data is sourced from public APIs
- No actual trading occurs through this platform (signals only)
- Users must use authorized brokers for real trades

#### Data Retention

- Mock auth data: Stored in browser only
- Portfolio data: Retained while user is active
- Logs: Retained for debugging purposes only

### Regular Security Audits

Recommended security checks:

- [ ] Weekly: Check for npm security vulnerabilities (`npm audit`)
- [ ] Monthly: Review access logs
- [ ] Quarterly: Update dependencies
- [ ] Annually: Security audit of codebase

### Security Features Implemented

✅ **Authentication**

- Session management
- Token-based auth (mock)
- Rate limiting on login attempts
- Security event logging

✅ **Data Protection**

- Local storage encryption (browser standard)
- HTTPS support (in production)
- Secure WebSocket connections

✅ **Access Control**

- Role-based permissions
- Route protection
- API authentication

✅ **Input Validation**

- All form inputs validated
- SQL injection prevention (ORM used)
- XSS prevention (React escaping)

✅ **Error Handling**

- No sensitive data in error messages
- Proper error boundaries
- Graceful fallbacks

### Known Limitations (Development Mode)

⚠️ **Current Limitations**:

1. Mock authentication is not production-ready
2. No email verification system
3. No 2FA/TOTP in production use
4. Local storage can be accessed by user (intentional for transparency)

🔒 **Production Requirements**:

1. Implement real authentication backend
2. Use HTTPS exclusively
3. Enable rate limiting
4. Add CSRF protection
5. Implement proper session management
6. Add database encryption at rest
7. Enable audit logging
8. Add security headers (CSP, HSTS, etc.)

### Security Headers (Production)

Recommended security headers:

```
Content-Security-Policy: default-src 'self'
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=(), microphone=(), camera=()
```

### Third-Party Dependencies

We minimize third-party dependencies and regularly audit:

- Chart libraries (Chart.js)
- Icon library (Lucide React)
- State management (Zustand)
- HTTP client (Axios)

All dependencies are vetted for security vulnerabilities.

### Secure Development Practices

1. **Code Review**: All changes reviewed before merge
2. **Testing**: Automated tests for critical paths
3. **Linting**: ESLint enforces security best practices
4. **TypeScript**: Type safety prevents common errors
5. **Dependency Management**: Regular updates and audits

### Data Backup

**User Responsibility**:

- Export portfolio data regularly
- Save important trading signals
- Keep records of significant trades

**System Backups** (Production):

- Database backups (daily)
- Configuration backups (on changes)
- Disaster recovery plan in place

---

## Summary

ZiggyAI takes security seriously while maintaining transparency for users:

✅ **No Hidden Data Collection**: Only what's needed for functionality
✅ **No Third-Party Tracking**: Your activity stays private  
✅ **Open Source**: Code is reviewable
✅ **User Control**: You can export and delete your data
✅ **Educational Focus**: Safe environment for learning trading

For production deployment, additional security measures must be implemented as outlined above.

---

_Last Updated: November 2025_
_Version: 1.0 (Development/Demo)_
