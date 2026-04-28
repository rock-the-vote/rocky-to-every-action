# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it privately rather than opening a public issue.

**Email:** civictech@rockthevote.org

Please include a description of the issue, steps to reproduce, and any relevant context. We will respond as quickly as possible and work with you to address the issue before any public disclosure.

## Scope

Security issues relevant to this project include:

- Exposure of voter PII in logs or run output
- Credential or API key leakage
- Bypass of the public repository enforcement check
- Vulnerabilities in the sync logic that could result in data being sent to unintended recipients

## Out of scope

- Vulnerabilities in third-party dependencies (Parsons, GitHub Actions) — report those upstream
- Issues that require physical access to a machine or GitHub account credentials
