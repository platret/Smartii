#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skill Manager - Native skill management for Claude Code
Handles skill discovery, enabling/disabling, and configuration management
"""

import os
import sys
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
import argparse

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


class SkillManager:
    def __init__(self, project_root: Optional[str] = None):
        """Initialize SkillManager with project root directory"""
        if project_root:
            self.project_root = Path(project_root)
        else:
            # Auto-detect project root (where .claude directory exists)
            current = Path.cwd()
            while current != current.parent:
                if (current / '.claude').exists():
                    self.project_root = current
                    break
                current = current.parent
            else:
                self.project_root = Path.cwd()

        self.skills_dir = self.project_root / '.claude' / 'skills'
        self.settings_file = self.project_root / '.claude' / 'settings.local.json'

    def discover_skills(self) -> List[Dict[str, Any]]:
        """Discover all skills in .claude/skills/ directory"""
        skills = []

        if not self.skills_dir.exists():
            return skills

        # Scan all subdirectories in .claude/skills/
        for skill_dir in self.skills_dir.iterdir():
            if not skill_dir.is_dir():
                continue

            skill_md = skill_dir / 'skill.md'
            if not skill_md.exists():
                continue

            # Parse skill metadata
            metadata = self._parse_skill_metadata(skill_md)
            metadata['skill_name'] = skill_dir.name
            metadata['skill_path'] = str(skill_dir)

            # Check enabled status
            metadata['enabled'] = self._check_skill_enabled(skill_dir.name)
            metadata['permissions'] = self._get_skill_permissions(skill_dir.name)

            skills.append(metadata)

        return skills

    def _parse_skill_metadata(self, skill_md_path: Path) -> Dict[str, Any]:
        """Parse YAML frontmatter from skill.md file"""
        metadata = {
            'name': '',
            'description': '',
            'version': '',
            'author': '',
            'tags': [],
            'auto_activate': False
        }

        try:
            with open(skill_md_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract YAML frontmatter (between --- markers)
            frontmatter_match = re.search(r'^---\s*\n(.*?)\n---', content, re.DOTALL | re.MULTILINE)
            if not frontmatter_match:
                return metadata

            frontmatter = frontmatter_match.group(1)

            # Parse YAML fields (simple parser, no external deps)
            for line in frontmatter.split('\n'):
                line = line.strip()
                if ':' not in line:
                    continue

                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()

                if key == 'name':
                    metadata['name'] = value
                elif key == 'description':
                    metadata['description'] = value
                elif key == 'version':
                    metadata['version'] = value
                elif key == 'author':
                    metadata['author'] = value
                elif key == 'auto-activate':
                    metadata['auto_activate'] = value.lower() in ('true', 'yes')
                elif key == 'tags':
                    # Parse tags array [tag1, tag2, tag3]
                    tags_match = re.findall(r'\[(.*?)\]', value)
                    if tags_match:
                        tags_str = tags_match[0]
                        metadata['tags'] = [t.strip() for t in tags_str.split(',')]

        except Exception as e:
            print(f"Error parsing {skill_md_path}: {e}", file=sys.stderr)

        return metadata

    def _check_skill_enabled(self, skill_name: str) -> bool:
        """Check if skill is enabled in settings.local.json"""
        settings = self._load_settings()
        if not settings:
            return False

        allow_list = settings.get('permissions', {}).get('allow', [])
        skill_permission = f"Skill({skill_name})"

        return skill_permission in allow_list

    def _get_skill_permissions(self, skill_name: str) -> List[str]:
        """Get all permissions related to a skill"""
        settings = self._load_settings()
        if not settings:
            return []

        allow_list = settings.get('permissions', {}).get('allow', [])

        # Find all permissions mentioning the skill name
        skill_perms = []
        for perm in allow_list:
            if skill_name in perm.lower():
                skill_perms.append(perm)

        return skill_perms

    def _load_settings(self) -> Optional[Dict]:
        """Load settings.local.json"""
        if not self.settings_file.exists():
            return None

        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading settings: {e}", file=sys.stderr)
            return None

    def _save_settings(self, settings: Dict) -> bool:
        """Save settings.local.json"""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving settings: {e}", file=sys.stderr)
            return False

    def enable_skill(self, skill_name: str) -> bool:
        """Enable a skill by adding to permissions.allow"""
        settings = self._load_settings()
        if not settings:
            settings = {'permissions': {'allow': [], 'deny': [], 'ask': []}}

        allow_list = settings.get('permissions', {}).get('allow', [])
        skill_permission = f"Skill({skill_name})"

        if skill_permission in allow_list:
            print(f"Skill '{skill_name}' is already enabled")
            return False

        allow_list.append(skill_permission)
        settings['permissions']['allow'] = allow_list

        if self._save_settings(settings):
            print(f"✅ Enabled: {skill_name}")
            return True
        return False

    def disable_skill(self, skill_name: str) -> bool:
        """Disable a skill by removing from permissions.allow"""
        settings = self._load_settings()
        if not settings:
            print(f"No settings file found")
            return False

        allow_list = settings.get('permissions', {}).get('allow', [])
        skill_permission = f"Skill({skill_name})"

        if skill_permission not in allow_list:
            print(f"Skill '{skill_name}' is not enabled")
            return False

        # Remove skill permission and related permissions
        updated_allow = []
        removed_perms = []

        for perm in allow_list:
            if skill_name in perm.lower():
                removed_perms.append(perm)
            else:
                updated_allow.append(perm)

        settings['permissions']['allow'] = updated_allow

        if self._save_settings(settings):
            print(f"⬜ Disabled: {skill_name}")
            if removed_perms:
                print(f"Removed permissions:")
                for perm in removed_perms:
                    print(f"  - {perm}")
            return True
        return False

    def list_skills(self, filter_type: str = 'all') -> None:
        """List skills with optional filtering"""
        skills = self.discover_skills()

        if not skills:
            print("No skills found in .claude/skills/")
            return

        # Filter skills
        if filter_type == 'enabled':
            skills = [s for s in skills if s['enabled']]
        elif filter_type == 'disabled':
            skills = [s for s in skills if not s['enabled']]

        # Sort by name
        skills.sort(key=lambda s: s['skill_name'])

        # Display
        print(f"\n📋 Skills ({len(skills)} total)\n")

        for skill in skills:
            status = "✅" if skill['enabled'] else "⬜"
            name = skill['name'] or skill['skill_name']
            version = skill['version'] or 'unknown'
            description = skill['description'] or 'No description'
            perm_count = len(skill['permissions'])

            print(f"{status} {skill['skill_name']} (v{version})")
            print(f"   {description}")
            print(f"   Permissions: {perm_count} configured")
            print()

    def show_skill_details(self, skill_name: str) -> None:
        """Show detailed information about a specific skill"""
        skills = self.discover_skills()
        skill = next((s for s in skills if s['skill_name'] == skill_name), None)

        if not skill:
            print(f"❌ Skill '{skill_name}' not found")
            return

        status = "✅ Enabled" if skill['enabled'] else "⬜ Not Enabled"

        print(f"\n📊 Skill Details: {skill_name}")
        print("=" * 60)
        print(f"\nBasic Info:")
        print(f"  Name: {skill['name'] or skill_name}")
        print(f"  Version: {skill['version'] or 'unknown'}")
        print(f"  Description: {skill['description'] or 'No description'}")
        print(f"  Author: {skill['author'] or 'Unknown'}")

        print(f"\nStatus:")
        print(f"  {status}")
        print(f"  Auto-activate: {'Yes' if skill['auto_activate'] else 'No'}")

        if skill['permissions']:
            print(f"\nPermissions ({len(skill['permissions'])}):")
            for perm in skill['permissions']:
                print(f"  ✅ {perm}")
        else:
            print(f"\nPermissions: None configured")

        if skill['tags']:
            print(f"\nTags:")
            print(f"  {', '.join(skill['tags'])}")

        print()

    def export_config(self) -> None:
        """Export current skill configuration as JSON"""
        skills = self.discover_skills()

        config = {
            'version': '1.0.0',
            'project_root': str(self.project_root),
            'skills': {}
        }

        for skill in skills:
            config['skills'][skill['skill_name']] = {
                'enabled': skill['enabled'],
                'version': skill['version'],
                'permissions': skill['permissions']
            }

        print(json.dumps(config, indent=2))

    def output_json(self) -> None:
        """Output skill discovery results as JSON (for Claude to parse)"""
        skills = self.discover_skills()
        print(json.dumps(skills, indent=2))

    # ============================================
    # ENHANCED FEATURES - Comprehensive Management
    # ============================================

    def toggle_auto_activate(self, skill_name: str, enable: bool) -> bool:
        """Toggle auto-activate setting for a skill"""
        skill_dir = self.skills_dir / skill_name
        skill_md = skill_dir / 'skill.md'

        if not skill_md.exists():
            print(f"❌ Skill '{skill_name}' not found")
            return False

        try:
            with open(skill_md, 'r', encoding='utf-8') as f:
                content = f.read()

            # Update auto-activate in frontmatter
            new_value = 'true' if enable else 'false'
            updated = re.sub(
                r'(auto-activate|auto_activate):\s*(true|false)',
                f'auto-activate: {new_value}',
                content
            )

            with open(skill_md, 'w', encoding='utf-8') as f:
                f.write(updated)

            status = "enabled" if enable else "disabled"
            print(f"✅ Auto-activate {status} for {skill_name}")
            return True

        except Exception as e:
            print(f"❌ Error updating auto-activate: {e}", file=sys.stderr)
            return False

    def add_permission(self, skill_name: str, permission: str) -> bool:
        """Add a specific permission for a skill"""
        settings = self._load_settings()
        if not settings:
            settings = {'permissions': {'allow': [], 'deny': [], 'ask': []}}

        allow_list = settings.get('permissions', {}).get('allow', [])

        if permission in allow_list:
            print(f"Permission '{permission}' already exists")
            return False

        allow_list.append(permission)
        settings['permissions']['allow'] = allow_list

        if self._save_settings(settings):
            print(f"✅ Added permission: {permission}")
            return True
        return False

    def remove_permission(self, skill_name: str, permission: str) -> bool:
        """Remove a specific permission for a skill"""
        settings = self._load_settings()
        if not settings:
            print(f"No settings file found")
            return False

        allow_list = settings.get('permissions', {}).get('allow', [])

        if permission not in allow_list:
            print(f"Permission '{permission}' not found")
            return False

        allow_list.remove(permission)
        settings['permissions']['allow'] = allow_list

        if self._save_settings(settings):
            print(f"✅ Removed permission: {permission}")
            return True
        return False

    def list_permissions(self, skill_name: str) -> None:
        """List all permissions for a specific skill"""
        permissions = self._get_skill_permissions(skill_name)

        if not permissions:
            print(f"No permissions configured for '{skill_name}'")
            return

        print(f"\n🔐 Permissions for {skill_name}:\n")
        for i, perm in enumerate(permissions, 1):
            print(f"  {i}. {perm}")
        print()

    def add_tag(self, skill_name: str, tag: str) -> bool:
        """Add a tag to a skill"""
        skill_dir = self.skills_dir / skill_name
        skill_md = skill_dir / 'skill.md'

        if not skill_md.exists():
            print(f"❌ Skill '{skill_name}' not found")
            return False

        try:
            with open(skill_md, 'r', encoding='utf-8') as f:
                content = f.read()

            # Find tags line and add new tag
            def add_tag_to_line(match):
                tags_content = match.group(1).strip()
                if tags_content.endswith(']'):
                    # Remove closing bracket, add tag, add bracket
                    tags_content = tags_content[:-1].strip()
                    if tags_content:
                        return f'tags: [{tags_content}, {tag}]'
                    else:
                        return f'tags: [{tag}]'
                return match.group(0)

            updated = re.sub(r'tags:\s*\[(.*?)\]', add_tag_to_line, content)

            with open(skill_md, 'w', encoding='utf-8') as f:
                f.write(updated)

            print(f"✅ Added tag '{tag}' to {skill_name}")
            return True

        except Exception as e:
            print(f"❌ Error adding tag: {e}", file=sys.stderr)
            return False

    def remove_tag(self, skill_name: str, tag: str) -> bool:
        """Remove a tag from a skill"""
        skill_dir = self.skills_dir / skill_name
        skill_md = skill_dir / 'skill.md'

        if not skill_md.exists():
            print(f"❌ Skill '{skill_name}' not found")
            return False

        try:
            with open(skill_md, 'r', encoding='utf-8') as f:
                content = f.read()

            # Remove tag from tags array
            def remove_tag_from_line(match):
                tags_content = match.group(1)
                tags_list = [t.strip() for t in tags_content.split(',')]
                tags_list = [t for t in tags_list if t != tag]
                return f'tags: [{", ".join(tags_list)}]'

            updated = re.sub(r'tags:\s*\[(.*?)\]', remove_tag_from_line, content)

            with open(skill_md, 'w', encoding='utf-8') as f:
                f.write(updated)

            print(f"✅ Removed tag '{tag}' from {skill_name}")
            return True

        except Exception as e:
            print(f"❌ Error removing tag: {e}", file=sys.stderr)
            return False

    def set_priority(self, skill_name: str, priority: int) -> bool:
        """Set execution priority for a skill (1-10, higher = more important)"""
        skill_dir = self.skills_dir / skill_name
        skill_md = skill_dir / 'skill.md'

        if not skill_md.exists():
            print(f"❌ Skill '{skill_name}' not found")
            return False

        if not 1 <= priority <= 10:
            print(f"❌ Priority must be between 1 and 10")
            return False

        try:
            with open(skill_md, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check if priority field exists
            if 'priority:' in content:
                # Update existing priority
                updated = re.sub(r'priority:\s*\d+', f'priority: {priority}', content)
            else:
                # Add priority field after tags
                updated = re.sub(
                    r'(tags:.*?\])\n',
                    f'\\1\npriority: {priority}\n',
                    content
                )

            with open(skill_md, 'w', encoding='utf-8') as f:
                f.write(updated)

            print(f"✅ Set priority {priority} for {skill_name}")
            return True

        except Exception as e:
            print(f"❌ Error setting priority: {e}", file=sys.stderr)
            return False

    def configure_skill(self, skill_name: str, key: str, value: str) -> bool:
        """Set a configuration parameter for a skill"""
        skill_dir = self.skills_dir / skill_name
        skill_md = skill_dir / 'skill.md'

        if not skill_md.exists():
            print(f"❌ Skill '{skill_name}' not found")
            return False

        try:
            with open(skill_md, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check if config section exists
            if '## Configuration' not in content:
                # Add configuration section
                content += f"\n\n## Configuration\n\n{key}: {value}\n"
            else:
                # Update or add config parameter
                if f'{key}:' in content:
                    content = re.sub(
                        f'{key}:.*',
                        f'{key}: {value}',
                        content
                    )
                else:
                    content = content.replace(
                        '## Configuration',
                        f'## Configuration\n\n{key}: {value}'
                    )

            with open(skill_md, 'w', encoding='utf-8') as f:
                f.write(content)

            print(f"✅ Set {key}={value} for {skill_name}")
            return True

        except Exception as e:
            print(f"❌ Error configuring skill: {e}", file=sys.stderr)
            return False

    def show_advanced_config(self, skill_name: str) -> None:
        """Show advanced configuration options for a skill"""
        skills = self.discover_skills()
        skill = next((s for s in skills if s['skill_name'] == skill_name), None)

        if not skill:
            print(f"❌ Skill '{skill_name}' not found")
            return

        print(f"\n⚙️  Advanced Configuration: {skill_name}")
        print("=" * 60)
        print(f"\n📋 Current Settings:")
        print(f"  Auto-activate: {'Yes' if skill['auto_activate'] else 'No'}")
        print(f"  Tags: {', '.join(skill['tags']) if skill['tags'] else 'None'}")
        print(f"  Enabled: {'Yes' if skill['enabled'] else 'No'}")
        print(f"  Permissions: {len(skill['permissions'])} configured")

        # Show feature toggles if available
        skill_md = self.skills_dir / skill_name / 'skill.md'
        if skill_md.exists():
            try:
                with open(skill_md, 'r', encoding='utf-8') as f:
                    content = f.read()
                import re
                feature_match = re.search(r'feature_config:\s*\n((?:  \w+: (?:enabled|disabled)\s*\n)+)', content)
                if feature_match:
                    print(f"\n🎛️  Feature Toggles:")
                    features = feature_match.group(1)
                    feature_lines = [line.strip() for line in features.split('\n') if line.strip()]
                    for line in feature_lines:
                        feature_name, status = line.split(':')
                        icon = "✅" if status.strip() == "enabled" else "⬜"
                        print(f"  {icon} {feature_name.strip()} - {status.strip().upper()}")
            except:
                pass

        print(f"\n🔧 Available Operations:")
        print(f"  1. Toggle auto-activate")
        print(f"  2. Add/remove tags")
        print(f"  3. Set priority (1-10)")
        print(f"  4. Manage permissions")
        print(f"  5. Configure parameters")
        print()

    def list_features(self, skill_name: str) -> None:
        """List all feature toggles for a skill"""
        skill_dir = self.skills_dir / skill_name
        skill_md = skill_dir / 'skill.md'

        if not skill_md.exists():
            print(f"❌ Skill '{skill_name}' not found")
            return

        try:
            with open(skill_md, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract feature_config section
            import re
            feature_match = re.search(r'feature_config:\s*\n((?:  \w+: (?:enabled|disabled)\s*\n)+)', content)

            if not feature_match:
                print(f"⬜ No feature toggles configured for {skill_name}")
                return

            print(f"\n🎛️  Feature Toggles: {skill_name}")
            print("=" * 60)

            features = feature_match.group(1)
            feature_lines = [line.strip() for line in features.split('\n') if line.strip()]

            for idx, line in enumerate(feature_lines, 1):
                feature_name, status = line.split(':')
                feature_name = feature_name.strip()
                status = status.strip()
                icon = "✅" if status == "enabled" else "⬜"
                print(f"  {idx}. {icon} {feature_name} - {status.upper()}")

            print()

        except Exception as e:
            print(f"❌ Error reading features: {e}", file=sys.stderr)

    def toggle_feature(self, skill_name: str, feature_name: str) -> bool:
        """Toggle a feature (enabled <-> disabled)"""
        skill_dir = self.skills_dir / skill_name
        skill_md = skill_dir / 'skill.md'

        if not skill_md.exists():
            print(f"❌ Skill '{skill_name}' not found")
            return False

        try:
            with open(skill_md, 'r', encoding='utf-8') as f:
                content = f.read()

            # Find current status
            import re
            pattern = rf'(\s+{re.escape(feature_name)}:\s*)(enabled|disabled)'
            match = re.search(pattern, content)

            if not match:
                print(f"❌ Feature '{feature_name}' not found in {skill_name}")
                return False

            # Toggle the status
            current_status = match.group(2)
            new_status = 'disabled' if current_status == 'enabled' else 'enabled'

            # Replace in content
            updated = re.sub(pattern, rf'\1{new_status}', content)

            # Write back
            with open(skill_md, 'w', encoding='utf-8') as f:
                f.write(updated)

            print(f"✅ Toggled {feature_name}: {current_status} → {new_status}")
            return True

        except Exception as e:
            print(f"❌ Error toggling feature: {e}", file=sys.stderr)
            return False

    def set_feature(self, skill_name: str, feature_name: str, enable: bool) -> bool:
        """Set a feature to enabled or disabled"""
        skill_dir = self.skills_dir / skill_name
        skill_md = skill_dir / 'skill.md'

        if not skill_md.exists():
            print(f"❌ Skill '{skill_name}' not found")
            return False

        try:
            with open(skill_md, 'r', encoding='utf-8') as f:
                content = f.read()

            # Find and replace status
            import re
            pattern = rf'(\s+{re.escape(feature_name)}:\s*)(enabled|disabled)'
            match = re.search(pattern, content)

            if not match:
                print(f"❌ Feature '{feature_name}' not found in {skill_name}")
                return False

            new_status = 'enabled' if enable else 'disabled'
            updated = re.sub(pattern, rf'\1{new_status}', content)

            # Write back
            with open(skill_md, 'w', encoding='utf-8') as f:
                f.write(updated)

            status_text = "enabled" if enable else "disabled"
            print(f"✅ {feature_name} {status_text}")
            return True

        except Exception as e:
            print(f"❌ Error setting feature: {e}", file=sys.stderr)
            return False

    def generate_abbreviation(self, name: str, prefix_type: str = 'S') -> str:
        """
        Generate 3-letter abbreviation from skill/agent name

        Algorithm:
        1. Check for special cases first
        2. Remove common words (helper, manager, agent, skill)
        3. Extract key words
        4. Take first 3 consonants from combined key words
        5. Pad with _ if < 3 characters

        Args:
            name: Skill or agent name
            prefix_type: 'S' for skill, 'A' for agent

        Returns:
            Full prefix like '[S:cli]' or '[A:esf]'
        """
        # Normalize name
        original_name = name
        name = name.lower().replace('_', '-')

        # Special cases for common patterns
        special_cases = {
            'cli-modern-tools': 'cli',
            'eslint-fixer': 'esf',
            'changelog-manager': 'chn',
            'sql-cli': 'sql',
            'pest-test-generator': 'peg',  # Pest gEnerator
            'pest-test-runner': 'per',      # Pest Euner
            'playwright-test-generator': 'pwg',  # PlayWright Generator
            'playwright-test-healer': 'pwh',
            'playwright-test-planner': 'pwp',
        }

        if name in special_cases:
            abbrev = special_cases[name]
            return f"[{prefix_type}:{abbrev}]"

        # Remove common suffixes/words but keep meaningful parts
        stop_words = ['helper', 'manager', 'agent', 'skill']
        words = name.split('-')
        key_words = [w for w in words if w not in stop_words]

        # If all words removed, use original
        if not key_words:
            key_words = words

        # Generate abbreviation from consonants of key words
        combined = ''.join(key_words)
        consonants = ''.join(c for c in combined if c not in 'aeiou')

        if len(consonants) >= 3:
            abbrev = consonants[:3]
        else:
            # Fallback: use first 3 chars of combined key words
            abbrev = combined[:3]

        # Pad if needed
        abbrev = abbrev[:3].ljust(3, '_')

        return f"[{prefix_type}:{abbrev}]"

    def discover_agents(self) -> List[Dict[str, Any]]:
        """Discover all agents in generic-claude-framework/agents/ directory"""
        agents = []
        agents_dir = self.project_root / 'generic-claude-framework' / 'agents'

        if not agents_dir.exists():
            # Try .claude/agents as fallback
            agents_dir = self.project_root / '.claude' / 'agents'
            if not agents_dir.exists():
                return agents

        for agent_dir in agents_dir.iterdir():
            if not agent_dir.is_dir():
                continue

            agent_md = agent_dir / 'agent.md'
            if not agent_md.exists():
                continue

            # Parse agent metadata (similar to skills)
            metadata = self._parse_skill_metadata(agent_md)
            metadata['agent_name'] = agent_dir.name
            metadata['agent_path'] = str(agent_dir)
            agents.append(metadata)

        return agents

    def generate_task_prefix_mapping(self) -> Dict[str, str]:
        """
        Generate complete task prefix mapping for all skills and agents

        Returns:
            Dictionary with skill/agent names as keys and prefixes as values
        """
        mapping = {}

        # Discover skills
        skills = self.discover_skills()
        for skill in skills:
            name = skill['skill_name']
            prefix = self.generate_abbreviation(name, 'S')
            mapping[name] = prefix

        # Discover agents
        agents = self.discover_agents()
        for agent in agents:
            name = agent['agent_name']
            prefix = self.generate_abbreviation(name, 'A')
            mapping[name] = prefix

        return mapping

    def add_claude_md_rule(self, rule_name: str) -> bool:
        """
        Add recommended rule to CLAUDE.md file

        Args:
            rule_name: Name of rule to add ('task-prefix', 'bash-attribution', 'minimal-commentary')

        Returns:
            True if successful, False otherwise
        """
        claude_md = self.project_root / 'CLAUDE.md'

        if not claude_md.exists():
            print(f"❌ CLAUDE.md not found at {claude_md}")
            return False

        try:
            with open(claude_md, 'r', encoding='utf-8') as f:
                content = f.read()

            if rule_name == 'task-prefix':
                # Check if rule already exists
                if '## Task Prefix System' in content:
                    print(f"⚠️  Task Prefix System already exists in CLAUDE.md")
                    return False

                # Generate mapping
                mapping = self.generate_task_prefix_mapping()

                # Build rule section
                rule_section = "\n\n## Task Prefix System\n\n"
                rule_section += "**CRITICAL: When creating tasks with TodoWrite, prefix content with skill/agent identifier**\n\n"
                rule_section += "This helps users understand which skill/agent is creating which task in the Claude CLI.\n\n"
                rule_section += "### Prefix Format\n"
                rule_section += "- Skills: `[S:xxx]` where xxx is 3-letter abbreviation\n"
                rule_section += "- Agents: `[A:xxx]` where xxx is 3-letter abbreviation\n\n"
                rule_section += "### Complete Mapping Table\n\n"
                rule_section += "**Skills:**\n"

                # Sort skills
                skills = {k: v for k, v in mapping.items() if v.startswith('[S:')}
                for name in sorted(skills.keys()):
                    prefix = skills[name]
                    rule_section += f"- `{prefix}` - {name}\n"

                rule_section += "\n**Agents:**\n"

                # Sort agents
                agents = {k: v for k, v in mapping.items() if v.startswith('[A:')}
                for name in sorted(agents.keys()):
                    prefix = agents[name]
                    rule_section += f"- `{prefix}` - {name}\n"

                rule_section += "\n### Usage Examples\n\n"
                rule_section += "```python\n"
                rule_section += "# Skill creating tasks\n"
                rule_section += 'TodoWrite(todos=[{\n'
                rule_section += '    "content": "[S:cli] Check if eza is installed",\n'
                rule_section += '    "status": "pending",\n'
                rule_section += '    "activeForm": "Checking eza installation"\n'
                rule_section += "}])\n\n"
                rule_section += "# Agent creating tasks\n"
                rule_section += 'TodoWrite(todos=[{\n'
                rule_section += '    "content": "[A:esf] Fix ESLint errors in src/",\n'
                rule_section += '    "status": "in_progress",\n'
                rule_section += '    "activeForm": "Fixing ESLint errors"\n'
                rule_section += "}])\n"
                rule_section += "```\n\n"
                rule_section += "### Rules\n"
                rule_section += "- **ALWAYS prefix** task content when skill/agent creates task\n"
                rule_section += "- **Use exact prefix** from mapping table above\n"
                rule_section += "- **Pad with underscore** if abbreviation < 3 chars (e.g., `[S:sql_]`)\n"
                rule_section += "- **User-created tasks** don't need prefix (only skill/agent tasks)\n\n"

                # Find good insertion point (after Communication Style if exists, otherwise end)
                if '## 🔧 Tool Usage Guidelines' in content:
                    # Insert before Tool Usage Guidelines
                    content = content.replace('## 🔧 Tool Usage Guidelines', rule_section + '## 🔧 Tool Usage Guidelines')
                else:
                    # Append to end
                    content += rule_section

                # Write back
                with open(claude_md, 'w', encoding='utf-8') as f:
                    f.write(content)

                print(f"✅ Added Task Prefix System to CLAUDE.md")
                print(f"📊 Generated {len(mapping)} prefixes ({len(skills)} skills, {len(agents)} agents)")
                return True

            elif rule_name == 'remove-task-prefix':
                # Remove task prefix section
                if '## Task Prefix System' not in content:
                    print(f"⚠️  Task Prefix System not found in CLAUDE.md")
                    return False

                # Find and remove section (until next ## heading)
                pattern = r'\n\n## Task Prefix System\n\n.*?(?=\n\n##|\Z)'
                content = re.sub(pattern, '', content, flags=re.DOTALL)

                # Write back
                with open(claude_md, 'w', encoding='utf-8') as f:
                    f.write(content)

                print(f"✅ Removed Task Prefix System from CLAUDE.md")
                return True

            else:
                print(f"❌ Unknown rule: {rule_name}")
                return False

        except Exception as e:
            print(f"❌ Error modifying CLAUDE.md: {e}", file=sys.stderr)
            return False


def main():
    parser = argparse.ArgumentParser(description='Skill Manager - Comprehensive skill management for Claude Code')
    parser.add_argument('action',
                       choices=['discover', 'list', 'enable', 'disable', 'status', 'export', 'json',
                               'auto-activate', 'add-permission', 'remove-permission', 'list-permissions',
                               'add-tag', 'remove-tag', 'set-priority', 'configure', 'advanced',
                               'list-features', 'toggle-feature', 'enable-feature', 'disable-feature',
                               'generate-abbreviation', 'show-task-prefixes', 'add-task-prefix-rule', 'remove-task-prefix-rule'],
                       help='Action to perform')
    parser.add_argument('skill_name', nargs='?', help='Skill name')
    parser.add_argument('value', nargs='?', help='Value for the action (permission, tag, priority, config key)')
    parser.add_argument('value2', nargs='?', help='Second value (for configure: config value)')
    parser.add_argument('--filter', choices=['all', 'enabled', 'disabled'], default='all',
                       help='Filter skills by status (for list command)')
    parser.add_argument('--on', action='store_true', help='Enable flag (for auto-activate)')
    parser.add_argument('--off', action='store_true', help='Disable flag (for auto-activate)')
    parser.add_argument('--project-root', help='Project root directory')

    args = parser.parse_args()

    manager = SkillManager(project_root=args.project_root)

    # Original actions
    if args.action == 'discover':
        manager.list_skills()
    elif args.action == 'list':
        manager.list_skills(filter_type=args.filter)
    elif args.action == 'enable':
        if not args.skill_name:
            print("❌ Error: skill_name required for enable action")
            sys.exit(1)
        manager.enable_skill(args.skill_name)
    elif args.action == 'disable':
        if not args.skill_name:
            print("❌ Error: skill_name required for disable action")
            sys.exit(1)
        manager.disable_skill(args.skill_name)
    elif args.action == 'status':
        if not args.skill_name:
            print("❌ Error: skill_name required for status action")
            sys.exit(1)
        manager.show_skill_details(args.skill_name)
    elif args.action == 'export':
        manager.export_config()
    elif args.action == 'json':
        manager.output_json()

    # New enhanced actions
    elif args.action == 'auto-activate':
        if not args.skill_name:
            print("❌ Error: skill_name required")
            sys.exit(1)
        if args.on:
            manager.toggle_auto_activate(args.skill_name, True)
        elif args.off:
            manager.toggle_auto_activate(args.skill_name, False)
        else:
            print("❌ Error: Use --on or --off flag")
            sys.exit(1)

    elif args.action == 'add-permission':
        if not args.skill_name or not args.value:
            print("❌ Error: skill_name and permission required")
            sys.exit(1)
        manager.add_permission(args.skill_name, args.value)

    elif args.action == 'remove-permission':
        if not args.skill_name or not args.value:
            print("❌ Error: skill_name and permission required")
            sys.exit(1)
        manager.remove_permission(args.skill_name, args.value)

    elif args.action == 'list-permissions':
        if not args.skill_name:
            print("❌ Error: skill_name required")
            sys.exit(1)
        manager.list_permissions(args.skill_name)

    elif args.action == 'add-tag':
        if not args.skill_name or not args.value:
            print("❌ Error: skill_name and tag required")
            sys.exit(1)
        manager.add_tag(args.skill_name, args.value)

    elif args.action == 'remove-tag':
        if not args.skill_name or not args.value:
            print("❌ Error: skill_name and tag required")
            sys.exit(1)
        manager.remove_tag(args.skill_name, args.value)

    elif args.action == 'set-priority':
        if not args.skill_name or not args.value:
            print("❌ Error: skill_name and priority (1-10) required")
            sys.exit(1)
        try:
            priority = int(args.value)
            manager.set_priority(args.skill_name, priority)
        except ValueError:
            print("❌ Error: Priority must be a number between 1 and 10")
            sys.exit(1)

    elif args.action == 'configure':
        if not args.skill_name or not args.value or not args.value2:
            print("❌ Error: skill_name, config_key, and config_value required")
            print("Usage: skill-manager.py configure <skill_name> <key> <value>")
            sys.exit(1)
        manager.configure_skill(args.skill_name, args.value, args.value2)

    elif args.action == 'advanced':
        if not args.skill_name:
            print("❌ Error: skill_name required")
            sys.exit(1)
        manager.show_advanced_config(args.skill_name)

    elif args.action == 'list-features':
        if not args.skill_name:
            print("❌ Error: skill_name required")
            sys.exit(1)
        manager.list_features(args.skill_name)

    elif args.action == 'toggle-feature':
        if not args.skill_name or not args.value:
            print("❌ Error: skill_name and feature_name required")
            print("Usage: skill-manager.py toggle-feature <skill_name> <feature_name>")
            sys.exit(1)
        manager.toggle_feature(args.skill_name, args.value)

    elif args.action == 'enable-feature':
        if not args.skill_name or not args.value:
            print("❌ Error: skill_name and feature_name required")
            print("Usage: skill-manager.py enable-feature <skill_name> <feature_name>")
            sys.exit(1)
        manager.set_feature(args.skill_name, args.value, True)

    elif args.action == 'disable-feature':
        if not args.skill_name or not args.value:
            print("❌ Error: skill_name and feature_name required")
            print("Usage: skill-manager.py disable-feature <skill_name> <feature_name>")
            sys.exit(1)
        manager.set_feature(args.skill_name, args.value, False)

    # Task Prefix System actions
    elif args.action == 'generate-abbreviation':
        if not args.skill_name:
            print("❌ Error: skill_name required")
            print("Usage: skill-manager.py generate-abbreviation <skill_name> [--agent]")
            sys.exit(1)
        prefix_type = 'A' if args.value == 'agent' else 'S'
        abbrev = manager.generate_abbreviation(args.skill_name, prefix_type)
        print(f"✅ Generated abbreviation: {abbrev}")

    elif args.action == 'show-task-prefixes':
        mapping = manager.generate_task_prefix_mapping()
        print("\n📋 Task Prefix Mapping")
        print("=" * 60)
        print("\n🔧 Skills:")
        for name in sorted([k for k, v in mapping.items() if v.startswith('[S:')]):
            print(f"  {mapping[name]} - {name}")
        print("\n🤖 Agents:")
        for name in sorted([k for k, v in mapping.items() if v.startswith('[A:')]):
            print(f"  {mapping[name]} - {name}")
        print(f"\n📊 Total: {len(mapping)} prefixes")

    elif args.action == 'add-task-prefix-rule':
        manager.add_claude_md_rule('task-prefix')

    elif args.action == 'remove-task-prefix-rule':
        manager.add_claude_md_rule('remove-task-prefix')


if __name__ == '__main__':
    main()
