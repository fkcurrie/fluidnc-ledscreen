# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Reporting a Vulnerability

We take the security of FluidNC LED Screen Monitor seriously. If you discover a security vulnerability, please follow these steps:

1. **Do Not** disclose the vulnerability publicly until it has been addressed
2. Submit a detailed report to [security contact information]
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fixes (if any)
   - Your contact information

## Security Features

The FluidNC LED Screen Monitor implements several security measures:

1. **Error Handling**
   - Secure error messages that don't expose internal details
   - Stack traces logged server-side only
   - Generic error responses to clients

2. **Dependency Management**
   - Regular security updates via Dependabot
   - Latest secure versions of all dependencies
   - Automated dependency scanning

3. **Network Security**
   - WebSocket communication with FluidNC
   - No exposed sensitive endpoints
   - Secure connection handling

4. **Container Security**
   - Docker-based deployment
   - Minimal attack surface
   - Regular base image updates

## Security Updates

Security updates are handled through:
1. Dependabot alerts for dependency vulnerabilities
2. Regular security scans
3. Manual security reviews

## Best Practices

When using this project:
1. Keep dependencies updated
2. Use the latest stable version
3. Monitor security alerts
4. Follow deployment guidelines
5. Report security issues promptly

## Contact

For security-related issues, please contact [security@sfle.ca].
