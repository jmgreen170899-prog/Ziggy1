# SSL/HTTPS Configuration Guide for ZiggyAI Production

## Overview

This guide outlines the SSL certificate setup required for production deployment of ZiggyAI.

## SSL Certificate Options

### Option 1: Let's Encrypt (Recommended for most deployments)

```bash
# Install certbot
sudo apt-get install certbot

# Obtain certificate for your domain
sudo certbot certonly --standalone -d yourdomain.com -d api.yourdomain.com

# Certificates will be saved to:
# /etc/letsencrypt/live/yourdomain.com/fullchain.pem
# /etc/letsencrypt/live/yourdomain.com/privkey.pem
```

### Option 2: Commercial SSL Certificate

1. Purchase from a trusted CA (Comodo, DigiCert, etc.)
2. Generate CSR (Certificate Signing Request)
3. Install provided certificates

## Backend HTTPS Configuration

### FastAPI SSL Setup (main.py modification needed)

```python
import ssl

if __name__ == "__main__":
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain('/path/to/cert.pem', '/path/to/key.pem')

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=443,
        ssl_context=ssl_context
    )
```

## Frontend HTTPS Configuration

### Next.js Production Build

```javascript
// next.config.ts - Add HTTPS redirect
const nextConfig = {
  async redirects() {
    return [
      {
        source: "/(.*)",
        has: [
          {
            type: "header",
            key: "x-forwarded-proto",
            value: "http",
          },
        ],
        destination: "https://yourdomain.com/:path*",
        permanent: true,
      },
    ];
  },
};
```

## Docker Configuration with SSL

### docker-compose.yml modifications

```yaml
version: "3.8"
services:
  backend:
    volumes:
      - ./ssl:/app/ssl:ro
    environment:
      - SSL_CERT_PATH=/app/ssl/cert.pem
      - SSL_KEY_PATH=/app/ssl/key.pem
    ports:
      - "443:443"

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/ssl/certs:ro
```

## Security Headers Configuration

### Add to main.py

```python
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(TrustedHostMiddleware, allowed_hosts=["yourdomain.com", "*.yourdomain.com"])

# Security headers
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response
```

## Testing SSL Configuration

### Verify SSL Setup

```bash
# Test certificate validity
openssl x509 -in certificate.pem -text -noout

# Test HTTPS connection
curl -I https://yourdomain.com

# SSL Labs test (recommended)
# Visit: https://www.ssllabs.com/ssltest/
```

## Implementation Status

- [ ] Domain purchased and configured
- [ ] SSL certificate obtained
- [ ] Backend HTTPS configured
- [ ] Frontend HTTPS configured
- [ ] Security headers added
- [ ] SSL testing completed

## Notes

- Certificates need renewal (Let's Encrypt: 90 days)
- Set up auto-renewal with cron jobs
- Test SSL configuration before going live
- Consider CDN (Cloudflare) for additional security
