#!/usr/bin/env python3
"""
Setup Project Structure - Create Project-tasks/{slug}/ directories
Part of: Hierarchical Multi-Agent Orchestration System v2.0.0 (Python)

Cross-platform replacement for:
  mkdir -p "Project-tasks/$SLUG/spec"
  mkdir -p "Project-tasks/$SLUG/deliverables"
  cp "spec.md" "Project-tasks/$SLUG/spec/original-spec.md"
"""

import sys
import argparse
import shutil
from pathlib import Path

# Import utilities
from utils import (
    log_info, log_warn, log_error,
    ensure_directory, slugify
)


def setup_project_structure(
    topic_slug: str,
    spec_source: str = None,
    create_spec_dir: bool = True,
    create_deliverables_dir: bool = True
) -> bool:
    """
    Create Project-tasks/{slug}/ directory structure

    Args:
        topic_slug: Topic slug (kebab-case)
        spec_source: Optional path to spec file to copy
        create_spec_dir: Create spec/ subdirectory
        create_deliverables_dir: Create deliverables/ subdirectory

    Returns:
        True if successful, False otherwise
    """
    try:
        # Validate slug
        if not topic_slug or not topic_slug.strip():
            log_error("Topic slug is required")
            return False

        # Sanitize slug
        topic_slug = slugify(topic_slug)

        # Base directory
        base_dir = Path("Project-tasks") / topic_slug
        ensure_directory(base_dir)
        log_info(f"Created: {base_dir}/")

        # Spec directory
        if create_spec_dir:
            spec_dir = base_dir / "spec"
            ensure_directory(spec_dir)
            log_info(f"Created: {spec_dir}/")

            # Copy spec file if provided
            if spec_source:
                spec_source_path = Path(spec_source)
                if spec_source_path.exists() and spec_source_path.is_file():
                    spec_dest = spec_dir / "original-spec.md"
                    shutil.copy2(spec_source_path, spec_dest)
                    log_info(f"Copied spec: {spec_source} → {spec_dest}")
                else:
                    log_warn(f"Spec file not found: {spec_source}")

        # Deliverables directory
        if create_deliverables_dir:
            deliverables_dir = base_dir / "deliverables"
            ensure_directory(deliverables_dir)
            log_info(f"Created: {deliverables_dir}/")

        log_info(f"✓ Project structure ready: {base_dir}")
        return True

    except Exception as e:
        log_error(f"Failed to create project structure: {e}")
        return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Create Project-tasks/{slug}/ directory structure'
    )
    parser.add_argument(
        'topic_slug',
        help='Topic slug (kebab-case)'
    )
    parser.add_argument(
        '--spec-source', '-s',
        help='Path to spec file to copy to spec/original-spec.md'
    )
    parser.add_argument(
        '--no-spec',
        action='store_true',
        help='Skip creating spec/ directory'
    )
    parser.add_argument(
        '--no-deliverables',
        action='store_true',
        help='Skip creating deliverables/ directory'
    )

    args = parser.parse_args()

    # Setup structure
    success = setup_project_structure(
        topic_slug=args.topic_slug,
        spec_source=args.spec_source,
        create_spec_dir=not args.no_spec,
        create_deliverables_dir=not args.no_deliverables
    )

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
