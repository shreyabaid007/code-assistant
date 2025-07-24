import tempfile
import shutil
from pathlib import Path
from typing import Optional
from .github_client import GitHubClient
from .openai_client import OpenAIAnalyzer
from .models import RepositoryAnalysis
from config.settings import settings


class RepoAnalyzer:
    def __init__(self):
        self.github_client = GitHubClient(settings.github_token)
        self.openai_analyzer = OpenAIAnalyzer()

    def analyze_repository(self, repo_url: str) -> RepositoryAnalysis:
        """Main method to analyze a repository"""
        print(f"🔍 Analyzing repository: {repo_url}")

        # Create temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Clone repository
            print("📥 Cloning repository...")
            local_path = self.github_client.clone_repository(repo_url, temp_dir)

            # Get repository metadata
            print("📊 Fetching repository metadata...")
            repo_info = self.github_client.get_repo_info(repo_url)

            # Analyze code files
            print("🔍 Analyzing code files...")
            code_files = self.github_client.analyze_local_repo(
                local_path,
                settings.max_file_size
            )

            print(f"Found {len(code_files)} analyzable files")

            # Perform AI analysis
            print("🤖 Running AI analysis...")
            analysis = self.openai_analyzer.analyze_repository(
                code_files, repo_info, repo_url
            )

            print("✅ Analysis complete!")
            return analysis


def main():
    """CLI interface for testing"""
    import typer
    from rich.console import Console
    from rich.table import Table
    from rich import print as rprint

    app = typer.Typer()
    console = Console()

    @app.command()
    def analyze(repo_url: str):
        """Analyze a GitHub repository"""
        try:
            analyzer = RepoAnalyzer()
            analysis = analyzer.analyze_repository(repo_url)

            # Display results
            console.print("\n🎯 [bold blue]Repository Analysis Results[/bold blue]\n")

            # Summary
            console.print(f"[bold green]Summary:[/bold green]\n{analysis.summary}\n")

            # Tech Stack
            tech_table = Table(title="Technology Stack")
            tech_table.add_column("Category", style="cyan")
            tech_table.add_column("Technologies", style="magenta")

            tech_table.add_row("Languages", ", ".join(analysis.tech_stack.languages))
            tech_table.add_row("Frameworks", ", ".join(analysis.tech_stack.frameworks))
            tech_table.add_row("Libraries", ", ".join(analysis.tech_stack.libraries))
            tech_table.add_row("Tools", ", ".join(analysis.tech_stack.tools))

            console.print(tech_table)

            # Scores
            scores_table = Table(title="Quality Scores")
            scores_table.add_column("Metric", style="cyan")
            scores_table.add_column("Score", style="green")

            scores_table.add_row("Documentation", f"{analysis.documentation_score:.2f}")
            scores_table.add_row("Code Quality", f"{analysis.code_quality_score:.2f}")
            scores_table.add_row("Maintainability", f"{analysis.maintainability_score:.2f}")

            console.print(scores_table)

            # Top Insights
            if analysis.insights:
                console.print("\n[bold red]Key Insights:[/bold red]")
                for i, insight in enumerate(analysis.insights[:5], 1):
                    console.print(f"{i}. [{insight.severity.upper()}] {insight.description}")
                    console.print(f"   💡 {insight.suggestion}\n")

            # Recommendations
            if analysis.recommendations:
                console.print("[bold yellow]Recommendations:[/bold yellow]")
                for i, rec in enumerate(analysis.recommendations, 1):
                    console.print(f"{i}. {rec}")

        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {e}")

    app()


if __name__ == "__main__":
    main()