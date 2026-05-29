# GitHub to HuggingFace Space Auto-Sync Guide

This document explains how the automatic synchronization between GitHub and HuggingFace Space works.

## Overview

When you push code to GitHub, a GitHub Action automatically syncs your files to your HuggingFace Space. This ensures both platforms stay in sync without manual intervention.

## How It Works

### 1. Trigger Conditions

The sync workflow is triggered when:
- You push to the `main` branch
- You push to the `feature/hermes-coder-assistant` branch
- You manually trigger the workflow from the Actions tab

### 2. What Gets Synced

✅ **Included Files:**
- All Python files (`.py`)
- Configuration files (`.txt`, `.yml`, `.json`, etc.)
- Documentation (`.md`)
- Docker files
- Shell scripts

❌ **Excluded Files:**
- `.git/` directory
- `__pycache__/` and compiled Python files
- Virtual environments (`.env`, `.venv`, `venv/`)
- IDE settings (`.vscode/`, `.idea/`)
- Log files
- Model cache and binary files (`.bin`, `.safetensors`)
- Temporary files

### 3. Required Secrets

You need to configure these secrets in your GitHub repository:

1. Go to your GitHub repository → Settings → Secrets and variables → Actions
2. Add the following secrets:

| Secret Name | Description | Example Value |
|-------------|-------------|---------------|
| `HF_TOKEN` | Your HuggingFace access token | `hf_xxxxx...` |
| `HF_USERNAME` *(optional)* | Your HuggingFace username | `FAJU85` |
| `HF_SPACE_NAME` *(optional)* | Your Space name | `hermes-coder-assistant` |

### 4. Getting Your HuggingFace Token

1. Go to https://huggingface.co/settings/tokens
2. Click "Create new token"
3. Give it a name (e.g., "GitHub Sync")
4. Select role: **Write**
5. Copy the token and add it to GitHub secrets as `HF_TOKEN`

## Workflow File Location

The sync workflow is configured in:
```
.github/workflows/sync-to-huggingface.yml
```

## Manual Trigger

You can manually trigger a sync:

1. Go to the **Actions** tab in your GitHub repository
2. Select **"Sync to HuggingFace Space"** workflow
3. Click **"Run workflow"**
4. Select the branch
5. Click **"Run workflow"**

## Viewing Sync Logs

After pushing to GitHub:

1. Go to the **Actions** tab
2. Click on the running workflow
3. View the logs to see which files were synced
4. Check for any errors or warnings

## Troubleshooting

### Common Issues

#### 1. "Authentication failed"
- Verify your `HF_TOKEN` secret is correctly set
- Ensure the token has **Write** permissions
- Check if the token has expired (create a new one if needed)

#### 2. "Space not found"
- Verify `HF_USERNAME` and `HF_SPACE_NAME` are correct
- Ensure the Space exists on HuggingFace
- Check that you have write access to the Space

#### 3. "Permission denied"
- Make sure your HuggingFace token has Write permissions
- Verify you're the owner or have write access to the target Space

#### 4. Files not syncing
- Check the workflow logs for excluded file patterns
- Verify the workflow is triggered (check branch names)
- Ensure files aren't in `.gitignore`

### Checking Sync Status

The workflow output shows:
```
🔄 Starting sync to HuggingFace Space: FAJU85/hermes-coder-assistant
📁 Source directory: /home/runner/work/...
📄 Found 10 files to sync

  Uploading: app.py
  Uploading: requirements.txt
  ...

✅ Successfully synced 10 files
🌐 View your Space: https://huggingface.co/spaces/FAJU85/hermes-coder-assistant
```

## Customization

### Changing Excluded Patterns

Edit the `EXCLUDE_PATTERNS` set in the workflow file to add or remove file patterns:

```python
EXCLUDE_PATTERNS = {
    '.git', '.github', '__pycache__', 
    # Add your custom patterns here
    'my_custom_folder', '*.custom'
}
```

### Syncing Different Branches

To sync additional branches, edit the workflow trigger:

```yaml
on:
  push:
    branches:
      - main
      - feature/hermes-coder-assistant
      - develop  # Add your branch here
```

### Using a Different Source Directory

If your app is in a subdirectory, update the `SOURCE_DIR` environment variable:

```yaml
env:
  SOURCE_DIR: ${{ github.workspace }}/my-subdirectory
```

## Best Practices

1. **Keep tokens secure**: Never commit tokens to your repository
2. **Test before deploying**: Use manual triggers to test sync before pushing
3. **Monitor logs**: Check sync logs regularly for issues
4. **Use meaningful commits**: Clear commit messages help track changes in HuggingFace
5. **Backup important files**: Don't rely solely on auto-sync for critical data

## Integration with Development Workflow

### Recommended Flow

1. Make changes locally
2. Test your changes
3. Commit and push to GitHub
4. GitHub Actions automatically syncs to HuggingFace
5. Verify the Space updated successfully
6. Test the live Space

### CI/CD Pipeline Integration

The sync workflow can be extended to:
- Run tests before syncing
- Deploy only on successful test runs
- Notify on Slack/Discord after sync
- Create release tags automatically

## Support

For issues with the sync workflow:

1. Check the [GitHub Actions documentation](https://docs.github.com/en/actions)
2. Review the [HuggingFace Spaces docs](https://huggingface.co/docs/hub/spaces-sdks-gradio)
3. Check workflow logs for specific error messages
4. Verify all secrets are correctly configured

---

**Last Updated:** 2024
**Workflow Version:** 2.0.0
