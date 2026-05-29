"""
Hermes Coder Assistant - AI Coding Assistant with GitHub Integration
Built on Hugging Face Spaces with Hermes-2-Pro-Llama-3-8B
"""

import gradio as gr
import os
import json
import re
import requests
import torch
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from threading import Thread

# Hugging Face and Transformers
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

# GitHub API helpers
GITHUB_API = "https://api.github.com"

# Model configuration - moved to config for better maintainability
MODEL_NAME = os.getenv("HF_MODEL_NAME", "NousResearch/Hermes-2-Pro-Llama-3-8B")
MODEL_LOADED = False
MODEL = None
TOKENIZER = None
MODEL_LOAD_PROGRESS = {"status": "not_started", "message": ""}

# Inference configuration from environment variables
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "512"))
TOP_P = float(os.getenv("TOP_P", "0.9"))

def load_hermes_model():
    """Load Hermes model in background with progress tracking"""
    global MODEL, TOKENIZER, MODEL_LOADED, MODEL_LOAD_PROGRESS
    
    if MODEL_LOADED:
        return True
    
    try:
        MODEL_LOAD_PROGRESS["status"] = "loading"
        MODEL_LOAD_PROGRESS["message"] = "Initializing quantization config..."
        print("Loading Hermes model...")
        
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
        )
        
        MODEL_LOAD_PROGRESS["status"] = "downloading"
        MODEL_LOAD_PROGRESS["message"] = "Downloading model weights (this may take a few minutes on first run)..."
        print("Downloading model...")
        
        MODEL = AutoModelForCausalLM.from_pretrained(
            MODEL_NAME,
            trust_remote_code=True,
            return_dict=True,
            quantization_config=quantization_config,
            device_map="auto",
            attn_implementation="eager",
        )
        
        TOKENIZER = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
        TOKENIZER.pad_token = TOKENIZER.eos_token
        TOKENIZER.padding_side = "left"
        
        MODEL_LOADED = True
        MODEL_LOAD_PROGRESS["status"] = "ready"
        MODEL_LOAD_PROGRESS["message"] = "Model loaded successfully!"
        print("Hermes model loaded!")
        return True
    except Exception as e:
        MODEL_LOAD_PROGRESS["status"] = "error"
        MODEL_LOAD_PROGRESS["message"] = f"Error loading model: {str(e)}"
        print(f"Error loading model: {e}")
        return False

