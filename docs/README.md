# Vibe Dating Backend Documentation

Welcome to the Vibe Dating application documentation. This directory contains comprehensive technical documentation for the backend services and infrastructure.

## 📁 Documentation Structure

### Core Documentation
- **[System Architecture](./system-architecture.md)** - Complete system overview, infrastructure, and data design
- **[API Complete Reference](./api-complete-reference.md)** - All API endpoints and authentication
- **[Development Handbook](./development-handbook.md)** - Complete development setup and guidelines
- **[Service Implementations](./service-implementations.md)** - Detailed service specifications
- **[Frontend Integration Guide](./frontend-integration-guide.md)** - Frontend integration examples

### Additional Resources
- **[Deployment Operations](./deployment-operations.md)** - Deployment and operational procedures
- **[Troubleshooting](./troubleshooting.md)** - Common issues and solutions

### Legacy Documentation
- **[legacy/](./legacy/)** - Previous documentation versions (archived)

## 🚀 Quick Start

1. **New to the project?** Start with [System Architecture](./system-architecture.md)
2. **Setting up development?** See [Development Handbook](./development-handbook.md)
3. **Working with APIs?** Check [API Complete Reference](./api-complete-reference.md)
4. **Frontend integration?** Review [Frontend Integration Guide](./frontend-integration-guide.md)

## 🏗️ System Overview

Vibe is a location-based dating application designed as a Telegram Mini-App for the gay community. The backend uses:

- **AWS Serverless Architecture** (Lambda, API Gateway, DynamoDB, S3)
- **Single-table DynamoDB design** with 4 Global Secondary Indexes
- **Telegram WebApp authentication**
- **Agora.io for real-time communication**
- **Python 3.11+ backend framework**

### Data Hierarchy
```
User (1) → Profiles (1-3) → Media (0-5) [images/videos]
User (1) → Profiles (1-3) → Location History (many)
```

### Global Secondary Indexes
- **GSI1**: Profile lookup (USER → PROFILE)
- **GSI2**: Profile lookup alternative (PROFILE → USER)  
- **GSI3**: Time-based queries
- **GSI4**: Location-based queries

## 📋 Core Features

- **Multi-Profile Support**: Up to 3 profiles per user
- **Location Services**: Real-time location tracking with geohash
- **Media Management**: Images and short videos (max 5 per profile)
- **Real-time Communication**: Agora.io integration
- **Comprehensive Profile Attributes**: Dating-specific fields

## 🔒 Security & Privacy

- Profile data isolation
- Location precision control
- Media access validation
- GDPR compliance with TTL
- KMS encryption for all data
- JWT token authentication

## 📖 Documentation Standards

This documentation follows these principles:
- **Single Source of Truth**: Each topic covered in one primary document
- **Cross-References**: Clear links between related topics
- **Practical Examples**: Code samples and implementation guides
- **Up-to-Date**: Documentation maintained with code changes

## 🤝 Contributing

When updating documentation:
1. Update the primary document for the topic
2. Add cross-references where relevant
3. Update this README if adding new documents
4. Archive outdated documents to `legacy/`

## 📞 Support

For questions about this documentation or the Vibe Dating backend:
- Review relevant documentation section first
- Check [Troubleshooting](./troubleshooting.md) for common issues
- Consult the [Development Handbook](./development-handbook.md) for setup issues

---

*Last updated: $(date)*