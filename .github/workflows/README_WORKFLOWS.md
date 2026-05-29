# GitHub Actions Workflows for HuggingFace Sync

This directory contains the automated workflows that sync your code to HuggingFace Space.

## Available Workflows

### 1. `sync-to-huggingface.yml` (Basic)
**Use this if:** You want simple, automatic sync on every push.

**Triggers:**
- Push to `main` branch
- Push to `master` branch

**Features:**
- Automatic file synchronization
- Basic error handling
- Clean commit messages

### 2. `sync-to-huggingface-advanced.yml` (Advanced) ⭐ RECOMMENDED
**Use this if:** You want production-grade sync with manual control.

**Triggers:**
- Push to `main`, `master`, or `develop` branches
- Manual trigger from GitHub Actions UI

**Features:**
- ✅ Skips sync if no changes detected
- ✅ Validates secrets before starting
- ✅ Retry logic (3 attempts) for reliability
- ✅ Manual force-sync option
- ✅ Detailed progress logging
- ✅ Post-sync verification
- ✅ Better error messages

## Which One Should I Use?

**Delete the basic workflow and keep only the advanced one** for production use:

```bash
# In your repository root
rm .github/workflows/sync-to-huggingface.yml
git add .github/workflows/sync-to-huggingface-advanced.yml
git commit -m "Use advanced HuggingFace sync workflow"
git push
```

Or rename the advanced workflow to replace the basic one:
```bash
mv .github/workflows/sync-to-huggingface-advanced.yml .github/workflows/sync-to-huggingface.yml
```

## How to Manually Trigger Sync (Advanced Workflow Only)

1. Go to **Actions** tab in GitHub
2. Click **"Sync to HuggingFace Space (Advanced)"**
3. Click **"Run workflow"** button
4. Select branch
5. Choose **"Force sync"** option if needed
6. Click **"Run workflow"**

## Required Secrets

Both workflows require these GitHub Secrets:

| Secret | Description |
|--------|-------------|
| `HF_TOKEN` | HuggingFace API token with Write permissions |
| `HF_USERNAME` | Your HuggingFace username |
| `HF_SPACE_NAME` | Your Space name (e.g., `my-app`) |

Add them in: **Settings** → **Secrets and variables** → **Actions**

## Troubleshooting

### Workflow Not Showing in Actions Tab
- Ensure the file is in `.github/workflows/` directory
- Check file extension is `.yml` or `.yaml`
- Verify YAML syntax is valid

### Workflow Fails Immediately
- Check all three secrets are set correctly
- Verify HF_TOKEN has Write permissions
- Ensure HuggingFace Space exists

### Sync Takes Too Long
- Check file sizes (large files slow down sync)
- Review exclusion patterns to skip unnecessary files
- Consider excluding `node_modules/`, `dist/`, etc.

## Customization Examples

### Add More Branches
Edit the `on.push.branches` array:
```yaml
on:
  push:
    branches:
      - main
      - master
      - develop
      - staging
      - production
```

### Run Tests Before Sync
Add a step before the sync job:
```yaml
- name: Run Tests
  run: |
    pip install -r requirements.txt
    pytest tests/ --tb=short
```

### Sync Only Specific Directories
Modify the rsync command:
```yaml
rsync -av \
  ./src/ hf_space_tmp/src/ \
  ./app.py hf_space_tmp/app.py
```

### Add Slack Notification
```yaml
- name: Notify Slack on Success
  if: success()
  uses: slackapi/slack-github-action@v1
  with:
    payload: |
      {
        "text": "✅ Synced to HuggingFace: ${{ github.sha }}"
      }
  env:
    SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK }}
```

## Monitoring Sync Status

### View Logs
1. Go to **Actions** tab
2. Click on the workflow run
3. Expand each step to see detailed logs

### Check Sync History
- Each successful sync creates a commit in HuggingFace Space
- Commit message format: `Auto-sync from GitHub: [SHA] - [commit message]`
- View history in your Space's **Files** tab

### Verify Files Synced
1. Visit your HuggingFace Space URL
2. Click **Files** tab
3. Compare with GitHub repository files

## Security Notes

- 🔒 Never commit tokens or secrets to the repository
- 🔒 All credentials must be stored as GitHub Secrets
- 🔒 Rotate HF_TOKEN every 90 days
- 🔒 Use minimum required permissions (Write, not Admin)
- 🔒 Review excluded files to prevent accidental leaks

## Performance Tips

- Keep workflow file in `.github/workflows/` (excluded from sync)
- Exclude large directories like `node_modules/`, `vendor/`
- Use `fetch-depth: 0` only when needed for git operations
- Enable caching for dependencies if running tests

---

**Need Help?** See the main documentation:
- Quick Start: `/QUICK_START_SYNC.md`
- Full Setup: `/HUGGINGFACE_SYNC_SETUP.md`
- Configuration: `/HUGGINGFACE_SYNC_CONFIG.md`
