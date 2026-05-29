---
title: Hermes Coder Assistant
emoji: 🤖
colorFrom: purple
colorTo: blue
sdk: gradio
sdk_version: 4.44.0
app_file: app.py
pinned: false
---

# 🤖 Hermes Coder Assistant

An AI-powered coding assistant that connects to **Hermes-2-Pro-Llama-3-8B** and your **GitHub repositories**.

## Features

- 🔗 **GitHub Integration**: Connect to any public or private GitHub repository
- 📁 **File Browser**: Navigate and explore codebases with an intuitive interface
- ✏️ **Code Editor**: View and edit files directly with syntax highlighting
- 💬 **AI Chat**: Ask Hermes questions about your codebase
- 🚀 **Direct Commits**: Save changes directly to GitHub
- 🤖 **Local AI**: Uses Hermes-2-Pro for code understanding (runs locally!)

## How to Use

### 1. Connect GitHub

Get a GitHub token from [github.com/settings/tokens](https://github.com/settings/tokens) with these scopes:
- `repo` - for private repositories
- `read:user` - for basic user info

Paste your token and click "Connect to GitHub"

### 2. Select a Repository

Choose any repository from your GitHub account using the dropdown menu.

### 3. Browse and Edit

- Navigate through folders by clicking on them
- Click on files to view their contents
- Edit code in the editor
- Click "Save Changes" to commit to GitHub

### 4. Chat with Hermes

Ask questions about your codebase:
- "What does this file do?"
- "Explain the project structure"
- "Help me fix this bug"
- "Write a test for this function"

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Hugging Face Space                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌─────────────┐     ┌──────────────┐     ┌───────────┐  │
│   │   Gradio   │────▶│ Hermes Model │◀────│  GitHub  │  │
│   │     UI     │     │  (Local)     │     │    API   │  │
│   └─────────────┘     └──────────────┘     └───────────┘  │
│         │                    │                     │        │
│         └────────────────────┴─────────────────────┘        │
│                         │                                   │
│                    Your Browser                             │
└─────────────────────────────────────────────────────────────┘
```

## Requirements

- **Model**: NousResearch/Hermes-2-Pro-Llama-3-8B (downloaded on first run)
- **GPU**: Recommended for faster inference (will run on CPU but slower)
- **RAM**: 16GB+ recommended for the full model

## Local Development

```bash
pip install -r requirements.txt
python app.py
```

Then open http://localhost:7860 in your browser.

## License

MIT License - See NousResearch/Hermes-Function-Calling for model licensing.

## Credits

- Model: [NousResearch/Hermes-2-Pro-Llama-3-8B](https://huggingface.co/NousResearch/Hermes-2-Pro-Llama-3-8B)
- Built with [Gradio](https://gradio.app/)
