# Deployment Checklist

Use this checklist to ensure your Hermes Coder Assistant is properly deployed to HuggingFace Spaces.

## Pre-Deployment Setup

### 1. GitHub Repository Configuration

- [ ] Repository is public or has appropriate access permissions
- [ ] `.github/workflows/sync-to-huggingface.yml` exists and is configured
- [ ] Branch protection rules allow GitHub Actions (if enabled)

### 2. HuggingFace Account Setup

- [ ] HuggingFace account created at https://huggingface.co
- [ ] HuggingFace Space created (type: Gradio)
- [ ] Space visibility set (public/private as needed)

### 3. Generate Access Tokens

#### GitHub Token
- [ ] Go to https://github.com/settings/tokens
- [ ] Create new token with scopes:
  - [ ] `repo` (for private repos)
  - [ ] `read:user` (for user info)
- [ ] Copy token securely

#### HuggingFace Token
- [ ] Go to https://huggingface.co/settings/tokens
- [ ] Create new token
- [ ] Select role: **Write**
- [ ] Copy token securely

### 4. Configure GitHub Secrets

Navigate to your GitHub repo → Settings → Secrets and variables → Actions

- [ ] Add `HF_TOKEN` secret
  - Name: `HF_TOKEN`
  - Value: Your HuggingFace access token
  - [ ] Save

- [ ] Add `HF_USERNAME` secret (optional)
  - Name: `HF_USERNAME`
  - Value: Your HuggingFace username (e.g., `FAJU85`)
  - [ ] Save

- [ ] Add `HF_SPACE_NAME` secret (optional)
  - Name: `HF_SPACE_NAME`
  - Value: Your Space name (e.g., `hermes-coder-assistant`)
  - [ ] Save

## Deployment Steps

### Option A: Import from GitHub (Recommended for New Spaces)

1. [ ] Go to https://huggingface.co/new-space
2. [ ] Select "Import from GitHub"
3. [ ] Choose your repository
4. [ ] Set Space type to **Gradio**
5. [ ] Click "Create Space"
6. [ ] Wait for initial build (~2-5 minutes)
7. [ ] Verify app loads successfully

### Option B: Manual Sync After Creating Empty Space

1. [ ] Create empty Gradio Space on HuggingFace
2. [ ] Make any commit to your GitHub repo
3. [ ] Go to GitHub Actions tab
4. [ ] Verify "Sync to HuggingFace Space" workflow runs
5. [ ] Check workflow logs for success
6. [ ] Visit your HuggingFace Space URL

## Post-Deployment Verification

### Functionality Tests

- [ ] Space loads without errors
- [ ] UI renders correctly (Gradio interface visible)
- [ ] Can enter GitHub token
- [ ] Can connect to GitHub
- [ ] Repository dropdown populates
- [ ] Can browse files
- [ ] Can read file content
- [ ] Model inference works (test chat)
- [ ] File editing works (if applicable)

### Performance Checks

- [ ] Initial model load time (< 2 minutes acceptable)
- [ ] Response time for chat queries (< 10 seconds)
- [ ] No memory errors in logs
- [ ] Space doesn't crash under normal use

### Security Verification

- [ ] `.env` file is NOT committed to repository
- [ ] Tokens are stored only in GitHub Secrets
- [ ] `.gitignore` includes sensitive files
- [ ] No hardcoded credentials in code

## Monitoring & Maintenance

### Regular Checks

- [ ] Monitor GitHub Actions for sync failures
- [ ] Check HuggingFace Space logs periodically
- [ ] Review disk usage on Space (Settings → Storage)
- [ ] Update dependencies monthly

### Updating Your Space

When you make changes to your code:

1. [ ] Commit changes to GitHub
2. [ ] Verify Actions workflow triggers
3. [ ] Check sync logs for errors
4. [ ] Test updated Space
5. [ ] Rollback if issues found (use git revert)

### Troubleshooting Common Issues

#### Space Won't Load
- [ ] Check HuggingFace Space logs (Settings → Logs)
- [ ] Verify `requirements.txt` has all dependencies
- [ ] Ensure `app.py` has no syntax errors
- [ ] Check for missing environment variables

#### Sync Workflow Fails
- [ ] Verify HF_TOKEN secret is valid
- [ ] Check token hasn't expired
- [ ] Ensure Space exists and is accessible
- [ ] Review workflow logs for specific error

#### Model Loading Errors
- [ ] Check available RAM on Space (Settings → Resources)
- [ ] Verify quantization is enabled (4-bit)
- [ ] Clear model cache if corrupted
- [ ] Consider upgrading Space hardware

## Resource Management

### HuggingFace Space Tiers

| Tier | CPU | RAM | GPU | Cost |
|------|-----|-----|-----|------|
| Basic | 2 vCPU | 16GB | None | Free |
| Upgraded | 4 vCPU | 32GB | None | ~$5/mo |
| GPU Small | 4 vCPU | 30GB | T4 | ~$0.60/hr |
| GPU Medium | 8 vCPU | 60GB | A10G | ~$1.50/hr |

**Recommendation:** Start with Basic (free tier). Upgrade if you experience:
- Frequent OOM (Out of Memory) errors
- Very slow model loading (> 5 minutes)
- Slow inference times (> 30 seconds per response)

### Optimizing for Free Tier

- [ ] Use 4-bit quantization (already configured)
- [ ] Limit `MAX_TOKENS` to 512-1024
- [ ] Clear model cache periodically
- [ ] Pause Space when not in use (saves hours)

## CI/CD Enhancements (Optional)

### Add Testing Before Deploy

- [ ] Create `tests/` directory
- [ ] Add unit tests for core functions
- [ ] Modify workflow to run tests before sync
- [ ] Only sync if tests pass

### Add Notifications

- [ ] Configure Slack notifications for workflow failures
- [ ] Set up Discord webhook for deployment alerts
- [ ] Email notifications for critical errors

### Automated Backups

- [ ] Schedule weekly Space backups
- [ ] Export configuration snapshots
- [ ] Maintain version tags in Git

## Support Resources

- **HuggingFace Docs**: https://huggingface.co/docs/hub/spaces
- **GitHub Actions Docs**: https://docs.github.com/en/actions
- **Gradio Docs**: https://gradio.app/docs/
- **Transformers Library**: https://huggingface.co/docs/transformers

---

**Last Updated:** 2024
**Version:** 1.0.0
