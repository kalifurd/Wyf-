# WYF* - What's Your Fantasy

An AI-powered interactive romance novel engine built with FastAPI and OpenRouter's Kimi K2 model.

## Overview

WYF* is a Victorian-era interactive romance narrative platform where users guide the story through choices and actions, while an AI narrator (the Caretaker) responds dynamically to create an immersive, emotionally engaging experience.

## Architecture

```
wyf-star/
├── server.py              # FastAPI application with API endpoints
├── static/
│   └── index.html         # Victorian Greenhouse POC frontend
├── prompts/
│   └── caretaker.txt      # AI narrator system prompt
├── docs/                  # Project specification and documentation
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── .gitignore            # Git ignore rules
└── README.md             # This file
```

## Quick Start

### Prerequisites
- Python 3.8+
- OpenRouter API key ([Get one here](https://openrouter.ai))

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/kalifurd/Wyf-.git
   cd Wyf-
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and add your OPENROUTER_API_KEY
   ```

5. **Run the server**
   ```bash
   python server.py
   ```

6. **Access the frontend**
   - Open your browser to `http://localhost:8000`
   - You should see the Victorian Greenhouse POC

## API Endpoints

### Health Check
```
GET /health
```
Returns API status and model configuration.

### Generate Response
```
POST /api/generate
Content-Type: application/json

{
  "prompt": "your action or response",
  "context": "current narrative context",
  "model": "kimi-k2"
}
```

Returns AI-generated narrative continuation.

## Features

✓ **Static File Serving** - Frontend served directly from `/static`  
✓ **CORS Support** - Local development friendly  
✓ **Environment Security** - API keys in `.env` (never committed)  
✓ **OpenRouter Integration** - Access to Kimi K2 AI model  
✓ **Caretaker Persona** - Sophisticated AI narrator with custom system prompt  
✓ **Victorian POC** - Immersive UI and narrative framework  

## Development

### File Structure Best Practices
- **Backend**: `server.py` - FastAPI application logic
- **Frontend**: `static/` - HTML/CSS/JS (served at `/static`)
- **AI Prompts**: `prompts/` - System prompts and persona definitions
- **Docs**: `docs/` - Specifications, architecture, and guidelines
- **Config**: `.env` - Environment variables (do not commit)

### Environment Variables
See `.env.example` for all available configuration options.

## Security Notes

⚠️ **Never commit `.env` to version control**  
⚠️ **Always use `.env.example` as a template**  
⚠️ **Regenerate API keys if accidentally exposed**  

## Troubleshooting

### "Cannot connect to API"
- Ensure server is running: `python server.py`
- Check that port 8000 is available
- Verify `http://localhost:8000/health` responds

### "OPENROUTER_API_KEY not found"
- Create `.env` file from `.env.example`
- Add your actual OpenRouter API key
- Restart the server

### CORS errors
- CORS is configured for local development
- For production, update allowed origins in `server.py`

## Next Steps

- [ ] Add narrative state management
- [ ] Implement user sessions and persistence
- [ ] Expand character system
- [ ] Add branching narrative trees
- [ ] Create admin interface for prompt management

## License

MIT

## Contributing

See `docs/` for technical specifications and contribution guidelines.

---

Built with ❤️ by the WYF* team
