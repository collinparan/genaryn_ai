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

### Current Architecture
- **Type**: Static HTML/JavaScript single-page application
- **Deployment**: Digital Ocean Droplet (IP: 178.128.67.127)
- **Web Server**: Nginx serving from `/var/www/html`
- **Authentication**: Simple hardcoded credentials (admin/admin123)

### LLM Integration
- **Endpoint**: `https://w3af7ebiihzxumrnhjb2nh2o.agents.do-ai.run/api/v1/chat/completions`
- **Type**: OpenAI-compatible API
- **Model**: `gpt-oss-120b` (OpenAI GPT variant)
- **API Key**: `0ZO1hlXaU2TtJG2_j6_vQSTkjM1Ap4vH`
- **Key Feature**: Server-Sent Events (SSE) for streaming responses
- **JavaScript Fetch API**: Used for real-time chat streaming

### Frontend Architecture
```javascript
// SSE streaming pattern for chat responses
async function streamResponse(messages) {
    const response = await fetch(API_CONFIG.endpoint, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${API_CONFIG.apiKey}`
        },
        body: JSON.stringify({
            messages: messages,
            model: API_CONFIG.model,
            stream: true
        })
    });
    // Parse SSE data chunks for real-time display
}
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

### HTML/CSS
- Military green color palette (#6B7C32 primary, #4A5A1F dark, #8B9A5A light)
- Responsive design with CSS Grid and Flexbox
- Clean, minimalist military aesthetic
- Logo sizing: 400px for login screen, 60px for header (maintains header height)
- Classification banners at top and bottom

### JavaScript
- Vanilla JavaScript (no frameworks)
- Async/await for all API calls
- SSE handling for real-time streaming
- LocalStorage for session management
- Clean separation of concerns

### UI/UX Design
- Real-time word-by-word streaming display
- Clear user/assistant message distinction
- Military-appropriate visual hierarchy
- Download to Word document functionality
- Continue response capability

### Security
- Simple authentication (to be enhanced)
- Input sanitization for chat messages
- HTML entity escaping/unescaping for display
- CORS handled by nginx proxy
- XSS prevention in innerHTML usage

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

1. **Don't deploy to wrong directory** - Always use `/var/www/html/` (NOT `/var/www/genaryn-static/` which is deprecated)
2. **Don't trust user input** - Always validate and sanitize
3. **Don't break CSS** - Ensure no conflicting properties in styles
4. **Don't forget cache busting** - Add version query strings to assets
5. **Don't ignore military context** - Accuracy matters

## Deprecated Directories

**DO NOT USE**:
- `/var/www/genaryn-static/` - Old deployment directory (no longer served by nginx)
- Any Docker/container references - Project is now static HTML only

## Project Status

**Completed**:
- Static HTML/JavaScript single-page application
- Digital Ocean Droplet deployment
- Nginx web server configuration
- LLM integration with streaming responses
- Military green UI theme
- Basic authentication system
- Download to Word document feature
- Continue response functionality

**Current Issues**:
- Logo sizing needs adjustment (400px login, 60px header)
- Logout button implementation
- Login page refinements

**Planned**:
- Enhanced authentication system
- Advanced COA analysis
- Intelligence fusion capabilities
- Multi-user collaboration
- Production hardening
- Database backend for persistence

## Resources

- **Repository**: https://github.com/collinparan/genaryn_ai
- **Monty (Builder)**: https://github.com/collinparan/monty
- **Company**: https://genaryn.com
- **Contact**: contact@genaryn.com

## Key Commands

```bash
# Deployment
ssh root@178.128.67.127                      # Connect to server
scp index.html root@178.128.67.127:/var/www/html/  # Deploy HTML
scp genaryn_logo.svg root@178.128.67.127:/var/www/html/  # Deploy logo

# Server Management
sudo systemctl restart nginx                 # Restart nginx
sudo nginx -t                               # Test nginx config
tail -f /var/log/nginx/error.log           # View error logs
tail -f /var/log/nginx/access.log          # View access logs

# File Locations
/var/www/html/index.html                    # Main application file
/var/www/html/genaryn_logo.svg             # Logo file
/etc/nginx/sites-available/genaryn-static   # Nginx config

# Development
# Local testing: Open static-site/index.html in browser
# Make changes to static-site/index-fixed.html
# Deploy using scp command above
```

---

Remember: This system supports real military decision-making. Accuracy, reliability, and security are paramount. When in doubt, prioritize safety and auditability over features.