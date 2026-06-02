#!/usr/bin/env python3
"""
Lark Batch Executor
Generates a compact, batch-executable plan for Claude Code to execute ALL Lark tasks at once
This minimizes token usage by avoiding step-by-step execution
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

class LarkBatchExecutor:
    """Generates compact batch execution plan for Lark task creation"""
    
    def __init__(self):
        self.current_year = datetime.now().year
    
    def load_json_file(self, json_path: Path) -> Dict[str, Any]:
        """Load and validate JSON file"""
        if not json_path.exists():
            raise FileNotFoundError(f"JSON file not found: {json_path}")
        
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if 'testOverview' not in data or 'scenarios' not in data:
            raise ValueError("Invalid JSON structure: missing testOverview or scenarios")
        
        return data
    
    def calculate_timestamp(self, date_str: str) -> str:
        """Convert date string to Unix timestamp in milliseconds (Lark format)"""
        try:
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            # Lark uses milliseconds
            return str(int(dt.timestamp() * 1000))
        except ValueError:
            # If parsing fails, use current date
            return str(int(datetime.now().timestamp() * 1000))
    
    def generate_batch_plan(self, json_path: Path, options: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a compact batch execution plan
        
        Returns a single JSON structure that Claude Code can execute in one go
        """
        data = self.load_json_file(json_path)
        overview = data['testOverview']
        scenarios = data['scenarios']
        
        # Calculate timestamps
        start_timestamp = self.calculate_timestamp(overview.get('startDate', datetime.now().strftime('%Y-%m-%d')))
        due_timestamp = self.calculate_timestamp(overview['targetDate'])
        
        # Count tasks
        total_tasks = sum(len(s.get('tasks', [])) for s in scenarios)
        
        # Build compact execution plan
        plan = {
            'execute_immediately': True,
            'execution_mode': 'batch',
            'json_path': str(json_path),
            'summary': {
                'test_title': overview['title'],
                'scenarios_count': len(scenarios),
                'tasks_count': total_tasks,
                'owner': overview['owner'],
                'target_date': overview['targetDate']
            },
            'mcp_calls': []
        }
        
        # Step 1: Create task list
        plan['mcp_calls'].append({
            'id': 'tasklist',
            'tool': 'lark-mcp',
            'method': 'task_v2_tasklist_create',
            'params': {
                'data': {
                    'name': f"Test: {overview['title']}",
                    'members': []
                },
                'useUAT': True
            },
            'save_result_as': 'tasklist_guid'
        })
        
        # Step 2: Create parent task
        plan['mcp_calls'].append({
            'id': 'parent_task',
            'tool': 'lark-mcp',
            'method': 'task_v2_task_create',
            'params': {
                'data': {
                    'summary': overview['title'],
                    'description': overview['description'],
                    'start': {
                        'timestamp': start_timestamp,
                        'is_all_day': True
                    },
                    'due': {
                        'timestamp': due_timestamp,
                        'is_all_day': True
                    },
                    'tasklists': [{
                        'tasklist_guid': '{{tasklist_guid}}'
                    }],
                    'mode': 2,
                    'is_milestone': False
                },
                'useUAT': True
            },
            'depends_on': ['tasklist'],
            'save_result_as': 'parent_task_guid'
        })
        
        # Step 3: Create scenario tasks
        start_date = datetime.strptime(overview['startDate'], '%Y-%m-%d')
        target_date = datetime.strptime(overview['targetDate'], '%Y-%m-%d')
        total_days = (target_date - start_date).days
        
        for i, scenario in enumerate(scenarios):
            # Distribute scenarios evenly
            days_offset = int((total_days / len(scenarios)) * (i + 1))
            scenario_date = start_date + timedelta(days=days_offset)
            scenario_timestamp = str(int(scenario_date.timestamp() * 1000))
            
            scenario_id = scenario['scenarioId']
            
            plan['mcp_calls'].append({
                'id': f'scenario_{scenario_id}',
                'tool': 'lark-mcp',
                'method': 'task_v2_taskSubtask_create',
                'params': {
                    'data': {
                        'summary': scenario['title'],
                        'description': scenario.get('description', ''),
                        'start': {
                            'timestamp': scenario_timestamp,
                            'is_all_day': True
                        },
                        'due': {
                            'timestamp': scenario_timestamp,
                            'is_all_day': True
                        },
                        'parent_task_guid': '{{parent_task_guid}}',
                        'mode': 2,
                        'is_milestone': len(scenario.get('tasks', [])) > 0
                    },
                    'useUAT': True
                },
                'depends_on': ['parent_task'],
                'save_result_as': f'scenario_{scenario_id}_guid',
                'metadata': {
                    'scenario_id': scenario_id,
                    'scenario_title': scenario['title']
                }
            })
            
            # Step 4: Create individual tasks for this scenario
            for task_index, task in enumerate(scenario.get('tasks', [])):
                task_id = task['taskId']
                
                plan['mcp_calls'].append({
                    'id': f'task_{task_id}',
                    'tool': 'lark-mcp',
                    'method': 'task_v2_taskSubtask_create',
                    'params': {
                        'data': {
                            'summary': task['title'],
                            'description': task['description'],
                            'due': {
                                'timestamp': scenario_timestamp,
                                'is_all_day': True
                            },
                            'parent_task_guid': f'{{{{scenario_{scenario_id}_guid}}}}',
                            'mode': 2,
                            'is_milestone': False
                        },
                        'useUAT': True
                    },
                    'depends_on': [f'scenario_{scenario_id}'],
                    'save_result_as': f'task_{task_id}_guid',
                    'metadata': {
                        'task_id': task_id,
                        'scenario_id': scenario_id,
                        'task_title': task['title']
                    }
                })
        
        # Step 5: Update JSON file instruction
        plan['post_execution'] = {
            'action': 'update_json',
            'json_path': str(json_path),
            'update_fields': {
                'larkActionsCompleted': True,
                'larkActionsCompletedAt': '{{execution_timestamp}}',
                'larksActions': 'completed'
            },
            'map_results': {
                'testOverview.parentTaskId': '{{parent_task_guid}}',
                'scenarios': 'map_by_scenarioId_to_lark_task_id',
                'tasks': 'map_by_taskId_to_lark_task_id'
            }
        }
        
        return plan
    
    def execute(self, json_path: Path, options: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute batch plan generation
        
        Returns a compact execution plan for Claude Code
        """
        print(f"🔄 Generating batch execution plan...")
        print(f"   📂 JSON: {json_path}")
        
        plan = self.generate_batch_plan(json_path, options)
        
        print(f"\n✅ Batch plan generated!")
        print(f"   📊 Total MCP calls: {len(plan['mcp_calls'])}")
        print(f"   🎯 Execution mode: BATCH (all at once)")
        print(f"   💡 Token efficient: YES")
        
        return {
            'success': True,
            'mode': 'batch_execution',
            'plan': plan
        }

def main():
    """Test the batch executor"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python lark_batch_executor.py <json-file>")
        sys.exit(1)
    
    json_path = Path(sys.argv[1])
    options = {
        'owner': 'Test User'
    }
    
    executor = LarkBatchExecutor()
    result = executor.execute(json_path, options)
    
    print("\n" + "="*60)
    print("📋 Batch Execution Plan")
    print("="*60)
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()

