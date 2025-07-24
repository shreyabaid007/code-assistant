from src.analyzer import RepoAnalyzer
import asyncio


async def main():
    # Example repositories to analyze
    test_repos = [
        "https://github.com/fastapi/fastapi",
    ]

    analyzer = RepoAnalyzer()

    for repo_url in test_repos:
        print(f"\n{'=' * 50}")
        print(f"Analyzing: {repo_url}")
        print('=' * 50)

        try:
            analysis = analyzer.analyze_repository(repo_url)

            print(f"\n📝 Summary: {analysis.summary[:200]}...")
            print(f"🏗️  Languages: {', '.join(analysis.tech_stack.languages)}")
            print(f"📊 Quality Score: {analysis.code_quality_score:.2f}")
            print(f"🔧 Insights Found: {len(analysis.insights)}")

        except Exception as e:
            print(f"❌ Error analyzing {repo_url}: {e}")


if __name__ == "__main__":
    asyncio.run(main())