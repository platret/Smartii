#!/usr/bin/env python3
"""
Lark Agent - Interactive CLI Mode
Provides an interactive conversational interface for creating Lark tasks

This script supports two modes:
1. Topic Mode: Generate test plan from a topic description
2. File Mode: Process existing markdown file

It prompts for all necessary information before proceeding.
"""

import sys
import os
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Import our modules
from markdown_parser import MarkdownParser
from lark_task_creator import LarkTaskCreator
from lark_task_verifier import LarkTaskVerifier

class InteractiveLarkAgent:
    """Interactive CLI interface for Lark Agent"""
    
    def __init__(self):
        self.mode = None  # 'topic' or 'file'
        self.config = {}
        
    def print_banner(self):
        """Print welcome banner"""
        print("\n" + "="*70)
        print("🚀 LARK AGENT - INTERACTIVE MODE")
        print("="*70)
        print("\nConvert test plans into hierarchical Lark tasks")
        print("Supports: Topic-based generation OR Markdown file processing\n")
    
    def prompt_mode(self) -> str:
        """Prompt user to select mode"""
        print("📋 How would you like to create your test plan?\n")
        print("  1. Generate from topic (AI-powered test plan generation)")
        print("  2. Use existing markdown file\n")
        
        while True:
            choice = input("Select mode (1 or 2): ").strip()
            if choice == '1':
                return 'topic'
            elif choice == '2':
                return 'file'
            else:
                print("❌ Invalid choice. Please enter 1 or 2.")
    
    def prompt_topic(self) -> str:
        """Prompt for test plan topic"""
        print("\n" + "="*70)
        print("📝 TEST PLAN TOPIC")
        print("="*70)
        print("\nDescribe what you want to test. Be as detailed as possible.")
        print("Example: 'User login functionality with email and password'\n")
        
        topic = input("Test plan topic: ").strip()
        
        if not topic:
            print("❌ Topic cannot be empty")
            return self.prompt_topic()
        
        return topic
    
    def prompt_file_path(self) -> Path:
        """Prompt for markdown file path"""
        print("\n" + "="*70)
        print("📁 MARKDOWN FILE")
        print("="*70)
        print("\nEnter the path to your markdown test file")
        print("Example: tests/manual/login-test.md\n")
        
        file_path = input("File path: ").strip()
        
        if not file_path:
            print("❌ File path cannot be empty")
            return self.prompt_file_path()
        
        path = Path(file_path)
        if not path.exists():
            print(f"❌ File not found: {file_path}")
            retry = input("Try again? (y/n): ").strip().lower()
            if retry == 'y':
                return self.prompt_file_path()
            else:
                sys.exit(1)
        
        return path
    
    def prompt_task_list_id(self) -> Optional[str]:
        """Prompt for Lark task list ID"""
        print("\n" + "="*70)
        print("📋 LARK TASK LIST")
        print("="*70)
        print("\nDo you want to use an existing Lark task list?")
        print("  - Enter task list ID to use existing")
        print("  - Press Enter to create a new task list\n")
        
        task_list_id = input("Task list ID (or Enter for new): ").strip()
        
        return task_list_id if task_list_id else None
    
    def prompt_target_date(self) -> str:
        """Prompt for target completion date"""
        print("\n" + "="*70)
        print("📅 TARGET COMPLETION DATE")
        print("="*70)
        
        default_date = (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d')
        print(f"\nWhen should this test be completed?")
        print(f"Default: {default_date} (14 days from now)\n")
        
        date_input = input(f"Target date (YYYY-MM-DD) or Enter for default: ").strip()
        
        if not date_input:
            return default_date
        
        # Validate date format
        try:
            datetime.strptime(date_input, '%Y-%m-%d')
            return date_input
        except ValueError:
            print("❌ Invalid date format. Please use YYYY-MM-DD")
            return self.prompt_target_date()
    
    def prompt_owner(self) -> str:
        """Prompt for task owner"""
        print("\n" + "="*70)
        print("👤 TASK OWNER")
        print("="*70)
        print("\nWho should be assigned to these tasks?")
        print("Default: Test User\n")
        
        owner = input("Owner name (or Enter for default): ").strip()
        
        return owner if owner else "Test User"
    
    def prompt_priority(self) -> str:
        """Prompt for task priority"""
        print("\n" + "="*70)
        print("⚡ TASK PRIORITY")
        print("="*70)
        print("\nWhat priority should these tasks have?")
        print("  1. Low")
        print("  2. Medium (default)")
        print("  3. High\n")
        
        choice = input("Select priority (1-3) or Enter for default: ").strip()
        
        priority_map = {'1': 'low', '2': 'medium', '3': 'high', '': 'medium'}
        return priority_map.get(choice, 'medium')
    
    def confirm_configuration(self) -> bool:
        """Display configuration and ask for confirmation"""
        print("\n" + "="*70)
        print("✅ CONFIGURATION SUMMARY")
        print("="*70)
        
        print(f"\n📋 Mode: {self.config['mode'].upper()}")
        
        if self.config['mode'] == 'topic':
            print(f"📝 Topic: {self.config['topic']}")
        else:
            print(f"📁 File: {self.config['file_path']}")
        
        if self.config.get('task_list_id'):
            print(f"📋 Task List ID: {self.config['task_list_id']}")
        else:
            print(f"📋 Task List: Create new")
        
        print(f"📅 Target Date: {self.config['target_date']}")
        print(f"👤 Owner: {self.config['owner']}")
        print(f"⚡ Priority: {self.config['priority']}")
        
        print("\n" + "="*70)
        confirm = input("\nProceed with this configuration? (y/n): ").strip().lower()
        
        return confirm == 'y'
    
    def generate_test_plan_from_topic(self, topic: str) -> str:
        """
        Generate test plan markdown from topic
        
        This will be executed by Claude Code using AI capabilities
        Returns a request for Claude Code to generate the markdown
        """
        print("\n" + "="*70)
        print("🤖 GENERATING TEST PLAN")
        print("="*70)
        print(f"\nTopic: {topic}")
        print("\nClaude Code will now generate a comprehensive test plan...")
        print("This includes:")
        print("  - Test overview and objectives")
        print("  - Test scenarios")
        print("  - Detailed test tasks with steps")
        print("  - Expected results\n")
        
        # Return a marker for Claude Code to process
        return {
            'action': 'generate_test_plan',
            'topic': topic,
            'format': 'markdown',
            'structure': {
                'h1': 'Test title from topic',
                'h2': 'Test scenarios (multiple)',
                'h3': 'Individual tasks with numbered steps and expected results'
            },
            'requirements': [
                'Follow the markdown format: H1 > H2 (Test Scenario:) > H3 (Task:)',
                'Include numbered steps for each task',
                'Include "Expected Result:" for each task',
                'Generate realistic, comprehensive test scenarios',
                'Cover positive, negative, and edge cases'
            ]
        }
    
    def execute(self):
        """Execute the interactive workflow"""
        self.print_banner()
        
        # Step 1: Select mode
        self.mode = self.prompt_mode()
        self.config['mode'] = self.mode
        
        # Step 2: Get input based on mode
        if self.mode == 'topic':
            self.config['topic'] = self.prompt_topic()
        else:
            self.config['file_path'] = self.prompt_file_path()
        
        # Step 3: Prompt for Lark task list ID
        self.config['task_list_id'] = self.prompt_task_list_id()
        
        # Step 4: Prompt for target date
        self.config['target_date'] = self.prompt_target_date()
        
        # Step 5: Prompt for owner
        self.config['owner'] = self.prompt_owner()
        
        # Step 6: Prompt for priority
        self.config['priority'] = self.prompt_priority()
        
        # Step 7: Confirm configuration
        if not self.confirm_configuration():
            print("\n❌ Configuration cancelled. Exiting...")
            sys.exit(0)
        
        # Step 8: Execute workflow based on mode
        print("\n" + "="*70)
        print("🚀 EXECUTING WORKFLOW")
        print("="*70)
        
        if self.mode == 'topic':
            # Generate test plan from topic
            generation_request = self.generate_test_plan_from_topic(self.config['topic'])
            
            return {
                'success': True,
                'mode': 'topic',
                'phase': 'test_plan_generation',
                'generation_request': generation_request,
                'config': self.config,
                'next_steps': [
                    'Claude Code will generate test plan markdown',
                    'Markdown will be saved to file',
                    'JSON will be generated from markdown',
                    'Lark tasks will be created',
                    'Verification will be performed'
                ]
            }
        else:
            # Process existing markdown file
            # Convert Path to string for JSON serialization
            config_serializable = {
                'mode': self.config['mode'],
                'file_path': str(self.config['file_path']),
                'task_list_id': self.config.get('task_list_id'),
                'target_date': self.config['target_date'],
                'owner': self.config['owner'],
                'priority': self.config['priority']
            }

            return {
                'success': True,
                'mode': 'file',
                'phase': 'ready_to_process',
                'file_path': str(self.config['file_path']),
                'config': config_serializable,
                'next_steps': [
                    'Parse markdown file',
                    'Generate JSON structure',
                    'Create Lark tasks',
                    'Verify creation',
                    'Generate report'
                ]
            }

def main():
    """Main entry point"""
    agent = InteractiveLarkAgent()
    result = agent.execute()
    
    print("\n" + "="*70)
    print("📤 WORKFLOW REQUEST FOR CLAUDE CODE")
    print("="*70)
    print(json.dumps(result, indent=2))
    print("\n")

if __name__ == '__main__':
    main()

