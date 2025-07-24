from openai import OpenAI
from typing import List, Dict, Any
from .models import RepositoryAnalysis, CodeFile, TechnologyStack, CodeInsight
from config.settings import settings
import json


class OpenAIAnalyzer:
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)

    def analyze_repository(self, code_files: List[CodeFile], repo_info: dict, repo_url: str) -> RepositoryAnalysis:
        """Main analysis using Responses API with multiple tools"""

        # Prepare repository context
        repo_context = self._prepare_repo_context(code_files, repo_info)

        # Use Responses API with built-in tools for comprehensive analysis
        response = self.client.responses.create(
            model=settings.reasoning_model,  # o4-mini for reasoning
            input=f"""
            Analyze this repository comprehensively: {repo_url}

            Repository Context:
            {repo_context}

            Please provide:
            1. A detailed summary of what this repository does
            2. Complete technology stack analysis
            3. Code quality insights and recommendations
            4. Documentation assessment
            5. Maintainability analysis
            6. Current industry trend comparisons (use web search)

            Structure your response as JSON following this schema:
            {{
                "summary": "detailed repository summary",
                "tech_stack": {{
                    "languages": ["list of languages"],
                    "frameworks": ["list of frameworks"],
                    "libraries": ["list of libraries"],
                    "tools": ["list of tools"],
                    "databases": ["list of databases"]
                }},
                "insights": [
                    {{
                        "category": "bug|improvement|architecture|performance",
                        "severity": "low|medium|high|critical", 
                        "description": "detailed description",
                        "file_path": "path/to/file.py",
                        "line_number": 42,
                        "suggestion": "specific improvement suggestion"
                    }}
                ],
                "documentation_score": 0.85,
                "code_quality_score": 0.92,
                "maintainability_score": 0.78,
                "trending_comparisons": ["comparison with current trends"],
                "recommendations": ["actionable recommendations"]
            }}
            """,
            tools=[
                {"type": "web_search"},  # For trend analysis
                {"type": "code_interpreter"}  # For code analysis
            ],
            store=False  # Don't store conversation
        )

        # Parse response and create structured analysis
        try:
            analysis_data = json.loads(response.output_text)
            return self._create_analysis_object(analysis_data, repo_url)
        except json.JSONDecodeError:
            # Fallback parsing if JSON is malformed
            return self._parse_fallback_response(response.output_text, repo_url)

    def _prepare_repo_context(self, code_files: List[CodeFile], repo_info: dict) -> str:
        """Prepare repository context for analysis"""
        context = f"""
        Repository: {repo_info.get('name', 'Unknown')}
        Description: {repo_info.get('description', 'No description')}
        Language: {repo_info.get('language', 'Multiple')}
        Stars: {repo_info.get('stargazers_count', 0)}
        Forks: {repo_info.get('forks_count', 0)}

        File Structure:
        """

        # Group files by type
        file_groups = {}
        for file in code_files:
            if file.file_type not in file_groups:
                file_groups[file.file_type] = []
            file_groups[file.file_type].append(file)

        for file_type, files in file_groups.items():
            context += f"\n{file_type.value.title()} Files ({len(files)}):\n"
            for file in files[:10]:  # Limit to first 10 files per type
                context += f"  - {file.path} ({file.language}, {file.size} bytes)\n"
                if len(file.content) < 2000:  # Include small files
                    context += f"    Content preview: {file.content[:500]}...\n"

        return context

    def _create_analysis_object(self, data: dict, repo_url: str) -> RepositoryAnalysis:
        """Create RepositoryAnalysis object from parsed data"""
        tech_stack = TechnologyStack(**data.get('tech_stack', {}))

        insights = []
        for insight_data in data.get('insights', []):
            insights.append(CodeInsight(**insight_data))

        return RepositoryAnalysis(
            repo_url=repo_url,
            summary=data.get('summary', ''),
            tech_stack=tech_stack,
            insights=insights,
            documentation_score=data.get('documentation_score', 0.0),
            code_quality_score=data.get('code_quality_score', 0.0),
            maintainability_score=data.get('maintainability_score', 0.0),
            trending_comparisons=data.get('trending_comparisons', []),
            recommendations=data.get('recommendations', [])
        )

    def _parse_fallback_response(self, response_text: str, repo_url: str) -> RepositoryAnalysis:
        """Fallback parser for non-JSON responses"""
        # Simple fallback - in production, you'd implement more robust parsing
        return RepositoryAnalysis(
            repo_url=repo_url,
            summary=response_text[:500] + "...",
            tech_stack=TechnologyStack(
                languages=[], frameworks=[], libraries=[], tools=[], databases=[]
            ),
            insights=[],
            documentation_score=0.5,
            code_quality_score=0.5,
            maintainability_score=0.5,
            trending_comparisons=[],
            recommendations=[]
        )