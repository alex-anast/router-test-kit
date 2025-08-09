#!/usr/bin/env python3
"""
Update CHANGELOG.md with new release information.
This script is used by the CI/CD pipeline to automatically update
the changelog when creating releases.
"""

import re
import sys
from datetime import datetime
from pathlib import Path


def update_changelog(version: str, changelog_path: str = "CHANGELOG.md") -> None:
    """Update the changelog with the new version."""
    changelog_file = Path(changelog_path)
    
    if not changelog_file.exists():
        print(f"Error: {changelog_path} not found")
        sys.exit(1)
    
    content = changelog_file.read_text()
    
    # Get today's date
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Replace the unreleased section with the new version
    unreleased_pattern = r'\[Unreleased\]'
    new_version_header = f'[{version}] - {today}'
    
    # Add a new Unreleased section at the top
    new_unreleased = f"""## [Unreleased]

### Added

### Changed

### Fixed

### Removed

## [{version}] - {today}"""
    
    # Replace [Unreleased] with the new version and add new Unreleased section
    if '[Unreleased]' in content:
        # Replace the first occurrence of [Unreleased] 
        content = content.replace('## [Unreleased]', new_unreleased, 1)
    else:
        # If no Unreleased section, add it at the top after the header
        lines = content.split('\n')
        insert_index = 0
        for i, line in enumerate(lines):
            if line.strip() and not line.startswith('#'):
                insert_index = i
                break
        
        lines.insert(insert_index, f"## [{version}] - {today}")
        lines.insert(insert_index, "")
        content = '\n'.join(lines)
    
    # Write back to file
    changelog_file.write_text(content)
    print(f"Updated {changelog_path} with version {version}")


def main():
    """Main entry point."""
    if len(sys.argv) != 2:
        print("Usage: python update_changelog.py <version>")
        print("Example: python update_changelog.py 1.2.3")
        sys.exit(1)
    
    version = sys.argv[1]
    
    # Validate version format (basic semver check)
    if not re.match(r'^\d+\.\d+\.\d+', version):
        print(f"Error: Invalid version format '{version}'. Expected semver (e.g., 1.2.3)")
        sys.exit(1)
    
    update_changelog(version)
    print(f"Successfully updated changelog for version {version}")


if __name__ == '__main__':
    main()
