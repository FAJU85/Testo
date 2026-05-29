---
title: Hermes Coder Assistant
emoji: ":robot:"
colorFrom: purple
colorTo: blue
sdk: gradio
sdk_version: 4.44.0
app_file: app.py
pinned: false
---

# Hermes Coder Assistant

An AI-powered coding assistant that connects **Hermes-2-Pro-Llama-3-8B** to your **GitHub repositories**. Browse, edit, and understand any codebase with AI assistance.

## Features

### GitHub Integration
- Connect to any public or private GitHub repository
- Browse files and folders with live navigation
- **Branch switching** - view and work on any branch
- **Search** - find files and code in your repository
- **Commits history** - view recent commits
- **Create branches** - easily create feature branches
- **Direct editing** - read, edit, and save files to GitHub

### AI-Powered
- Uses Hermes-2-Pro for intelligent code assistance
- Context-aware responses about your codebase
- Code analysis and explanations
- Runs locally on Hugging Face Spaces (free tier compatible!)

### File Editor
- Syntax highlighting for 50+ languages
- Read files from any GitHub repo
- Edit and save with automatic commits
- Delete files with confirmation

### Chat Interface
- Ask questions about your codebase
- Get code explanations and suggestions
- Multi-turn conversation support
- Model-aware context from your files

## Quick Start

### 1. Get a GitHub Token
Create one at github.com/settings/tokens with:
- `repo` - for private repository access
- `read:user` - for basic user info

### 2. Connect & Start Coding
1. Enter your GitHub token and click "Connect"
2. Select any repository from the dropdown
3. Browse files by clicking on them
4. Click "Read" to load file content
5. Edit in the code editor
6. Click "Save Changes" to commit to GitHub

### 3. Chat with Hermes
- Ask: "What does this file do?"
- Ask: "Help me fix this bug"
- Ask: "Explain the project structure"

## Architecture

```
+-----------------+
| Hugging Face    |
| Space           |
+----+------+-----+
|         |       |
|  Gradio | Hermes| GitHub
|   UI    | Model | API
|         |       |
+---------+-------+
```

## System Requirements

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| RAM | 8GB | 16GB+ |
| GPU | None (CPU works) | GPU for faster inference |
| Storage | 2GB | 20GB for model cache |

## Deployment

### Option 1: Hugging Face Spaces (Recommended)
1. Create a new Space at huggingface.co/new-space
2. Select "Import from GitHub"
3. Import this repository
4. Done! Your app will be live

### Option 2: Local Development
```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd hermes-coder-assistant
pip install -r requirements.txt
python app.py
```
Open http://localhost:7860 in your browser.

### Option 3: Docker
```bash
docker build -t hermes-coder .
docker run -p 7860:7860 hermes-coder
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `GITHUB_TOKEN` | Your GitHub personal access token |
| `HF_TOKEN` | Hugging Face token for model downloads |

## License

MIT License - See NousResearch/Hermes-Function-Calling for model licensing.

## Credits

- AI Model: NousResearch/Hermes-2-Pro-Llama-3-8B
- Built with Gradio
- Inspired by OpenHands