class GitHubClient:
    """GitHub API client for repository operations"""
    
    def __init__(self, token: str = None):
        self.token = token or os.getenv("GITHUB_TOKEN", "")
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        } if self.token else {}
    
    def get_user_info(self) -> Dict:
        """Get authenticated user info"""
        url = f"{GITHUB_API}/user"
        resp = requests.get(url, headers=self.headers)
        resp.raise_for_status()
        return resp.json()
    
    def get_repos(self, page: int = 1, per_page: int = 30) -> List[Dict]:
        """Get user's repositories"""
        url = f"{GITHUB_API}/user/repos"
        params = {"page": page, "per_page": per_page, "sort": "updated"}
        resp = requests.get(url, headers=self.headers, params=params)
        resp.raise_for_status()
        return resp.json()
    
    def get_repo(self, owner: str, repo: str) -> Dict:
        """Get repository details"""
        url = f"{GITHUB_API}/repos/{owner}/{repo}"
        resp = requests.get(url, headers=self.headers)
        resp.raise_for_status()
        return resp.json()
    
    def get_repo_contents(self, owner: str, repo: str, path: str = "") -> List[Dict]:
        """Get contents of a repository path"""
        url = f"{GITHUB_API}/repos/{owner}/{repo}/contents/{path}"
        resp = requests.get(url, headers=self.headers)
        resp.raise_for_status()
        return resp.json()
    
    def get_file_content(self, owner: str, repo: str, path: str) -> Tuple[str, str]:
        """Get file content and sha"""
        url = f"{GITHUB_API}/repos/{owner}/{repo}/contents/{path}"
        resp = requests.get(url, headers=self.headers)
        resp.raise_for_status()
        data = resp.json()
        import base64
        content = base64.b64decode(data["content"]).decode("utf-8")
        return content, data["sha"]
    
    def update_file(self, owner: str, repo: str, path: str, content: str, 
                    message: str, sha: str) -> Dict:
        """Update a file in the repository"""
        import base64
        url = f"{GITHUB_API}/repos/{owner}/{repo}/contents/{path}"
        data = {
            "message": message,
            "content": base64.b64encode(content.encode()).decode(),
            "sha": sha
        }
        resp = requests.put(url, headers=self.headers, json=data)
        resp.raise_for_status()
        return resp.json()
    
    def create_file(self, owner: str, repo: str, path: str, content: str, 
                    message: str) -> Dict:
        """Create a new file in the repository"""
        import base64
        url = f"{GITHUB_API}/repos/{owner}/{repo}/contents/{path}"
        data = {
            "message": message,
            "content": base64.b64encode(content.encode()).decode()
        }
        resp = requests.put(url, headers=self.headers, json=data)
        resp.raise_for_status()
        return resp.json()
    
    def delete_file(self, owner: str, repo: str, path: str, sha: str, 
                    message: str) -> Dict:
        """Delete a file from the repository"""
        url = f"{GITHUB_API}/repos/{owner}/{repo}/contents/{path}"
        data = {"message": message, "sha": sha}
        resp = requests.delete(url, headers=self.headers, json=data)
        resp.raise_for_status()
        return resp.json()
    
    def get_branches(self, owner: str, repo: str) -> List[Dict]:
        """Get repository branches"""
        url = f"{GITHUB_API}/repos/{owner}/{repo}/branches"
        resp = requests.get(url, headers=self.headers)
        resp.raise_for_status()
        return resp.json()
    
    def get_commits(self, owner: str, repo: str, per_page: int = 10) -> List[Dict]:
        """Get repository commits"""
        url = f"{GITHUB_API}/repos/{owner}/{repo}/commits"
        resp = requests.get(url, headers=self.headers, params={"per_page": per_page})
        resp.raise_for_status()
        return resp.json()
    
    def get_file_history(self, owner: str, repo: str, path: str) -> List[Dict]:
        """Get commit history for a specific file"""
        url = f"{GITHUB_API}/repos/{owner}/{repo}/commits"
        resp = requests.get(url, headers=self.headers, params={"path": path})
        resp.raise_for_status()
        return resp.json()


