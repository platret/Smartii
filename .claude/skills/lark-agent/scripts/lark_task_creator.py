#!/usr/bin/env python3
"""
Lark Task Creator
Creates hierarchical Lark tasks from JSON structures using Lark MCP tools

This module is designed to work with Claude Code's tool calling capabilities
to interact with the Lark MCP server.
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

class LarkTaskCreator:
    """Creates hierarchical Lark tasks via MCP"""
    
    def __init__(self):
        # Lark MCP tool names (will be called by Claude Code)
        self.lark_tools = {
            'task_create': 'mcp__lark-mcp__task_v2_task_create',
            'task_get': 'mcp__lark-mcp__task_v2_task_get',
            'tasklist_create': 'mcp__lark-mcp__task_v2_tasklist_create',
            'task_add_tasklist': 'mcp__lark-mcp__task_v2_task_addTasklist',
            'task_add_members': 'mcp__lark-mcp__task_v2_task_addMembers',
            'task_subtask_create': 'mcp__lark-mcp__task_v2_taskSubtask_create',
        }
        
        self.created_tasks = {}  # taskId -> larkTaskId mapping
        self.current_year = datetime.now().year
    
    def load_json_file(self, json_path: Path) -> Dict[str, Any]:
        """Load and validate JSON file"""
        if not json_path.exists():
            raise FileNotFoundError(f"JSON file not found: {json_path}")
        
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Validate structure
        if 'testOverview' not in data or 'scenarios' not in data:
            raise ValueError("Invalid JSON structure: missing testOverview or scenarios")
        
        return data
    
    def calculate_timestamp(self, date_str: str) -> int:
        """Convert date string to Unix timestamp in seconds"""
        try:
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            return int(dt.timestamp())
        except ValueError:
            # If parsing fails, use current date
            return int(datetime.now().timestamp())
    
    def format_members(self, owner: str, user_assignment: Optional[Dict] = None) -> List[Dict]:
        """
        Format members for Lark task assignment
        
        Returns list of member objects for Lark API
        This will be processed by Claude Code to make actual MCP calls
        """
        if user_assignment:
            return [user_assignment]
        
        # Return a placeholder that Claude Code will resolve
        return [{
            'id': owner,
            'type': 'user',
            'role': 'assignee'
        }]
    
    def create_parent_task(self, data: Dict[str, Any], tasklist_id: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create Level 1 parent task
        
        Returns a request object for Claude Code to execute via MCP
        """
        overview = data['testOverview']
        
        start_timestamp = self.calculate_timestamp(overview.get('startDate', datetime.now().strftime('%Y-%m-%d')))
        due_timestamp = self.calculate_timestamp(overview['targetDate'])
        
        task_request = {
            'action': 'create_task',
            'tool': self.lark_tools['task_create'],
            'level': 1,
            'data': {
                'summary': overview['title'],
                'description': overview['description'],
                'start': {
                    'timestamp': str(start_timestamp),
                    'is_all_day': True
                },
                'due': {
                    'timestamp': str(due_timestamp),
                    'is_all_day': True
                },
                'tasklists': [{
                    'tasklist_guid': tasklist_id,
                    'section_guid': None
                }],
                'members': self.format_members(overview['owner'], options.get('user_assignment')),
                'mode': 2,  # or-sign task
                'is_milestone': False
            },
            'metadata': {
                'type': 'parent',
                'title': overview['title']
            }
        }
        
        return task_request
    
    def create_scenario_tasks(self, data: Dict[str, Any], parent_task_id: str, options: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Create Level 2 scenario tasks
        
        Returns list of request objects for Claude Code to execute via MCP
        """
        scenario_requests = []
        scenarios = data['scenarios']
        
        # Calculate date distribution
        start_date = datetime.strptime(data['testOverview']['startDate'], '%Y-%m-%d')
        target_date = datetime.strptime(data['testOverview']['targetDate'], '%Y-%m-%d')
        total_days = (target_date - start_date).days
        
        for i, scenario in enumerate(scenarios):
            # Distribute scenarios evenly across timeline
            days_offset = int((total_days / len(scenarios)) * (i + 1))
            scenario_date = start_date + timedelta(days=days_offset)
            scenario_timestamp = int(scenario_date.timestamp())
            
            task_request = {
                'action': 'create_task',
                'tool': self.lark_tools['task_subtask_create'],
                'level': 2,
                'data': {
                    'summary': scenario['title'],
                    'description': scenario.get('description', ''),
                    'start': {
                        'timestamp': str(scenario_timestamp),
                        'is_all_day': True
                    },
                    'due': {
                        'timestamp': str(scenario_timestamp),
                        'is_all_day': True
                    },
                    'parent_task_guid': parent_task_id,
                    'members': self.format_members(scenario.get('owner', data['testOverview']['owner']), options.get('user_assignment')),
                    'mode': 2,
                    'is_milestone': len(scenario.get('tasks', [])) > 0  # Milestone if has subtasks
                },
                'metadata': {
                    'type': 'scenario',
                    'scenario_id': scenario['scenarioId'],
                    'title': scenario['title'],
                    'index': i
                }
            }
            
            scenario_requests.append(task_request)
        
        return scenario_requests
    
    def create_individual_tasks(self, data: Dict[str, Any], scenario_task_ids: Dict[str, str], options: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Create Level 3 individual tasks
        
        Returns list of request objects for Claude Code to execute via MCP
        """
        task_requests = []
        
        for scenario in data['scenarios']:
            scenario_id = scenario['scenarioId']
            parent_task_id = scenario_task_ids.get(scenario_id)
            
            if not parent_task_id:
                print(f"Warning: No parent task ID for scenario {scenario_id}")
                continue
            
            for task_index, task in enumerate(scenario.get('tasks', [])):
                # Use scenario date for individual tasks
                task_timestamp = self.calculate_timestamp(data['testOverview']['targetDate'])
                
                task_request = {
                    'action': 'create_task',
                    'tool': self.lark_tools['task_subtask_create'],
                    'level': 3,
                    'data': {
                        'summary': task['title'],
                        'description': task['description'],
                        'extra': {
                            'expected_result': task.get('expectedResult', '')
                        },
                        'due': {
                            'timestamp': str(task_timestamp),
                            'is_all_day': True
                        },
                        'parent_task_guid': parent_task_id,
                        'members': self.format_members(scenario.get('owner', data['testOverview']['owner']), options.get('user_assignment')),
                        'mode': 2,
                        'is_milestone': False
                    },
                    'metadata': {
                        'type': 'task',
                        'task_id': task['taskId'],
                        'scenario_id': scenario_id,
                        'title': task['title'],
                        'index': task_index
                    }
                }
                
                task_requests.append(task_request)
        
        return task_requests
    
    def update_json_with_task_ids(self, json_path: Path, data: Dict[str, Any], task_ids: Dict[str, str]) -> Path:
        """Update JSON file with created Lark task IDs"""
        # Update testOverview
        if 'parent' in task_ids:
            data['testOverview']['parentTaskId'] = task_ids['parent']
        
        # Update scenarios
        for scenario in data['scenarios']:
            scenario_id = scenario['scenarioId']
            if scenario_id in task_ids:
                scenario['lark_task_id'] = task_ids[scenario_id]
            
            # Update tasks within scenario
            for task in scenario.get('tasks', []):
                task_id = task['taskId']
                if task_id in task_ids:
                    task['lark_task_id'] = task_ids[task_id]
        
        # Update completion flags
        data['larkActionsCompleted'] = True
        data['larkActionsCompletedAt'] = datetime.now().isoformat()
        data['larksActions'] = 'completed'
        
        # Write updated JSON
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return json_path
    
    def execute(self, json_path: Path, options: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the task creation workflow
        
        Returns a workflow plan for Claude Code to execute
        """
        print(f"🏗️  Loading JSON file: {json_path}")
        data = self.load_json_file(json_path)
        
        print(f"   Test: {data['testOverview']['title']}")
        print(f"   Scenarios: {len(data['scenarios'])}")
        
        total_tasks = sum(len(s.get('tasks', [])) for s in data['scenarios'])
        print(f"   Total tasks: {total_tasks}\n")
        
        # Generate workflow plan for Claude Code to execute
        workflow = {
            'phase': 'task_creation',
            'json_path': str(json_path),
            'data': data,
            'options': options,
            'steps': []
        }
        
        # Step 1: Create or get task list
        workflow['steps'].append({
            'step': 1,
            'action': 'create_tasklist',
            'tool': self.lark_tools['tasklist_create'],
            'data': {
                'name': f"Test: {data['testOverview']['title']}",
                'description': data['testOverview']['description']
            }
        })
        
        # Step 2: Create parent task
        parent_request = self.create_parent_task(data, '{{tasklist_id}}', options)
        workflow['steps'].append({
            'step': 2,
            'description': 'Create parent task (Level 1)',
            **parent_request
        })
        
        # Step 3: Create scenario tasks
        scenario_requests = self.create_scenario_tasks(data, '{{parent_task_id}}', options)
        workflow['steps'].append({
            'step': 3,
            'description': f'Create {len(scenario_requests)} scenario tasks (Level 2)',
            'tasks': scenario_requests
        })
        
        # Step 4: Create individual tasks
        # This will be populated after scenario tasks are created
        workflow['steps'].append({
            'step': 4,
            'description': f'Create {total_tasks} individual tasks (Level 3)',
            'note': 'Will be executed after scenario tasks are created',
            'data': data,
            'options': options
        })
        
        # Step 5: Update JSON with task IDs
        workflow['steps'].append({
            'step': 5,
            'action': 'update_json',
            'description': 'Update JSON file with Lark task IDs',
            'json_path': str(json_path)
        })
        
        return workflow

def main():
    """Test the task creator"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python lark_task_creator.py <json-file>")
        sys.exit(1)
    
    json_path = Path(sys.argv[1])
    options = {
        'owner': 'Test User',
        'user_assignment': None
    }
    
    creator = LarkTaskCreator()
    workflow = creator.execute(json_path, options)
    
    print("\n" + "="*60)
    print("📋 Task Creation Workflow Plan")
    print("="*60)
    print(json.dumps(workflow, indent=2))

if __name__ == '__main__':
    main()

