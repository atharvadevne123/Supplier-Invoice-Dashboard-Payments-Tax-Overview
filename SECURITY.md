# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.0.x   | Yes       |

## Reporting a Vulnerability

Please **do not** open a public GitHub issue for security vulnerabilities.

Report them by email to **devneatharva@gmail.com** with:
- A description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if known)

You will receive a response within 72 hours. If the issue is confirmed, a patch will be released as soon as possible.

## Security Considerations

- Never commit `.env` files containing real credentials
- Always rotate database passwords in production
- Use HTTPS in production (reverse proxy via nginx or a cloud load balancer)
- The `DATABASE_URL` env var should reference a user with least-privilege access
