#!/usr/bin/env python3
"""
Lark Task Verifier
Verifies created Lark tasks and generates verification reports

This module validates that tasks were created correctly in Lark
and generates comprehensive reports.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

class LarkTaskVerifier:
    """Verifies Lark task creation and generates reports"""
    
    def __init__(self):
        # Lark MCP tool names
        self.lark_tools = {
            'task_get': 'mcp__lark-mcp__task_v2_task_get',
            'task_list': 'mcp__lark-mcp__task_v2_task_list',
        }
        
        self.verification_criteria = {
            'parent_task': {
                'required': ['title', 'description', 'owner', 'due_date'],
                'checks': ['has_owner', 'has_valid_dates', 'has_description']
            },
            'level2_tasks': {
                'required': ['title', 'description', 'is_milestone'],
                'checks': ['has_owner', 'has_valid_dates', 'milestone_setting', 'has_subtasks']
            },
            'level3_tasks': {
                'required': ['title', 'description', 'expected_result'],
                'checks': ['has_owner', 'has_valid_dates', 'manual_testing_steps']
            }
        }
    
    def load_json_file(self, json_path: Path) -> Dict[str, Any]:
        """Load and validate JSON file"""
        if not json_path.exists():
            raise FileNotFoundError(f"JSON file not found: {json_path}")
        
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return data
    
    def check_completion_status(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Check if task creation was completed"""
        return {
            'lark_actions_completed': data.get('larkActionsCompleted', False),
            'lark_actions_completed_at': data.get('larkActionsCompletedAt'),
            'lark_actions_status': data.get('larksActions', 'pending')
        }
    
    def validate_json_structure(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate JSON structure and completeness"""
        issues = []
        warnings = []
        
        # Check testOverview
        if 'testOverview' not in data:
            issues.append("Missing testOverview section")
        else:
            overview = data['testOverview']
            if not overview.get('parentTaskId'):
                warnings.append("Parent task ID not set")
            if not overview.get('title'):
                issues.append("Test overview missing title")
        
        # Check scenarios
        if 'scenarios' not in data:
            issues.append("Missing scenarios section")
        elif len(data['scenarios']) == 0:
            warnings.append("No scenarios defined")
        else:
            for i, scenario in enumerate(data['scenarios']):
                if not scenario.get('lark_task_id'):
                    warnings.append(f"Scenario {i+1} missing Lark task ID")
                if not scenario.get('tasks'):
                    warnings.append(f"Scenario {i+1} has no tasks")
                else:
                    for j, task in enumerate(scenario['tasks']):
                        if not task.get('lark_task_id'):
                            warnings.append(f"Scenario {i+1}, Task {j+1} missing Lark task ID")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings
        }
    
    def verify_parent_task(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify parent task (Level 1)
        
        Returns verification request for Claude Code to execute
        """
        overview = data['testOverview']
        parent_task_id = overview.get('parentTaskId')
        
        if not parent_task_id:
            return {
                'verified': False,
                'error': 'Parent task ID not found in JSON'
            }
        
        return {
            'action': 'verify_task',
            'tool': self.lark_tools['task_get'],
            'level': 1,
            'task_id': parent_task_id,
            'expected': {
                'title': overview['title'],
                'description': overview['description'],
                'owner': overview['owner'],
                'has_subtasks': len(data['scenarios']) > 0
            },
            'checks': self.verification_criteria['parent_task']['checks']
        }
    
    def verify_scenario_tasks(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Verify scenario tasks (Level 2)
        
        Returns list of verification requests for Claude Code to execute
        """
        verification_requests = []
        
        for i, scenario in enumerate(data['scenarios']):
            task_id = scenario.get('lark_task_id')
            
            if not task_id:
                verification_requests.append({
                    'verified': False,
                    'scenario_index': i,
                    'error': f'Scenario {i+1} missing Lark task ID'
                })
                continue
            
            verification_requests.append({
                'action': 'verify_task',
                'tool': self.lark_tools['task_get'],
                'level': 2,
                'task_id': task_id,
                'scenario_index': i,
                'expected': {
                    'title': scenario['title'],
                    'description': scenario.get('description', ''),
                    'is_milestone': len(scenario.get('tasks', [])) > 0,
                    'has_subtasks': len(scenario.get('tasks', [])) > 0,
                    'subtask_count': len(scenario.get('tasks', []))
                },
                'checks': self.verification_criteria['level2_tasks']['checks']
            })
        
        return verification_requests
    
    def verify_individual_tasks(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Verify individual tasks (Level 3)
        
        Returns list of verification requests for Claude Code to execute
        """
        verification_requests = []
        
        for scenario_index, scenario in enumerate(data['scenarios']):
            for task_index, task in enumerate(scenario.get('tasks', [])):
                task_id = task.get('lark_task_id')
                
                if not task_id:
                    verification_requests.append({
                        'verified': False,
                        'scenario_index': scenario_index,
                        'task_index': task_index,
                        'error': f'Scenario {scenario_index+1}, Task {task_index+1} missing Lark task ID'
                    })
                    continue
                
                verification_requests.append({
                    'action': 'verify_task',
                    'tool': self.lark_tools['task_get'],
                    'level': 3,
                    'task_id': task_id,
                    'scenario_index': scenario_index,
                    'task_index': task_index,
                    'expected': {
                        'title': task['title'],
                        'description': task['description'],
                        'expected_result': task.get('expectedResult', ''),
                        'is_milestone': False
                    },
                    'checks': self.verification_criteria['level3_tasks']['checks']
                })
        
        return verification_requests
    
    def generate_verification_report(self, data: Dict[str, Any], verification_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive verification report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'test_title': data['testOverview']['title'],
            'summary': {
                'total_scenarios': len(data['scenarios']),
                'total_tasks': sum(len(s.get('tasks', [])) for s in data['scenarios']),
                'verification_status': 'pending'
            },
            'structure_validation': self.validate_json_structure(data),
            'completion_status': self.check_completion_status(data),
            'verification_requests': verification_results,
            'recommendations': []
        }
        
        # Add recommendations based on findings
        if not report['completion_status']['lark_actions_completed']:
            report['recommendations'].append("Complete Lark task creation before verification")
        
        if report['structure_validation']['warnings']:
            report['recommendations'].append("Review and address warnings in JSON structure")
        
        return report
    
    def execute(self, json_path: Path, options: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the verification workflow
        
        Returns a verification plan for Claude Code to execute
        """
        print(f"✅ Loading JSON file for verification: {json_path}")
        data = self.load_json_file(json_path)
        
        print(f"   Test: {data['testOverview']['title']}")
        print(f"   Scenarios: {len(data['scenarios'])}")
        
        total_tasks = sum(len(s.get('tasks', [])) for s in data['scenarios'])
        print(f"   Total tasks: {total_tasks}\n")
        
        # Check completion status
        completion = self.check_completion_status(data)
        print(f"   Lark Actions Completed: {completion['lark_actions_completed']}")
        print(f"   Status: {completion['lark_actions_status']}\n")
        
        # Validate structure
        structure = self.validate_json_structure(data)
        print(f"   Structure Valid: {structure['valid']}")
        if structure['issues']:
            print(f"   Issues: {len(structure['issues'])}")
            for issue in structure['issues']:
                print(f"      - {issue}")
        if structure['warnings']:
            print(f"   Warnings: {len(structure['warnings'])}")
            for warning in structure['warnings'][:5]:  # Show first 5
                print(f"      - {warning}")
        
        # Generate verification workflow
        workflow = {
            'phase': 'verification',
            'json_path': str(json_path),
            'data': data,
            'options': options,
            'steps': []
        }
        
        # Step 1: Verify parent task
        parent_verification = self.verify_parent_task(data)
        workflow['steps'].append({
            'step': 1,
            'description': 'Verify parent task (Level 1)',
            **parent_verification
        })
        
        # Step 2: Verify scenario tasks
        scenario_verifications = self.verify_scenario_tasks(data)
        workflow['steps'].append({
            'step': 2,
            'description': f'Verify {len(scenario_verifications)} scenario tasks (Level 2)',
            'verifications': scenario_verifications
        })
        
        # Step 3: Verify individual tasks
        task_verifications = self.verify_individual_tasks(data)
        workflow['steps'].append({
            'step': 3,
            'description': f'Verify {len(task_verifications)} individual tasks (Level 3)',
            'verifications': task_verifications
        })
        
        # Step 4: Generate report
        workflow['steps'].append({
            'step': 4,
            'action': 'generate_report',
            'description': 'Generate verification report',
            'report_template': {
                'timestamp': datetime.now().isoformat(),
                'test_title': data['testOverview']['title'],
                'structure_validation': structure,
                'completion_status': completion
            }
        })
        
        return workflow

def main():
    """Test the verifier"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python lark_task_verifier.py <json-file>")
        sys.exit(1)
    
    json_path = Path(sys.argv[1])
    options = {}
    
    verifier = LarkTaskVerifier()
    workflow = verifier.execute(json_path, options)
    
    print("\n" + "="*60)
    print("📋 Verification Workflow Plan")
    print("="*60)
    print(json.dumps(workflow, indent=2))

if __name__ == '__main__':
    main()

