"""
Simple usage example for multi-provider support.

Set environment variables:
- OPENAI_API_KEY=your-key (for OpenAI)
- LLM_PROVIDER=ollama (to use Ollama by default)
"""

import os
from src.analyzer import RepoAnalyzer

# Example usage
def main():
    print("🔍 Simple Multi-Provider Example\n")
    
    # Method 1: Use default provider from settings
    print("1. Using default provider...")
    try:
        analyzer = RepoAnalyzer()
        # analyzer.analyze_repository("https://github.com/user/repo")
        print("   ✅ Default analyzer ready")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Method 2: Explicitly choose provider
    print("\n2. Choosing specific providers...")
    
    # OpenAI
    try:
        openai_analyzer = RepoAnalyzer("openai")
        print("   ✅ OpenAI analyzer ready")
    except Exception as e:
        print(f"   ⚠️ OpenAI not available: {e}")
    
    # Ollama (free local)
    try:
        ollama_analyzer = RepoAnalyzer("ollama") 
        print("   ✅ Ollama analyzer ready")
    except Exception as e:
        print(f"   ⚠️ Ollama not available: {e}")
    
    print("\n💡 Usage tips:")
    print("   • Set OPENAI_API_KEY for OpenAI")
    print("   • Install Ollama and run 'ollama pull llama3.1:8b' for free analysis")
    print("   • CLI: python src/analyzer.py analyze <repo> --provider ollama")

if __name__ == "__main__":
    main()