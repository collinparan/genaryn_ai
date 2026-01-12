# CLAUDE.md - Genaryn AI Deputy Commander

This file provides context for AI assistants (like Claude) when working on the Genaryn AI Deputy Commander project.

## Project Overview

You are working on an AI-powered military decision support system that acts as a virtual Deputy Commander for defense and security operations. The system provides strategic advice, analyzes courses of action, and helps military leaders make data-informed decisions.

## Core Mission

**Tagline**: "Independent AI Judgment. Stronger Commander Decisions."

The system must:
1. Provide clear, actionable intelligence and recommendations
2. Support the Military Decision Making Process (MDMP)
3. Analyze multiple courses of action with risk assessments
4. Maintain operational security (OPSEC)
5. Create auditable decision logs for accountability

## Technical Context

### LLM Integration
- **Endpoint**: `https://w3af7ebiihzxumrnhjb2nh2o.agents.do-ai.run/api/v1/chat/completions`
- **Type**: OpenAI-compatible API
- **Model**: `gpt-oss-120b` (OpenAI GPT variant)
- **Key Feature**: Streaming responses for real-time interaction
- **No API Key Required**: Open endpoint

### Architecture Patterns
```python
# Always use async/await patterns
async def stream_chat(self, messages: list):
    async with self.client.stream(...) as response:
        async for line in response.aiter_lines():
            yield parse_sse(line)

# UUID primary keys for all models
id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

# Structured logging
logger = structlog.get_logger(__name__)
```

### Military System Prompt

When implementing AI responses, use this context:

```python
MILITARY_SYSTEM_PROMPT = """You are the Genaryn AI Deputy Commander, a strategic advisor for military operations.

Your role:
- Provide clear, actionable intelligence and recommendations
- Analyze multiple courses of action (COAs) with risk assessments
- Support the Military Decision Making Process (MDMP)
- Maintain operational security (OPSEC)
- Consider time constraints and resource limitations

Communication style:
- Be concise and direct
- Use military terminology appropriately
- Present information in priority order
- Clearly distinguish facts from assessments
- Provide confidence levels for assessments

Always consider:
- Mission objectives
- Commander's intent
- Available resources
- Enemy capabilities
- Terrain and weather
- Time constraints
"""
```

## Code Style Guidelines

### Python Backend
- Use type hints for all functions
- Follow PEP 8 with 88-character line limit (Black formatter)
- Async/await for all I/O operations
- Comprehensive error handling with structured logging
- Docstrings for all public methods

### Database
- UUID primary keys for all tables
- `created_at` and `updated_at` timestamps
- JSONB for flexible metadata fields
- Use Alembic for all schema changes
- Repository pattern for data access

### API Design
- RESTful endpoints with clear naming
- Pydantic schemas for validation
- Response models for all endpoints
- Proper HTTP status codes
- Comprehensive error messages

### Security
- JWT tokens with 15-minute expiry
- Refresh tokens in httpOnly cookies
- Input validation on all endpoints
- SQL injection prevention via SQLAlchemy
- XSS prevention in all outputs

## Military Domain Knowledge

### User Roles
1. **Commander**: Decision authority, full system access
2. **Staff Officer**: Create recommendations, analyze data
3. **Observer**: Read-only access for situational awareness

### Decision Concepts
- **COA (Course of Action)**: Potential plans or strategies
- **MDMP (Military Decision Making Process)**: Structured planning methodology
- **Risk Assessment**: Probability vs Impact matrix
- **Commander's Intent**: End state and purpose
- **OPSEC**: Operational security considerations

### Communication Patterns
- Clear, direct language
- Bottom Line Up Front (BLUF)
- Situation, Mission, Execution, Admin/Logistics, Command/Signal (SMEAC)
- Facts vs Assessments distinction
- Confidence levels for intelligence

## Development Workflow

### When Adding Features
1. Check existing patterns in similar files
2. Maintain async/await consistency
3. Add appropriate logging
4. Include unit tests
5. Update API documentation

### When Fixing Bugs
1. Add structured logging for debugging
2. Check for similar issues in other modules
3. Add regression tests
4. Document the fix in comments

### When Reviewing Code
- Ensure military terminology is correct
- Verify security measures are in place
- Check for proper async patterns
- Confirm logging is comprehensive
- Validate error handling

## Testing Priorities

1. **Security**: Authentication, authorization, input validation
2. **Core Functionality**: LLM integration, streaming, decisions
3. **Military Features**: COA analysis, risk assessment, MDMP
4. **Performance**: Response times, concurrent users, caching
5. **Reliability**: Error recovery, reconnection, data persistence

## Common Pitfalls to Avoid

1. **Don't use synchronous I/O** - Always async/await
2. **Don't trust user input** - Always validate
3. **Don't store sensitive data in logs** - Use structured logging
4. **Don't skip health checks** - Critical for Docker
5. **Don't ignore military context** - Accuracy matters

## Project Status

**Completed**:
- Docker infrastructure (PostgreSQL, Redis, Nginx)
- FastAPI application structure
- Database models and migrations
- LLM service integration with Digital Ocean

**In Progress**:
- JWT authentication system
- WebSocket real-time chat
- Frontend React application
- Military decision frameworks

**Planned**:
- Advanced COA analysis
- Intelligence fusion capabilities
- Multi-user collaboration
- Production hardening

## Resources

- **Repository**: https://github.com/collinparan/genaryn_ai
- **Monty (Builder)**: https://github.com/collinparan/monty
- **Company**: https://genaryn.com
- **Contact**: contact@genaryn.com

## Key Commands

```bash
# Development
docker-compose up -d          # Start all services
docker-compose logs -f api    # View API logs
docker exec -it genaryn_api_1 bash  # Enter container

# Database
alembic upgrade head          # Run migrations
alembic revision -m "message" # Create migration

# Testing
pytest tests/                 # Run all tests
pytest --cov=app tests/       # With coverage
```

---

Remember: This system supports real military decision-making. Accuracy, reliability, and security are paramount. When in doubt, prioritize safety and auditability over features.