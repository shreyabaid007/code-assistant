import requests
import json
from typing import List
from .models import RepositoryAnalysis, CodeFile, TechnologyStack, CodeInsight
from config.settings import settings


class OllamaAnalyzer:
    """Simple Ollama client with same interface as OpenAIAnalyzer"""
    
    def __init__(self):
        self.base_url = settings.ollama_base_url
        self.model = settings.ollama_model

    def _make_request(self, prompt: str, max_tokens: int = 1000) -> str:
        """Make request to Ollama"""
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"num_predict": max_tokens, "temperature": 0.1}
        }
        
        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()
        return response.json().get('response', '').strip()

    def summarize_large_files(self, files: List[CodeFile]) -> List[str]:
        """Create summaries for large files"""
        summaries = []
        for file in files:
            if len(file.content) > settings.max_file_content_chars:
                try:
                    content = file.content[:settings.max_file_content_chars]
                    prompt = f"Summarize this {file.language} file in 2-3 sentences:\n{content}"
                    summary = self._make_request(prompt, max_tokens=100)
                    summaries.append(f"{file.path}: {summary}")
                except Exception as e:
                    print(f"Error summarizing {file.path}: {e}")
                    summaries.append(f"{file.path}: Large {file.language} file ({file.size} bytes)")
            else:
                summaries.append(f"{file.path}: {file.language} file ({file.size} bytes)")
        return summaries

    def analyze_repository(self, code_files: List[CodeFile], repo_info: dict, repo_url: str) -> RepositoryAnalysis:
        """Analyze repository using Ollama"""
        from .github_client import GitHubClient
        
        github_client = GitHubClient()
        
        # Stage 1: Quick overview
        print("Stage 1: Quick overview (Ollama)...")
        summaries = self.summarize_large_files(code_files)
        context = f"""Repository: {repo_info.get('name', 'Unknown')}
Description: {repo_info.get('description', 'No description')}

Files: {chr(10).join(summaries[:10])}"""

        stage1_prompt = f"""Analyze this repository: {repo_url}
{context}

Provide a brief overview as JSON:
{{"summary": "brief description", "primary_tech": ["main technologies"]}}"""

        try:
            stage1_response = self._make_request(stage1_prompt, max_tokens=300)
            stage1_data = json.loads(stage1_response)
        except:
            stage1_data = {"summary": "Repository analysis", "primary_tech": []}

        # Stage 2: Detailed analysis
        print("Stage 2: Detailed analysis (Ollama)...")
        important_files = github_client.select_important_files(code_files, settings.max_analysis_files)
        
        detailed_context = f"Repository: {stage1_data.get('summary', '')}\n\nKey Files:\n"
        for file in important_files:
            if file.file_type.value == 'source_code':
                content = github_client.extract_key_content(file)
            else:
                content = file.content[:settings.max_file_content_chars]
            detailed_context += f"\n{file.path}:\n{content}\n---\n"

        stage2_prompt = f"""Analyze these key files:
{detailed_context}

Provide analysis as JSON:
{{
    "tech_stack": {{"languages": [], "frameworks": [], "libraries": [], "tools": [], "databases": []}},
    "insights": [{{"category": "improvement", "severity": "medium", "description": "issue", "file_path": "file.py", "line_number": null, "suggestion": "fix"}}],
    "documentation_score": 0.75,
    "code_quality_score": 0.85,
    "maintainability_score": 0.80,
    "recommendations": ["recommendation"]
}}"""

        try:
            stage2_response = self._make_request(stage2_prompt, max_tokens=800)
            stage2_data = json.loads(stage2_response)
        except:
            stage2_data = {
                "tech_stack": {"languages": [], "frameworks": [], "libraries": [], "tools": [], "databases": []},
                "insights": [], "documentation_score": 0.5, "code_quality_score": 0.5, 
                "maintainability_score": 0.5, "recommendations": []
            }

        # Create analysis object
        tech_stack = TechnologyStack(**stage2_data.get('tech_stack', {}))
        insights = [CodeInsight(**insight) for insight in stage2_data.get('insights', []) if isinstance(insight, dict)]

        return RepositoryAnalysis(
            repo_url=repo_url,
            summary=stage1_data.get('summary', ''),
            tech_stack=tech_stack,
            insights=insights,
            documentation_score=stage2_data.get('documentation_score', 0.5),
            code_quality_score=stage2_data.get('code_quality_score', 0.5),
            maintainability_score=stage2_data.get('maintainability_score', 0.5),
            trending_comparisons=[],
            recommendations=stage2_data.get('recommendations', [])
        )