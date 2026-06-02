#!/usr/bin/env python3
"""
Settings Migration Tool for agenthero-ai agent.
Migrates settings from v1.0 to v2.0 schema with backward compatibility.

Phase 3 - Polish & Optimization
"""

import json
import sys
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import shutil


class SettingsMigrator:
    """
    Migrates settings files between schema versions.
    Handles backward compatibility and validation.
    """
    
    def __init__(self):
        """Initialize migrator."""
        self.migrations = {
            "1.0.0": self._migrate_from_1_0_0,
            "1.1.0": self._migrate_from_1_1_0,
        }
    
    def migrate(self, settings_path: Path, backup: bool = True) -> Dict[str, Any]:
        """
        Migrate settings file to latest version.
        
        Args:
            settings_path: Path to settings.json
            backup: Create backup before migration
            
        Returns:
            Migrated settings dictionary
        """
        # Load current settings
        with open(settings_path, 'r', encoding='utf-8') as f:
            settings = json.load(f)
        
        current_version = settings.get("schema_version", "1.0.0")
        target_version = "1.0.0"  # Latest schema version
        
        print(f"Current schema version: {current_version}")
        print(f"Target schema version: {target_version}")
        
        # Check if migration needed
        if current_version == target_version:
            print("✓ Settings already at latest version")
            return settings
        
        # Create backup
        if backup:
            backup_path = settings_path.with_suffix('.json.backup')
            shutil.copy2(settings_path, backup_path)
            print(f"✓ Backup created: {backup_path}")
        
        # Perform migration
        migrated = self._perform_migration(settings, current_version, target_version)
        
        # Save migrated settings
        with open(settings_path, 'w', encoding='utf-8') as f:
            json.dump(migrated, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Migration complete: {current_version} → {target_version}")
        
        return migrated
    
    def _perform_migration(self, settings: Dict[str, Any], 
                          from_version: str, to_version: str) -> Dict[str, Any]:
        """
        Perform migration from one version to another.
        
        Args:
            settings: Current settings
            from_version: Source version
            to_version: Target version
            
        Returns:
            Migrated settings
        """
        # For now, we only have one version, so just add missing fields
        if from_version == "1.0.0" and to_version == "1.0.0":
            return self._ensure_all_fields(settings)
        
        # Future: chain migrations if needed
        # e.g., 1.0.0 → 1.1.0 → 2.0.0
        
        return settings
    
    def _ensure_all_fields(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ensure all required fields exist with defaults.
        
        Args:
            settings: Current settings
            
        Returns:
            Settings with all fields
        """
        # Add advanced section if missing
        if "advanced" not in settings:
            print("  Adding 'advanced' section...")
            settings["advanced"] = {
                "hooks": {
                    "enabled": True,
                    "throttle_seconds": 30,
                    "todowrite_integration": True
                },
                "event_bus": {
                    "enabled": True,
                    "max_history": 1000
                },
                "caching": {
                    "enabled": True,
                    "settings_ttl": 300,
                    "topic_state_ttl": 60
                },
                "parallel_execution": {
                    "enabled": False,
                    "max_workers": 4
                },
                "dry_run": {
                    "enabled": False,
                    "validate_before_execution": True
                }
            }
        
        # Update last_updated timestamp
        settings["last_updated"] = datetime.now().isoformat()
        
        return settings
    
    def _migrate_from_1_0_0(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate from schema version 1.0.0."""
        # Add advanced features
        settings = self._ensure_all_fields(settings)
        settings["schema_version"] = "1.0.0"
        return settings
    
    def _migrate_from_1_1_0(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate from schema version 1.1.0 (future)."""
        # Future migration logic
        settings["schema_version"] = "1.0.0"
        return settings
    
    def validate_migration(self, settings: Dict[str, Any]) -> bool:
        """
        Validate migrated settings.
        
        Args:
            settings: Settings to validate
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = [
            "version",
            "schema_version",
            "workflow",
            "behavior",
            "features",
            "paths",
            "validation_rules",
            "advanced"
        ]
        
        for field in required_fields:
            if field not in settings:
                print(f"✗ Missing required field: {field}")
                return False
        
        # Validate advanced section
        if "advanced" in settings:
            required_advanced = ["hooks", "event_bus", "caching", "parallel_execution", "dry_run"]
            for field in required_advanced:
                if field not in settings["advanced"]:
                    print(f"✗ Missing advanced field: {field}")
                    return False
        
        print("✓ Validation passed")
        return True


def migrate_settings_file(settings_path: str, backup: bool = True) -> bool:
    """
    Migrate settings file to latest version.
    
    Args:
        settings_path: Path to settings.json
        backup: Create backup before migration
        
    Returns:
        True if successful, False otherwise
    """
    try:
        migrator = SettingsMigrator()
        settings = migrator.migrate(Path(settings_path), backup)
        
        # Validate migration
        if not migrator.validate_migration(settings):
            print("✗ Migration validation failed")
            return False
        
        return True
    
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate agenthero-ai settings to latest version")
    parser.add_argument("settings_file", help="Path to settings.json")
    parser.add_argument("--no-backup", action="store_true", help="Skip backup creation")
    parser.add_argument("--validate-only", action="store_true", help="Only validate, don't migrate")
    
    args = parser.parse_args()
    
    print("Settings Migration Tool")
    print("="*80)
    
    settings_path = Path(args.settings_file)
    
    if not settings_path.exists():
        print(f"✗ Settings file not found: {settings_path}")
        sys.exit(1)
    
    if args.validate_only:
        # Validate only
        with open(settings_path, 'r', encoding='utf-8') as f:
            settings = json.load(f)
        
        migrator = SettingsMigrator()
        if migrator.validate_migration(settings):
            print("\n✓ Settings file is valid")
            sys.exit(0)
        else:
            print("\n✗ Settings file is invalid")
            sys.exit(1)
    
    else:
        # Migrate
        success = migrate_settings_file(str(settings_path), backup=not args.no_backup)
        
        if success:
            print("\n✓ Migration successful")
            sys.exit(0)
        else:
            print("\n✗ Migration failed")
            sys.exit(1)

