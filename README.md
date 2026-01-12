# Genaryn AI Deputy Commander

> **Independent AI Judgment. Stronger Commander Decisions.**

An AI-powered decision support system for defense and security operations, featuring an AI Deputy Commander that provides unbiased, data-informed insights to military leaders.

## 🎯 Overview

The Genaryn AI Deputy Commander is a strategic advisor designed for military operations, providing:
- Real-time decision support through conversational AI
- Course of Action (COA) analysis with risk assessments
- Military Decision Making Process (MDMP) integration
- Secure, auditable decision logging
- Multi-user collaboration with role-based access

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Git
- 4GB+ RAM available

### Installation

1. **Clone the repository**
```bash
git clone git@github.com:collinparan/genaryn_ai.git
cd genaryn_ai
```

2. **Configure environment**
```bash
cp .env.example .env
```

Edit `.env` and ensure the LLM endpoint is configured:
```
DO_LLM_ENDPOINT=https://w3af7ebiihzxumrnhjb2nh2o.agents.do-ai.run/api/v1/chat/completions
```

3. **Start the application**
```bash
docker-compose up -d
```

4. **Access the application**
- API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Frontend: http://localhost:3000 (when available)

## 🏗️ Architecture

### Tech Stack
- **Backend**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL with UUID primary keys
- **Cache**: Redis for session management
- **LLM**: Digital Ocean hosted model (OpenAI-compatible)
- **Frontend**: React + TypeScript + Vite
- **Infrastructure**: Docker Compose with Nginx reverse proxy

### Services
```yaml
- FastAPI (port 8000): Main application server
- PostgreSQL (port 5432): Primary database
- Redis (port 6379): Cache and session storage
- Nginx (port 80): Reverse proxy and load balancer
```

## 🔐 Security Features

- **JWT Authentication**: Secure token-based auth with refresh tokens
- **Role-Based Access**: Commander, Staff, Observer roles
- **Audit Logging**: All decisions tracked and logged
- **Rate Limiting**: API protection against abuse
- **Input Validation**: SQL injection and XSS prevention

## 🎖️ Military Features

### Decision Support
- **COA Analysis**: Compare multiple courses of action
- **Risk Assessment**: Evaluate risks for each decision
- **MDMP Integration**: Follows military decision-making process
- **Intelligence Fusion**: Combine multiple data sources

### User Roles
- **Commander**: Full access, final decision authority
- **Staff**: Create and analyze recommendations
- **Observer**: Read-only access for monitoring

## 📡 API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and receive JWT
- `POST /api/auth/refresh` - Refresh access token

### Chat & Decisions
- `POST /api/chat/completions` - Send message to AI Deputy
- `GET /api/conversations` - List conversations
- `GET /api/decisions` - View decision history
- `WebSocket /ws/chat` - Real-time chat with streaming

### Health & Monitoring
- `GET /health` - Service health check
- `GET /metrics` - Prometheus metrics

## 🔧 Development

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Testing
```bash
# Run unit tests
pytest tests/unit

# Run integration tests
pytest tests/integration

# Run with coverage
pytest --cov=app tests/
```

## 🌐 Environment Variables

Key configuration options in `.env`:

```bash
# LLM Configuration
DO_LLM_ENDPOINT=https://w3af7ebiihzxumrnhjb2nh2o.agents.do-ai.run/api/v1/chat/completions
LLM_MODEL=meta-llama/llama-3.2-3b-instruct

# Database
DATABASE_URL=postgresql://user:password@postgres:5432/genaryn

# Redis
REDIS_URL=redis://redis:6379

# Security
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15

# Application
APP_NAME="Genaryn AI Deputy Commander"
DEBUG=false
LOG_LEVEL=INFO
```

## 📚 Documentation

- [API Documentation](http://localhost:8000/docs) - Interactive API docs
- [CLAUDE.md](./CLAUDE.md) - AI assistant context and guidelines
- [Architecture Diagrams](./docs/architecture.md) - System design

## 🤝 Contributing

This project was built with [Monty](https://github.com/collinparan/monty), an autonomous AI development agent.

### Development Workflow
1. Create feature branch
2. Make changes following existing patterns
3. Run tests
4. Submit pull request

## 📄 License

Proprietary - Genaryn Corporation

## 🆘 Support

- **Email**: contact@genaryn.com
- **Phone**: 860.709.8051
- **Location**: Alexandria, VA 22314

## 🎯 Mission

Genaryn is redefining decision support for defense and security operations. Our AI Deputy Commander delivers unbiased, data-informed insights to help leaders make faster, more confident, and mission-ready decisions.

---

**Built with Monty** - Autonomous AI Development Agent
"Excellent..." - C. Montgomery Burns