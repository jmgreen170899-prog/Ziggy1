# ZiggyClean Authentication

## Overview
The ZiggyClean platform uses a mock authentication system for development and testing purposes. All features are protected behind a sign-in page.

## Default Credentials

### Administrator Access
- **Email**: `admin@ziggyclean.com` (or just `admin`)
- **Password**: `admin`

### Access Levels
- **Admin**: Full system access with administrative privileges
- **User**: Standard trading platform access (not implemented in mock)

## Environment Configuration

The authentication system is configured through environment variables in `.env.local`:

```bash
# Authentication Provider
NEXT_PUBLIC_AUTH_PROVIDER=mock

# Admin Access (enabled by default in development)
NEXT_PUBLIC_AUTH_ENABLE_ADMIN=true

# Session Configuration
NEXT_PUBLIC_AUTH_SESSION_TTL_MIN=43200  # 30 days
```

## Features

### Authentication Flow
1. **Unauthenticated users** are redirected to `/auth/signin`
2. **Authenticated users** accessing auth pages are redirected to dashboard
3. **Session persistence** using localStorage
4. **Auto-refresh** tokens before expiry

### Security Features
- Rate limiting on authentication attempts
- Security event logging
- Device session management
- Optional TOTP (Two-Factor Authentication)
- Password reset flow

### Protected Routes
All routes except authentication pages require authentication:
- `/auth/signin` - Sign in page
- `/auth/signup` - User registration
- `/auth/forgot-password` - Password reset
- `/auth/verify` - Email verification

## Mock Authentication Provider

The system uses a mock authentication provider (`mockAuthProvider.ts`) that:
- Simulates real authentication flows
- Stores data in memory/localStorage
- Provides realistic user experience
- Can be easily swapped with real API provider

## Development Notes

- Authentication is **required** to access any dashboard features
- The `forceShow` option on IntroGate has been removed
- The AuthGuard component handles all route protection
- Session state persists across browser refreshes
- Admin access is enabled by default in development mode

## Testing Authentication

1. Navigate to `http://localhost:3000`
2. You'll be redirected to the sign-in page
3. Use admin credentials: `admin` / `admin`
4. Successfully authenticated users see the dashboard

## Future Implementation

The mock provider can be replaced with a real authentication API by:
1. Creating a new provider implementing the same interface
2. Updating `NEXT_PUBLIC_AUTH_PROVIDER` to `'api'`
3. Configuring API endpoints in the new provider