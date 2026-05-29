# Changelog

All notable changes to the Hermes Coder Assistant project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Automatic GitHub to HuggingFace Space synchronization workflow
  - Syncs code on every push to `main` or `feature/hermes-coder-assistant` branches
  - Smart file filtering excludes build artifacts, caches, and sensitive files
  - Configurable via GitHub Secrets (HF_TOKEN, HF_USERNAME, HF_SPACE_NAME)
- Comprehensive documentation:
  - `HUGGINGFACE_SYNC_GUIDE.md` - Complete guide for auto-sync setup and troubleshooting
  - `DEPLOYMENT_CHECKLIST.md` - Step-by-step deployment verification checklist
- Environment variable configuration template (`.env.example`)
- Configurable model inference parameters via environment variables:
  - `TEMPERATURE` - Controls randomness in model output (default: 0.7)
  - `MAX_TOKENS` - Maximum tokens to generate (default: 512)
  - `TOP_P` - Nucleus sampling parameter (default: 0.9)
  - `HF_MODEL_NAME` - Custom model selection (default: NousResearch/Hermes-2-Pro-Llama-3-8B)

### Changed
- Updated sync workflow to use official `huggingface_hub` API instead of raw HTTP requests
- Moved hardcoded model parameters to environment variables for better flexibility
- Improved error handling and logging in sync workflow with emoji indicators
- Enhanced workflow to provide detailed upload progress and failure reporting

### Improved
- Auto-sync now uses industry-standard huggingface_hub library
- Better exclusion patterns prevent syncing unnecessary files
- More informative workflow logs for easier debugging
- Documentation covers common issues and solutions

## [1.0.0] - 2024-05-29

### Added
- Initial release of Hermes Coder Assistant
- GitHub integration for repository browsing and editing
- AI-powered chat using Hermes-2-Pro-Llama-3-8B model
- File editor with syntax highlighting
- Branch management capabilities
- Docker support for local deployment
- GitHub Actions CI/CD pipeline

---

**Legend:**
- **Added** - New features
- **Changed** - Changes in existing functionality
- **Deprecated** - Soon-to-be removed features
- **Removed** - Removed features
- **Fixed** - Bug fixes
- **Improved** - Performance or quality improvements
- **Security** - Security enhancements
