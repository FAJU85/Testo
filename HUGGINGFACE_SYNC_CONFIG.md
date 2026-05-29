# HuggingFace Sync Configuration

This document tracks the configuration state for GitHub → HuggingFace Space automatic synchronization.

## 🔐 Required GitHub Secrets

| Secret Name | Description | Where to Get | Status |
|-------------|-------------|--------------|--------|
| `HF_TOKEN` | HuggingFace API token with Write permissions | [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens) | ⬜ Not Set |
| `HF_USERNAME` | Your HuggingFace username | Your HF profile URL | ⬜ Not Set |
| `HF_SPACE_NAME` | The name of your Space (not full URL) | Your Space URL path | ⬜ Not Set |

## ✅ Setup Checklist

- [ ] HuggingFace Space created
- [ ] Access token generated with Write permissions
- [ ] All three secrets added to GitHub repository
- [ ] Workflow file committed to `.github/workflows/`
- [ ] Test push performed successfully
- [ ] Verified files appear in HuggingFace Space

## 📊 Sync History

| Date | Commit Hash | Status | Files Synced | Notes |
|------|-------------|--------|--------------|-------|
| - | - | - | - | No syncs yet |

## 🔧 Current Configuration

**Synced Branches:** `main`, `master`  
**Excluded Paths:** 
- `.github/**`
- `README.md`
- `*.md`
- `.gitignore`

**File Exclusions (rsync):**
- `.git/`
- `.github/`
- `__pycache__/`
- `*.pyc`
- `.env`
- `*.log`
- `hf_space_tmp/`

## 🚨 Common Issues & Solutions

### Issue: "Authentication failed"
**Solution:** Verify HF_TOKEN has Write permissions and is not expired

### Issue: "Repository not found"
**Solution:** Check HF_USERNAME and HF_SPACE_NAME match exactly (case-sensitive)

### Issue: "Permission denied"
**Solution:** Ensure you own the Space or have Write access

### Issue: Workflow not triggering
**Solution:** Verify push is to `main` or `master` branch, check Actions are enabled

## 📝 Manual Sync Command (Emergency Use)

If automatic sync fails, you can manually sync using:

```bash
# Clone both repositories
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git github_repo
git clone https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME hf_space

# Sync files
rsync -av --exclude='.git' \
          --exclude='.github/' \
          --exclude='__pycache__/' \
          --exclude='*.pyc' \
          --exclude='.env' \
          --exclude='*.log' \
          ./github_repo/ ./hf_space/

# Commit and push to HF
cd hf_space
git add -A
git commit -m "Manual sync from GitHub"
git push
```

## 🔄 Version Tracking

- **Workflow Version:** 1.0.0
- **Last Updated:** 2024
- **Schema:** GitHub Actions YAML v1

---

**Note:** This configuration file should be kept in sync with the actual workflow file. Any changes to exclusion patterns or sync behavior should be documented here.