class HermesCoderAssistant:
    """Main application logic for Hermes Coder Assistant"""
    
    def __init__(self):
        self.github = None
        self.current_repo = None
        self.current_repo_info = {}
        self.current_path = ""
        self.current_branch = "main"
        self.file_contents = {}  # Cache for edited files
        self.conversation_history = []
        self.search_results = []
    
    def set_github_token(self, token: str) -> str:
        """Set GitHub token and verify with retry logic"""
        self.github = GitHubClient(token)
        max_retries = 3
        for attempt in range(max_retries):
            try:
                user = self.github.get_user_info()
                self.conversation_history = []
                return f"✅ Connected as: {user.get('login', 'Unknown')}"
            except requests.exceptions.RateLimitError:
                if attempt < max_retries - 1:
                    import time
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                self.github = None
                return f"❌ Rate limit exceeded. Please wait and try again."
            except Exception as e:
                self.github = None
                return f"❌ Connection failed: {str(e)}"
        return "❌ Connection failed after multiple attempts"
    
    def get_repositories(self) -> List[str]:
        """Get list of user's repositories"""
        if not self.github:
            return ["Please connect GitHub first"]
        try:
            repos = self.github.get_repos()
            return [f"{r['owner']['login']}/{r['name']}" for r in repos]
        except Exception as e:
            return [f"Error: {str(e)}"]
    
    def select_repository(self, repo_full_name: str) -> str:
        """Select a repository to work with"""
        if not self.github or repo_full_name == "Please connect GitHub first":
            return "Please connect GitHub first"
        try:
            self.current_repo = repo_full_name
            self.current_path = ""
            self.file_contents = {}
            self.search_results = []
            owner, repo = repo_full_name.split("/")
            
            # Get repo info including default branch
            self.current_repo_info = self.github.get_repo(owner, repo)
            self.current_branch = self.current_repo_info.get("default_branch", "main")
            
            contents = self.github.get_repo_contents(owner, repo)
            return self._format_directory_list(contents, "")
        except Exception as e:
            return f"Error: {str(e)}"
    
    def get_repo_info(self) -> str:
        """Get current repository info"""
        if not self.current_repo_info:
            return "No repository selected"
        try:
            info = self.current_repo_info
            desc = info.get("description", "No description")
            stars = info.get("stargazers_count", 0)
            forks = info.get("forks_count", 0)
            Lang = info.get("language", "Unknown")
            return f"📊 **{self.current_repo}**\n\n{desc or 'No description'}\n\n⭐ {stars} | 🍴 {forks} | 📝 {Lang}"
        except Exception:
            return "Error getting repo info"
    
    def get_branches_list(self) -> List[str]:
        """Get list of branches"""
        if not self.github or not self.current_repo:
            return ["No repository selected"]
        try:
            owner, repo = self.current_repo.split("/")
            branches = self.github.get_branches(owner, repo)
            return [b["name"] for b in branches]
        except Exception as e:
            return [f"Error: {str(e)}"]
    
    def switch_branch(self, branch: str) -> str:
        """Switch to a different branch"""
        if not self.github or not self.current_repo:
            return "No repository selected"
        try:
            self.current_branch = branch
            self.current_path = ""
            self.file_contents = {}
            owner, repo = self.current_repo.split("/")
            contents = self.github.get_repo_contents(owner, repo, headers={"ref": branch})
            return self._format_directory_list(contents, "")
        except Exception as e:
            return f"Error switching branch: {str(e)}"
    
    def search_in_repo(self, query: str, search_type: str = "code") -> str:
        """Search for files or code in the repository"""
        if not self.github or not self.current_repo:
            return "No repository selected"
        if not query.strip():
            return "Please enter a search query"
        
        try:
            owner, repo = self.current_repo.split("/")
            # Use GitHub search API
            url = f"{GITHUB_API}/search/code"
            params = {
                "q": f"{query} repo:{owner}/{repo}",
                "per_page": 20
            }
            resp = requests.get(url, headers=self.github.headers, params=params)
            resp.raise_for_status()
            results = resp.json()
            
            items = results.get("items", [])
            if not items:
                return f"No results found for: {query}"
            
            self.search_results = items
            lines = [f"🔍 Found {len(items)} results for '{query}':\n"]
            for item in items[:15]:
                lines.append(f"📄 {item['path']}")
            
            return "\n".join(lines)
        except Exception as e:
            return f"Search error: {str(e)}"
    
    def get_commits_list(self, limit: int = 10) -> str:
        """Get recent commits for current repo"""
        if not self.github or not self.current_repo:
            return "No repository selected"
        try:
            owner, repo = self.current_repo.split("/")
            commits = self.github.get_commits(owner, repo, per_page=limit)
            lines = [f"📜 Recent commits in {self.current_repo}:\n"]
            for commit in commits:
                msg = commit.get("commit", {}).get("message", "").split("\n")[0]
                author = commit.get("commit", {}).get("author", {}).get("name", "Unknown")
                date = commit.get("commit", {}).get("author", {}).get("date", "")[:10]
                sha = commit.get("sha", "")[:7]
                lines.append(f"• `{sha}` {msg} - {author} ({date})")
            return "\n".join(lines)
        except Exception as e:
            return f"Error fetching commits: {str(e)}"
    
    def create_branch(self, branch_name: str, from_branch: str = None) -> str:
        """Create a new branch"""
        if not self.github or not self.current_repo:
            return "No repository selected"
        if not branch_name.strip():
            return "Please enter a branch name"
        
        try:
            owner, repo = self.current_repo.split("/")
            base_branch = from_branch or self.current_branch
            
            # Get the SHA of the base branch's latest commit
            url = f"{GITHUB_API}/repos/{owner}/{repo}/git/ref/heads/{base_branch}"
            resp = requests.get(url, headers=self.github.headers)
            resp.raise_for_status()
            base_sha = resp.json()["object"]["sha"]
            
            # Create new branch
            url = f"{GITHUB_API}/repos/{owner}/{repo}/git/refs"
            data = {
                "ref": f"refs/heads/{branch_name}",
                "sha": base_sha
            }
            resp = requests.post(url, headers=self.github.headers, json=data)
            resp.raise_for_status()
            
            self.current_branch = branch_name
            return f"✅ Created branch '{branch_name}' from '{base_branch}'"
        except Exception as e:
            return f"Error creating branch: {str(e)}"
    
    def navigate_to_path(self, path: str) -> str:
        """Navigate to a specific path in the repository"""
        if not self.github or not self.current_repo:
            return "No repository selected"
        try:
            self.current_path = path
            owner, repo = self.current_repo.split("/")
            contents = self.github.get_repo_contents(owner, repo, path)
            return self._format_directory_list(contents, path)
        except Exception as e:
            return f"Error: {str(e)}"
    
    def read_file(self, filename: str) -> Tuple[str, str]:
        """Read a file's content"""
        if not self.github or not self.current_repo:
            return "", "No repository selected"
        
        # Determine full path
        if self.current_path:
            full_path = f"{self.current_path}/{filename}" if filename else self.current_path
        else:
            full_path = filename
        
        try:
            owner, repo = self.current_repo.split("/")
            content, sha = self.github.get_file_content(owner, repo, full_path)
            self.file_contents[full_path] = {"content": content, "sha": sha}
            
            # Add to conversation context
            self._add_to_context("file_read", full_path, content[:1000])
            
            return content, f"📄 {full_path}"
        except Exception as e:
            return "", f"Error reading file: {str(e)}"
    
    def save_file(self, filename: str, content: str) -> str:
        """Save changes to a file"""
        if not self.github or not self.current_repo:
            return "No repository selected"
        
        full_path = f"{self.current_path}/{filename}" if self.current_path else filename
        
        try:
            owner, repo = self.current_repo.split("/")
            
            # Get SHA for existing files
            if full_path in self.file_contents:
                sha = self.file_contents[full_path]["sha"]
                self.github.update_file(owner, repo, full_path, content, 
                                       f"Update {filename} via Hermes Coder", sha)
            else:
                self.github.create_file(owner, repo, full_path, content,
                                       f"Create {filename} via Hermes Coder")
            
            self._add_to_context("file_saved", full_path, content[:500])
            return f"✅ Saved: {full_path}"
        except Exception as e:
            return f"❌ Error saving: {str(e)}"
    
    def delete_file(self, filename: str) -> str:
        """Delete a file from the repository"""
        if not self.github or not self.current_repo:
            return "No repository selected"
        
        full_path = f"{self.current_path}/{filename}" if self.current_path else filename
        
        try:
            owner, repo = self.current_repo.split("/")
            content, sha = self.github.get_file_content(owner, repo, full_path)
            self.github.delete_file(owner, repo, full_path, sha, 
                                   f"Delete {filename} via Hermes Coder")
            return f"✅ Deleted: {full_path}"
        except Exception as e:
            return f"❌ Error deleting: {str(e)}"
    
    def ask_hermes(self, question: str) -> str:
        """Ask Hermes about the current repository/context"""
        if not question.strip():
            return ""
        
        self.conversation_history.append({"role": "user", "content": question})
        
        # Build context from current state
        context = self._build_context_string()
        
        # For now, provide helpful responses based on the context
        # In production, this would call the Hermes model
        response = self._generate_hermes_response(question, context)
        
        self.conversation_history.append({"role": "assistant", "content": response})
        return response
    
    def _build_context_string(self) -> str:
        """Build context string from current state"""
        parts = []
        
        if self.current_repo:
            parts.append(f"Repository: {self.current_repo}")
        
        if self.current_path:
            parts.append(f"Current path: {self.current_path}")
        
        if self.file_contents:
            parts.append("\nFiles in context:")
            for path, data in list(self.file_contents.items())[:5]:
                parts.append(f"\n--- {path} ---\n{data['content'][:500]}...")
        
        if self.conversation_history:
            parts.append("\nConversation history:")
            for msg in self.conversation_history[-5:]:
                parts.append(f"\n{msg['role']}: {msg['content'][:200]}...")
        
        return "\n".join(parts)
    
    def _add_to_context(self, action: str, path: str, content: str):
        """Add action to context for AI awareness"""
        self.conversation_history.append({
            "role": "system",
            "content": f"[{action}] {path}: {content}"
        })
    
    def _generate_hermes_response(self, question: str, context: str) -> str:
        """Generate response based on question and context using Hermes model"""
        global MODEL, TOKENIZER, MODEL_LOADED
        
        # Check if model is loaded
        if not MODEL_LOADED:
            # Try to load model
            status = load_hermes_model()
            if not status:
                return self._fallback_response(question, context)
        
        try:
            # Build prompt for Hermes
            prompt = self._build_hermes_prompt(question, context)
            
            # Tokenize and generate
            inputs = TOKENIZER(prompt, return_tensors="pt", truncation=True, max_length=2048)
            
            if hasattr(inputs, 'input_ids'):
                input_ids = inputs.input_ids.to(MODEL.device)
                attention_mask = inputs.attention_mask.to(MODEL.device) if 'attention_mask' in inputs else None
            else:
                input_ids = inputs.to(MODEL.device)
                attention_mask = None
            
            with torch.no_grad():
                outputs = MODEL.generate(
                    input_ids,
                    attention_mask=attention_mask,
                    max_new_tokens=MAX_TOKENS,
                    temperature=TEMPERATURE,
                    top_p=TOP_P,
                    do_sample=True,
                    pad_token_id=TOKENIZER.eos_token_id,
                )
            
            response = TOKENIZER.decode(outputs[0], skip_special_tokens=True)
            
            # Extract just the new response
            response = response[len(prompt):].strip()
            
            return response if response else "I processed your request but couldn't generate a response."
            
        except Exception as e:
            return self._fallback_response(question, context, str(e))
    
    def _build_hermes_prompt(self, question: str, context: str) -> str:
        """Build a prompt for Hermes model"""
        
        system_prompt = """You are Hermes, an expert AI coding assistant. You help users understand, debug, and write code.

When answering questions:
- Be specific and technical when explaining code
- Provide code examples when helpful
- Focus on practical, actionable advice
- If you see bugs, point them out clearly"""
        
        prompt = f"<|im_start|>system\n{system_prompt}<|im_end|>\n"
        
        # Add context about the current repository
        if self.current_repo:
            prompt += f"<|im_start|>user\nContext: Working on repository {self.current_repo}\n"
            if self.current_path:
                prompt += f"Current path: {self.current_path}\n"
            if self.file_contents:
                prompt += "\nFiles in context:\n"
                for path, data in list(self.file_contents.items())[:3]:
                    prompt += f"\n--- {path} ---\n{data['content'][:500]}...\n"
            prompt += f"\n\nQuestion: {question}<|im_end|>\n"
        else:
            prompt += f"<|im_start|>user\n{question}<|im_end|>\n"
        
        prompt += "<|im_start|>assistant\n"
        
        return prompt
    
    def _fallback_response(self, question: str, context: str, error: str = None) -> str:
        """Fallback responses when model is not available"""
        question_lower = question.lower()
        
        if error:
            print(f"Hermes inference error: {error}")
        
        # Repository info responses
        if "what" in question_lower and ("repository" in question_lower or "repo" in question_lower):
            if self.current_repo:
                return f"📁 Current repository: **{self.current_repo}**\n\nModel loading... I can help you work with this codebase!\n- Read and analyze files\n- Suggest code improvements\n- Help you understand the structure\n\nWhat would you like to do?"
            else:
                return "No repository selected. Please select a GitHub repository from the dropdown to start working."
        
        # Help responses
        if "help" in question_lower or question_lower.startswith("how"):
            return """🛠️ **Hermes Coder Assistant - Available Commands:**

**Navigation:**
- Select a repository from the dropdown
- Click on folders to navigate into them
- Use ".." to go back to parent directory

**File Operations:**
- Click on any file to read its contents
- Edit code in the file editor
- Click "Save Changes" to commit to GitHub

**AI Assistance:**
- Ask me questions about the codebase
- Request code explanations
- Get suggestions for improvements
- Help writing new features

**Example Questions:**
- "What does this file do?"
- "Explain the project structure"
- "Help me fix this bug"
- "Write a test for this function"

How can I help you?"""
        
        # Project structure
        if "structure" in question_lower or "files" in question_lower or "folders" in question_lower:
            if self.current_repo and self.github:
                try:
                    owner, repo = self.current_repo.split("/")
                    contents = self.github.get_repo_contents(owner, repo)
                    files = [c["name"] for c in contents]
                    return f"📂 **Project Structure:**\n\n" + "\n".join([f"- {f}" for f in files])
                except:
                    pass
            return "Please select a repository first to see its structure."
        
        # Code explanation
        if self.file_contents:
            for path, data in self.file_contents.items():
                if path.endswith(('.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.go', '.rs')):
                    return self._analyze_code(data['content'], path)
        
        # Default helpful response
        if self.current_repo:
            return f"""🤔 I'm here to help with **{self.current_repo}**!

I can assist with:
- 📖 Reading and understanding code
- ✍️ Writing new code or modifying existing
- 🐛 Debugging issues
- 📝 Explaining complex logic
- 🔍 Analyzing project structure

Just let me know what you need!"""
        else:
            return "👋 Hi! Connect your GitHub account and select a repository to get started. I can help you work with any codebase!"

    def _analyze_code(self, content: str, path: str) -> str:
        """Simple code analysis"""
        lines = content.split('\n')
        analysis = [f"📊 **Analysis of `{path}`**\n"]
        analysis.append(f"- Total lines: {len(lines)}")
        analysis.append(f"- Non-empty lines: {len([l for l in lines if l.strip()])}")
        
        # Count some patterns
        functions = len(re.findall(r'def\s+\w+', content))
        classes = len(re.findall(r'class\s+\w+', content))
        comments = len(re.findall(r'#.*$', content, re.MULTILINE))
        
        if functions:
            analysis.append(f"- Functions defined: {functions}")
        if classes:
            analysis.append(f"- Classes defined: {classes}")
        if comments:
            analysis.append(f"- Comment lines: {comments}")
        
        return "\n".join(analysis)
    
    def _format_directory_list(self, contents: List[Dict], path: str) -> str:
        """Format directory listing as markdown"""
        items = []
        for item in sorted(contents, key=lambda x: (x['type'] != 'dir', x['name'])):
            icon = "📁" if item['type'] == 'dir' else "📄"
            items.append(f"{icon} {item['name']}")
        
        if path:
            items.insert(0, "📂 ..")
        
        return "\n".join(items) if items else "Empty directory"


