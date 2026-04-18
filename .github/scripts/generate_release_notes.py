#!/usr/bin/env python3
"""
Generate release notes for GitHub releases.
This script is used by the CI/CD pipeline to automatically generate
release notes based on git commit history.
"""

import sys
from datetime import datetime

import git


def main():
    """Generate release notes based on git history."""
    if len(sys.argv) != 2:
        print("Usage: python generate_release_notes.py <version>")
        sys.exit(1)

    current_tag = sys.argv[1]

    try:
        repo = git.Repo(".")
    except git.InvalidGitRepositoryError:
        print("Error: Not a git repository")
        sys.exit(1)

    # Get all tags sorted by date
    try:
        tags = sorted(
            repo.tags, key=lambda t: t.commit.committed_datetime, reverse=True
        )
    except Exception:
        tags = []

    current_ref = f"v{current_tag}"

    # Find the previous tag
    previous_tag = None
    for tag in tags:
        if tag.name != current_ref:
            previous_tag = tag.name
            break

    print(f"## 🚀 Router Test Kit v{current_tag}")
    print()
    print(f"Released on {datetime.now().strftime('%Y-%m-%d')}")
    print()

    # Get commits since last tag
    if previous_tag:
        print(f"### Changes since {previous_tag}")
        print()
        try:
            commits = list(repo.iter_commits(f"{previous_tag}..HEAD"))
        except Exception:
            commits = list(repo.iter_commits("HEAD", max_count=10))
    else:
        print("### Changes in this release")
        print()
        commits = list(repo.iter_commits("HEAD", max_count=10))

    # Categorize commits
    features = []
    fixes = []
    docs = []
    tests = []
    ci = []
    others = []

    for commit in commits:
        message = commit.message.strip().split("\n")[0]  # First line only

        if any(
            keyword in message.lower()
            for keyword in ["feat:", "feature:", "add:", "new:"]
        ):
            features.append(message)
        elif any(keyword in message.lower() for keyword in ["fix:", "bug:", "patch:"]):
            fixes.append(message)
        elif any(
            keyword in message.lower()
            for keyword in ["docs:", "doc:", "documentation:"]
        ):
            docs.append(message)
        elif any(
            keyword in message.lower() for keyword in ["test:", "tests:", "testing:"]
        ):
            tests.append(message)
        elif any(
            keyword in message.lower()
            for keyword in ["ci:", "cd:", "workflow:", "action:"]
        ):
            ci.append(message)
        else:
            others.append(message)

    # Output categorized changes
    if features:
        print("#### ✨ New Features")
        for feat in features:
            print(f"- {feat}")
        print()

    if fixes:
        print("#### 🐛 Bug Fixes")
        for fix in fixes:
            print(f"- {fix}")
        print()

    if docs:
        print("#### 📚 Documentation")
        for doc in docs:
            print(f"- {doc}")
        print()

    if tests:
        print("#### 🧪 Testing")
        for test in tests:
            print(f"- {test}")
        print()

    if ci:
        print("#### ⚙️ CI/CD")
        for item in ci:
            print(f"- {item}")
        print()

    if others:
        print("#### 🔧 Other Changes")
        for other in others[:5]:  # Limit to 5 items
            print(f"- {other}")
        print()

    # Installation and links
    print("### 📦 Installation")
    print()
    print("```bash")
    print(f"pip install router-test-kit=={current_tag}")
    print("```")
    print()
    print("### 🔗 Links")
    print()
    print("- [📖 Documentation](https://alex-anast.github.io/router-test-kit/)")
    print("- [📦 PyPI Package](https://pypi.org/project/router-test-kit/)")
    print("- [💻 Source Code](https://github.com/alex-anast/router-test-kit)")
    print("- [🐛 Issues](https://github.com/alex-anast/router-test-kit/issues)")
    print()
    print("---")
    print()
    print("Thank you for using Router Test Kit! 🎉")


if __name__ == "__main__":
    main()
