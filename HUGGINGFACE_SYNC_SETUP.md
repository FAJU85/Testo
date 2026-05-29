# GitHub to HuggingFace Space Auto-Sync

This repository is configured to automatically sync all code changes to a HuggingFace Space whenever you push to the `main` or `master` branch.

## 🚀 How It Works

1. You push code changes to GitHub (`main` or `master` branch)
2. GitHub Actions workflow triggers automatically
3. Files are synced to your HuggingFace Space
4. Your Space updates live within 2-5 minutes

## 📋 Setup Instructions

### Step 1: Create a HuggingFace Space

1. Go to [huggingface.co/spaces](https://huggingface.co/spaces)
2. Click "Create new Space"
3. Choose your Space name (e.g., `my-awesome-app`)
4. Select the appropriate SDK (Gradio, Streamlit, Docker, etc.)
5. Set visibility (Public or Private)
6. Click "Create Space"

### Step 2: Generate HuggingFace Access Token

1. Go to [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
2. Click "New token"
3. Give it a name (e.g., `github-sync`)
4. Select **Write** permission role
5. Click "Generate token"
6. **Copy the token immediately** - you won't see it again!

### Step 3: Configure GitHub Secrets

1. Go to your GitHub repository
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret** three times to add:

| Secret Name | Value |
|-------------|-------|
| `HF_TOKEN` | Your HuggingFace access token (from Step 2) |
| `HF_USERNAME` | Your HuggingFace username |
| `HF_SPACE_NAME` | Your Space name (e.g., `my-awesome-app`, NOT the full URL) |

### Step 4: Verify Setup

1. Make a small change to any file in your repository
2. Commit and push to `main` or `master`
3. Go to **Actions** tab in GitHub
4. Watch the "Sync to HuggingFace Space" workflow run
5. Visit your HuggingFace Space to confirm the changes appeared

## 📁 What Gets Synced

✅ **Included:**
- All Python files
- Configuration files (`.yaml`, `.json`, `.toml`, etc.)
- Static assets (images, CSS, JS)
- Requirements files
- Dockerfiles

❌ **Excluded:**
- `.git/` directory
- `.github/` workflows (don't need to sync these)
- `__pycache__/` directories
- `*.pyc` files
- `.env` files (security)
- `*.log` files
- Markdown documentation files

## 🔧 Customization

### Change Synced Branches

Edit `.github/workflows/sync-to-huggingface.yml`:

```yaml
on:
  push:
    branches:
      - main
      - master
      - production  # Add your branch here
```

### Modify File Exclusions

Edit the `paths-ignore` section and `rsync` exclude patterns in the workflow file.

### Add Pre-Sync Steps

Add steps before the sync job to run tests, build assets, etc.:

```yaml
- name: Run Tests
  run: pytest tests/

- name: Build Assets
  run: npm run build
```

## 🐛 Troubleshooting

### Workflow Not Triggering

- Ensure you're pushing to `main` or `master` branch
- Check that Actions are enabled in repository settings
- Verify the workflow file is in `.github/workflows/` directory

### Authentication Failed

- Regenerate your HF_TOKEN with Write permissions
- Ensure HF_USERNAME is correct (case-sensitive)
- Check that HF_SPACE_NAME matches exactly (no spaces/typos)

### Sync Fails Silently

- Check the **Actions** tab for detailed logs
- Verify your HuggingFace Space exists and is accessible
- Ensure you have Write permissions on the Space

### Permission Denied on HuggingFace

- Make sure your token has **Write** permission
- Verify you're the owner or have write access to the Space
- Try regenerating the token

## 📊 Monitoring

- **GitHub Actions Tab**: View sync history, logs, and failures
- **HuggingFace Space**: Check the "Files" tab to see latest synced version
- **Commit History**: Each sync creates a commit with message "Auto-sync from GitHub: [commit-hash]"

## 🔒 Security Best Practices

1. **Never commit tokens** - Always use GitHub Secrets
2. **Rotate tokens regularly** - Regenerate HF_TOKEN every 90 days
3. **Limit token permissions** - Only grant Write access, not Admin
4. **Review excluded files** - Ensure sensitive files (.env, credentials) are excluded
5. **Monitor workflow runs** - Check for unexpected sync attempts

## 🆘 Support

If you encounter issues:

1. Check the [GitHub Actions documentation](https://docs.github.com/en/actions)
2. Review the [HuggingFace Hub library docs](https://huggingface.co/docs/huggingface_hub)
3. Examine workflow logs in the Actions tab
4. Verify all secrets are correctly configured

## 📝 Example Workflow Output

```
Starting file synchronization...
Cloning HuggingFace Space...
Found 15 files to sync
Uploading app.py... ✅
Uploading requirements.txt... ✅
Uploading utils/helpers.py... ✅
Committing changes...
Pushing to HuggingFace...
✅ Sync completed successfully!
🔗 View your Space at: https://huggingface.co/spaces/username/my-awesome-app
```

---

**License**: MIT  
**Maintained by**: GitHub Actions Automation
