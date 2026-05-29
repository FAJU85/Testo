# ⚡ Quick Start: GitHub → HuggingFace Auto-Sync

Get automatic synchronization working in **5 minutes**!

## Step 1: Create Your HuggingFace Space (2 min)

1. Go to https://huggingface.co/spaces
2. Click **"Create new Space"**
3. Fill in:
   - **Space name**: `my-app` (remember this!)
   - **License**: MIT
   - **SDK**: Choose your framework (Gradio, Streamlit, Docker, etc.)
4. Click **"Create Space"**

## Step 2: Get Your API Token (1 min)

1. Go to https://huggingface.co/settings/tokens
2. Click **"New token"**
3. Name: `github-sync`
4. Role: **Write** (important!)
5. Click **"Generate token"**
6. **COPY IT NOW** - you can't see it again! 🔑

## Step 3: Add GitHub Secrets (1 min)

1. In your GitHub repo, go to **Settings** → **Secrets and variables** → **Actions**
2. Click **"New repository secret"** three times:

```
Name: HF_TOKEN
Value: [paste your token from Step 2]

Name: HF_USERNAME  
Value: [your HF username]

Name: HF_SPACE_NAME
Value: [your space name, e.g., "my-app"]
```

## Step 4: Test It! (1 min)

1. Make any small change to a file
2. Commit and push to `main` branch
3. Go to **Actions** tab
4. Watch **"Sync to HuggingFace Space"** workflow run
5. Visit your Space: https://huggingface.co/spaces/YOUR_USERNAME/my-app

## ✅ Success Indicators

- ✅ Workflow shows green checkmark
- ✅ Your files appear in HuggingFace Space "Files" tab
- ✅ Space starts rebuilding with new code

## ❌ Something Wrong?

Check these common issues:

| Problem | Solution |
|---------|----------|
| Workflow doesn't start | Push to `main` or `master` branch |
| Authentication failed | Regenerate token with **Write** permission |
| Space not found | Check HF_SPACE_NAME is exact (no spaces!) |
| Permission denied | You must own the Space or have Write access |

## 🎯 That's It!

Every push to GitHub now automatically updates your HuggingFace Space. No manual uploads needed! 🚀

---

**Need more details?** See [HUGGINGFACE_SYNC_SETUP.md](./HUGGINGFACE_SYNC_SETUP.md) for full documentation.
