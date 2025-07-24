from openai import OpenAI
from typing import List, Dict, Any
from .models import RepositoryAnalysis, CodeFile, TechnologyStack, CodeInsight
from config.settings import settings
import json


class OpenAIAnalyzer:
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)

    def summarize_large_files(self, files: List[CodeFile]) -> List[str]:
        """Create concise summaries for large files using gpt-4o-mini"""
        summaries = []
        
        for file in files:
            if len(file.content) > settings.max_file_content_chars:
                try:
                    # Truncate content for summarization
                    truncated_content = file.content[:settings.max_file_content_chars]
                    
                    response = self.client.chat.completions.create(
                        model=settings.analysis_model,  # gpt-4o-mini
                        messages=[{
                            "role": "user",
                            "content": f"""Summarize this {file.language} file in 2-3 sentences. Focus on its main purpose and key functionality.

File: {file.path}
Content:
{truncated_content}"""
                        }],
                        max_tokens=100,
                        temperature=0.1
                    )
                    
                    summary = response.choices[0].message.content.strip()
                    summaries.append(f"{file.path}: {summary}")
                    
                except Exception as e:
                    print(f"Error summarizing {file.path}: {e}")
                    summaries.append(f"{file.path}: Large {file.language} file ({file.size} bytes)")
            else:
                # For smaller files, just note their existence
                summaries.append(f"{file.path}: {file.language} file ({file.size} bytes)")
                
        return summaries

    def _prepare_lightweight_context(self, code_files: List[CodeFile], repo_info: dict) -> str:
        """Prepare lightweight context using file summaries instead of full content"""
        context = f"""
Repository: {repo_info.get('name', 'Unknown')}
Description: {repo_info.get('description', 'No description')}
Language: {repo_info.get('language', 'Multiple')}
Stars: {repo_info.get('stargazers_count', 0)}
Forks: {repo_info.get('forks_count', 0)}

File Structure Summary:
"""
        
        # Get file summaries
        summaries = self.summarize_large_files(code_files)
        for summary in summaries:
            context += f"  - {summary}\n"
            
        return context

    def analyze_repository(self, code_files: List[CodeFile], repo_info: dict, repo_url: str) -> RepositoryAnalysis:
        """Two-stage cost-optimized analysis using regular chat completions"""
        from .github_client import GitHubClient
        
        # Initialize GitHub client for file selection
        github_client = GitHubClient()
        
        # Stage 1: Quick overview with lightweight context using gpt-4o-mini
        print("Stage 1: Quick repository overview...")
        lightweight_context = self._prepare_lightweight_context(code_files, repo_info)
        
        try:
            stage1_response = self.client.chat.completions.create(
                model=settings.analysis_model,  # gpt-4o-mini
                messages=[{
                    "role": "user", 
                    "content": f"""Provide a quick overview of this repository: {repo_url}

{lightweight_context}

Respond with a brief analysis (max 500 tokens) covering:
1. Repository purpose and main functionality
2. Primary technologies used
3. Overall architecture assessment

Format as JSON:
{{
    "summary": "brief description",
    "primary_tech": ["main technologies"],
    "architecture_notes": "brief architecture assessment"
}}"""
                }],
                max_tokens=500,
                temperature=0.1
            )
            
            stage1_data = json.loads(stage1_response.choices[0].message.content)
            print(f"Stage 1 completed. Tokens used: {stage1_response.usage.total_tokens}")
            
        except Exception as e:
            print(f"Stage 1 error: {e}")
            stage1_data = {"summary": "Repository analysis", "primary_tech": [], "architecture_notes": ""}
        
        # Stage 2: Detailed analysis on selected important files using gpt-4o
        print("Stage 2: Detailed analysis of key files...")
        important_files = github_client.select_important_files(code_files, settings.max_analysis_files)
        
        # Extract key content and limit file sizes
        detailed_context = f"""
Repository: {repo_info.get('name', 'Unknown')} - {stage1_data.get('summary', '')}
Key Technologies: {', '.join(stage1_data.get('primary_tech', []))}

Important Files Analysis:
"""
        
        for file in important_files:
            # Use extract_key_content for code files, limit all files
            if file.file_type.value == 'source_code':
                content = github_client.extract_key_content(file)
            else:
                content = file.content[:settings.max_file_content_chars]
                
            detailed_context += f"""
File: {file.path} ({file.language})
{content}

---
"""
        
        try:
            stage2_response = self.client.chat.completions.create(
                model=settings.reasoning_model,  # gpt-4o
                messages=[{
                    "role": "user",
                    "content": f"""Provide detailed analysis of this repository's key files.

{detailed_context}

Provide comprehensive analysis (max 1000 tokens) as JSON:
{{
    "tech_stack": {{
        "languages": ["detected languages"],
        "frameworks": ["detected frameworks"], 
        "libraries": ["detected libraries"],
        "tools": ["detected tools"],
        "databases": ["detected databases"]
    }},
    "insights": [
        {{
            "category": "bug|improvement|architecture|performance",
            "severity": "low|medium|high|critical",
            "description": "detailed issue description", 
            "file_path": "path/to/file.py",
            "line_number": null,
            "suggestion": "specific improvement suggestion"
        }}
    ],
    "documentation_score": 0.75,
    "code_quality_score": 0.85,
    "maintainability_score": 0.80,
    "recommendations": ["specific actionable recommendations"]
}}"""
                }],
                max_tokens=1000,
                temperature=0.1
            )
            
            stage2_data = json.loads(stage2_response.choices[0].message.content)
            print(f"Stage 2 completed. Tokens used: {stage2_response.usage.total_tokens}")
            
        except Exception as e:
            print(f"Stage 2 error: {e}")
            stage2_data = {
                "tech_stack": {"languages": [], "frameworks": [], "libraries": [], "tools": [], "databases": []},
                "insights": [],
                "documentation_score": 0.5,
                "code_quality_score": 0.5, 
                "maintainability_score": 0.5,
                "recommendations": []
            }
        
        # Combine results from both stages
        combined_data = {
            "summary": stage1_data.get('summary', ''),
            "tech_stack": stage2_data.get('tech_stack', {}),
            "insights": stage2_data.get('insights', []),
            "documentation_score": stage2_data.get('documentation_score', 0.5),
            "code_quality_score": stage2_data.get('code_quality_score', 0.5),
            "maintainability_score": stage2_data.get('maintainability_score', 0.5),
            "trending_comparisons": [],  # Removed to save costs
            "recommendations": stage2_data.get('recommendations', [])
        }
        
        return self._create_analysis_object(combined_data, repo_url)

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