# Initialize the application
app = HermesCoderAssistant()

# ============== Gradio UI ==============

def create_ui():
    """Create the Gradio interface"""
    
    with gr.Blocks(
        title="Hermes Coder Assistant",
        theme=gr.themes.Soft(
            primary_hue="blue",
            secondary_hue="purple",
        )
    ) as demo:
        
        gr.Markdown("""
        # 🤖 Hermes Coder Assistant
        
        An AI-powered coding assistant that connects to **Hermes-2-Pro-Llama-3-8B** and your **GitHub repositories**.
        
        ### Features:
        - 🔗 Connect to any GitHub repository
        - 📁 Browse and navigate codebases
        - ✏️ Edit files directly with AI assistance
        - 💬 Chat with Hermes about your code
        - 🚀 Commit changes directly to GitHub
        """)
        
        # Model status display
        model_status = gr.State(value="Model will load on first query...")
        
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### 🔐 GitHub Connection")
                
                github_token = gr.Textbox(
                    label="GitHub Token (or HF_TOKEN with GitHub permissions)",
                    type="password",
                    placeholder="ghp_xxxxxxxxxxxx",
                    info="Create at: https://github.com/settings/tokens"
                )
                
                connect_btn = gr.Button("🔗 Connect to GitHub", variant="primary")
                connection_status = gr.Textbox(label="Status", interactive=False)
                
                connect_btn.click(
                    fn=app.set_github_token,
                    inputs=[github_token],
                    outputs=[connection_status]
                )
                
                gr.Markdown("### 🤖 Hermes Model")
                
                model_status_display = gr.HTML(
                    value='<div style="padding: 10px; background: #f0f0f0; border-radius: 5px;">🤖 Model: Loading on first query...</div>'
                )
                
                gr.Markdown("### 📁 Repository")
                
                repo_dropdown = gr.Dropdown(
                    label="Select Repository",
                    choices=app.get_repositories(),
                    allow_custom_value=True
                )
                
                refresh_btn = gr.Button("🔄 Refresh Repos")
                refresh_btn.click(
                    fn=app.get_repositories,
                    outputs=[repo_dropdown]
                )
                
                repo_display = gr.Textbox(
                    label="Files & Folders",
                    lines=12,
                    interactive=False
                )
                
                repo_dropdown.change(
                    fn=app.select_repository,
                    inputs=[repo_dropdown],
                    outputs=[repo_display]
                )
                
                with gr.Row():
                    branch_dropdown = gr.Dropdown(
                        label="Branch",
                        choices=["main"],
                        scale=2
                    )
                    branch_btn = gr.Button("🔀", scale=1, info="Switch branch")
                
                branch_btn.click(
                    fn=app.get_branches_list,
                    outputs=[branch_dropdown]
                )
                
                branch_dropdown.change(
                    fn=app.switch_branch,
                    inputs=[branch_dropdown],
                    outputs=[repo_display]
                )
                
                path_input = gr.Textbox(
                    label="Navigate to Path",
                    placeholder="subfolder-name or ..",
                    info="Enter folder name to navigate, or '..' for parent"
                )
                
                navigate_btn = gr.Button("📂 Go")
                navigate_btn.click(
                    fn=app.navigate_to_path,
                    inputs=[path_input],
                    outputs=[repo_display]
                )
                
                gr.Markdown("### 🔍 Search & Utils")
                
                with gr.Accordion("Search", open=False):
                    search_input = gr.Textbox(
                        label="Search in Repository",
                        placeholder="Enter search term..."
                    )
                    search_btn = gr.Button("🔍 Search")
                    search_results = gr.Textbox(label="Results", lines=8, interactive=False)
                    
                    search_btn.click(
                        fn=app.search_in_repo,
                        inputs=[search_input],
                        outputs=[search_results]
                    )
                
                with gr.Accordion("📜 Commits", open=False):
                    commits_display = gr.Textbox(label="Recent Commits", lines=10, interactive=False)
                    commits_btn = gr.Button("📜 Load Commits")
                    
                    commits_btn.click(
                        fn=app.get_commits_list,
                        outputs=[commits_display]
                    )
                
                with gr.Accordion("🌿 Create Branch", open=False):
                    new_branch_input = gr.Textbox(
                        label="New Branch Name",
                        placeholder="feature/my-feature"
                    )
                    create_branch_btn = gr.Button("🌿 Create Branch")
                    branch_status = gr.Textbox(label="Status", interactive=False)
                    
                    create_branch_btn.click(
                        fn=app.create_branch,
                        inputs=[new_branch_input],
                        outputs=[branch_status]
                    )
            
            with gr.Column(scale=2):
                gr.Markdown("### 📝 File Editor")
                
                with gr.Row():
                    file_select = gr.Textbox(
                        label="File to Edit",
                        placeholder="Click on a file above or enter filename",
                        scale=3
                    )
                    read_btn = gr.Button("📖 Read", scale=1)
                
                file_editor = gr.Code(
                    label="File Content",
                    language="auto",
                    lines=20
                )
                
                with gr.Row():
                    save_btn = gr.Button("💾 Save Changes", variant="primary")
                    delete_btn = gr.Button("🗑️ Delete File", variant="stop")
                
                file_status = gr.Textbox(label="Status", interactive=False)
                
                read_btn.click(
                    fn=app.read_file,
                    inputs=[file_select],
                    outputs=[file_editor, file_status]
                )
                
                save_btn.click(
                    fn=app.save_file,
                    inputs=[file_select, file_editor],
                    outputs=[file_status]
                )
                
                delete_btn.click(
                    fn=app.delete_file,
                    inputs=[file_select],
                    outputs=[file_status]
                )
                
                gr.Markdown("---")
                gr.Markdown("### 💬 Chat with Hermes")
                
                chatbot = gr.Chatbot(
                    label="Conversation",
                    height=300
                )
                
                msg_input = gr.Textbox(
                    label="Ask Hermes",
                    placeholder="What does this codebase do? Help me fix a bug...",
                    scale=4
                )
                
                send_btn = gr.Button("Send", scale=1, variant="primary")
                
                def respond(message, history):
                    # Update model status
                    if not MODEL_LOADED:
                        status_html = '<div style="padding: 10px; background: #fff3cd; border-radius: 5px;">🤖 Model: Loading now... (first query takes longer)</div>'
                    else:
                        status_html = '<div style="padding: 10px; background: #d4edda; border-radius: 5px;">✅ Model: Ready</div>'
                    
                    response = app.ask_hermes(message)
                    history.append((message, response))
                    return "", history, status_html
                
                msg_input.submit(
                    fn=respond,
                    inputs=[msg_input, chatbot],
                    outputs=[msg_input, chatbot, model_status_display]
                )
                
                send_btn.click(
                    fn=respond,
                    inputs=[msg_input, chatbot],
                    outputs=[msg_input, chatbot, model_status_display]
                )
                
                gr.Markdown("""
                ---
                ### 📖 How to Use
                
                1. **Connect GitHub**: Enter your GitHub token and click Connect
                2. **Select Repo**: Choose a repository from the dropdown
                3. **Browse Files**: Click on files/folders to navigate
                4. **Edit & Save**: Make changes and click Save to commit
                5. **Chat**: Ask Hermes questions about the code (first query loads the model)
                
                💡 *Tip: Your GitHub token needs 'repo' scope for private repos*
                """)
    
    return demo


# Launch the app
if __name__ == "__main__":
    demo = create_ui()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=True
    )
