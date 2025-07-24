import requests
import os
from git import Repo
from pathlib import Path
from typing import List, Tuple, Optional
from .models import CodeFile, FileType


class GitHubClient:
    def __init__(self, token: Optional[str] = None):
        self.token = token
        self.headers = {"Authorization": f"token {token}"} if token else {}

    def clone_repository(self, repo_url: str, local_path: str) -> str:
        """Clone repository to local path"""
        if os.path.exists(local_path):
            import shutil
            shutil.rmtree(local_path)

        Repo.clone_from(repo_url, local_path)
        return local_path

    def get_repo_info(self, repo_url: str) -> dict:
        """Get repository metadata from GitHub API"""
        parts = repo_url.replace("https://github.com/", "").split("/")
        if len(parts) >= 2:
            owner, repo = parts[0], parts[1]
            api_url = f"https://api.github.com/repos/{owner}/{repo}"

            response = requests.get(api_url, headers=self.headers)
            if response.status_code == 200:
                return response.json()

        return {}

    def analyze_local_repo(self, repo_path: str, max_file_size: int = 100_000) -> List[CodeFile]:
        """Analyze local repository and extract code files"""
        code_files = []
        repo_path = Path(repo_path)

        # File type mapping
        extension_map = {
            '.py': ('python', FileType.SOURCE_CODE),
            '.js': ('javascript', FileType.SOURCE_CODE),
            '.ts': ('typescript', FileType.SOURCE_CODE),
            '.jsx': ('javascript', FileType.SOURCE_CODE),
            '.tsx': ('typescript', FileType.SOURCE_CODE),
            '.java': ('java', FileType.SOURCE_CODE),
            '.cpp': ('cpp', FileType.SOURCE_CODE),
            '.c': ('c', FileType.SOURCE_CODE),
            '.go': ('go', FileType.SOURCE_CODE),
            '.rs': ('rust', FileType.SOURCE_CODE),
            '.rb': ('ruby', FileType.SOURCE_CODE),
            '.php': ('php', FileType.SOURCE_CODE),
            '.md': ('markdown', FileType.DOCUMENTATION),
            '.txt': ('text', FileType.DOCUMENTATION),
            '.json': ('json', FileType.CONFIGURATION),
            '.yaml': ('yaml', FileType.CONFIGURATION),
            '.yml': ('yaml', FileType.CONFIGURATION),
            '.toml': ('toml', FileType.CONFIGURATION),
        }

        # Skip common directories
        skip_dirs = {'.git', 'node_modules', '__pycache__', '.venv', 'venv', 'dist', 'build'}

        for file_path in repo_path.rglob('*'):
            if (file_path.is_file() and
                    file_path.suffix in extension_map and
                    not any(skip_dir in file_path.parts for skip_dir in skip_dirs) and
                    file_path.stat().st_size <= max_file_size):

                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()

                    language, file_type = extension_map[file_path.suffix]

                    # Detect test files
                    if 'test' in file_path.name.lower() or 'spec' in file_path.name.lower():
                        file_type = FileType.TEST

                    code_files.append(CodeFile(
                        path=str(file_path.relative_to(repo_path)),
                        content=content,
                        language=language,
                        size=len(content),
                        file_type=file_type
                    ))

                except Exception as e:
                    print(f"Error reading {file_path}: {e}")
                    continue

        return code_files

    def extract_key_content(self, file: CodeFile) -> str:
        """Extract key content from file by removing imports, comments, and empty lines"""
        lines = file.content.split('\n')
        meaningful_lines = []
        
        for line in lines:
            stripped = line.strip()
            # Skip empty lines
            if not stripped:
                continue
            # Skip single-line comments (basic patterns)
            if (stripped.startswith('#') or 
                stripped.startswith('//') or 
                stripped.startswith('/*') or
                stripped.startswith('*') or
                stripped.startswith('*/') or
                stripped.startswith('<!--')):
                continue
            # Skip imports/requires (basic patterns)
            if (stripped.startswith('import ') or 
                stripped.startswith('from ') or
                stripped.startswith('require(') or
                stripped.startswith('const ') and 'require(' in stripped or
                stripped.startswith('import{') or
                stripped.startswith('import {')):
                continue
                
            meaningful_lines.append(line)
            
            # Return first 50 meaningful lines
            if len(meaningful_lines) >= 50:
                break
                
        return '\n'.join(meaningful_lines)

    def select_important_files(self, code_files: List[CodeFile], max_files: int = 10) -> List[CodeFile]:
        """Select the most important files for analysis, prioritizing main files and larger files"""
        if not code_files:
            return []
            
        # Priority scoring function
        def get_priority_score(file: CodeFile) -> int:
            score = 0
            filename = file.path.lower()
            
            # High priority files
            if any(name in filename for name in ['main.py', 'app.py', '__init__.py', 'index.js', 'index.ts']):
                score += 100
            
            # Config files
            if any(ext in filename for ext in ['.json', '.yaml', '.yml', '.toml', '.config']):
                score += 50
                
            # Core application files (not in subdirectories)
            if '/' not in file.path or file.path.count('/') <= 1:
                score += 30
                
            # Larger files (more likely to contain important logic)
            if file.size > 1000:
                score += 20
                
            # Source code over other types
            if file.file_type.value == 'source_code':
                score += 10
                
            return score
            
        # Sort by priority score (descending)
        sorted_files = sorted(code_files, key=get_priority_score, reverse=True)
        
        # Return top files up to max_files limit
        return sorted_files[:max_files]