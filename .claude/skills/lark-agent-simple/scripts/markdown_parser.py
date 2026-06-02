#!/usr/bin/env python3
"""
Markdown Parser for Lark Agent
Parses markdown test files and extracts structured data
"""

import re
from typing import Dict, List, Any, Optional
from datetime import datetime

class MarkdownParser:
    """Parser for markdown test files"""
    
    def __init__(self):
        self.current_timestamp = int(datetime.now().timestamp() * 1000)
    
    def parse_file(self, content: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse markdown content and return structured JSON
        
        Args:
            content: Markdown file content
            options: Configuration options (owner, dates, etc.)
        
        Returns:
            Structured JSON matching the Lark Agent schema
        """
        lines = content.split('\n')
        
        # Extract test overview (H1)
        test_overview = self._extract_test_overview(lines, options)
        
        # Extract scenarios (H2) and tasks (H3)
        scenarios = self._extract_scenarios(lines, options)
        
        return {
            'testOverview': test_overview,
            'scenarios': scenarios,
            'larkActionsCompleted': False,
            'larkActionsCompletedAt': None,
            'larksActions': 'pending'
        }
    
    def _extract_test_overview(self, lines: List[str], options: Dict[str, Any]) -> Dict[str, Any]:
        """Extract test overview from H1 heading and description"""
        title = ""
        description = ""
        
        # Find H1 heading
        for i, line in enumerate(lines):
            if line.startswith('# '):
                title = line[2:].strip()
                # Get description (lines after H1 until next heading)
                desc_lines = []
                for j in range(i + 1, len(lines)):
                    if lines[j].startswith('#'):
                        break
                    if lines[j].strip():
                        desc_lines.append(lines[j].strip())
                description = ' '.join(desc_lines)
                break
        
        return {
            'title': title,
            'description': description,
            'owner': options.get('owner', 'Test User'),
            'targetDate': options.get('target_date', ''),
            'startDate': options.get('start_date', ''),
            'status': 'pending',
            'larkTaskListId': None,
            'parentTaskId': None,
            'priority': options.get('priority', 'medium')
        }
    
    def _extract_scenarios(self, lines: List[str], options: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract scenarios (H2) and their tasks (H3)"""
        scenarios = []
        current_scenario = None
        current_task = None
        scenario_index = 0
        task_index = 0
        
        for i, line in enumerate(lines):
            # H2 - Scenario
            if line.startswith('## '):
                # Save previous scenario if exists
                if current_scenario:
                    scenarios.append(current_scenario)
                
                # Start new scenario
                title = line[3:].strip()
                description = self._extract_description(lines, i + 1, '##')
                
                current_scenario = {
                    'scenarioId': f'scenario-{scenario_index}-{self.current_timestamp}',
                    'title': title,
                    'description': description,
                    'expectedOutcome': '',
                    'owner': options.get('owner', 'Test User'),
                    'status': 'pending',
                    'tasks': [],
                    'lark_task_id': None
                }
                scenario_index += 1
                task_index = 0
            
            # H3 - Task
            elif line.startswith('### '):
                if current_scenario is None:
                    continue
                
                # Save previous task if exists
                if current_task:
                    current_scenario['tasks'].append(current_task)
                
                # Start new task
                title = line[4:].strip()
                task_content = self._extract_task_content(lines, i + 1)
                
                current_task = {
                    'taskId': f'task-{scenario_index-1}-{task_index}-{self.current_timestamp}',
                    'title': title,
                    'description': task_content['description'],
                    'expectedResult': task_content['expected_result'],
                    'status': 'pending',
                    'notes': '',
                    'lark_task_id': None
                }
                task_index += 1
        
        # Save last task and scenario
        if current_task and current_scenario:
            current_scenario['tasks'].append(current_task)
        if current_scenario:
            scenarios.append(current_scenario)
        
        return scenarios
    
    def _extract_description(self, lines: List[str], start_idx: int, stop_marker: str) -> str:
        """Extract description text until next heading"""
        desc_lines = []
        for i in range(start_idx, len(lines)):
            line = lines[i]
            if line.startswith(stop_marker):
                break
            if line.strip() and not line.startswith('#'):
                desc_lines.append(line.strip())
        return ' '.join(desc_lines)
    
    def _extract_task_content(self, lines: List[str], start_idx: int) -> Dict[str, str]:
        """Extract task steps and expected result"""
        steps = []
        expected_result = ""
        
        for i in range(start_idx, len(lines)):
            line = lines[i].strip()
            
            # Stop at next heading
            if line.startswith('#'):
                break
            
            # Extract expected result
            if line.startswith('Expected Result:'):
                expected_result = line.replace('Expected Result:', '').strip()
                continue
            
            # Extract numbered steps
            if re.match(r'^\d+\.', line):
                # Remove number prefix
                step = re.sub(r'^\d+\.\s*', '', line)
                steps.append(step)
        
        return {
            'description': ' '.join(steps) if steps else '',
            'expected_result': expected_result
        }

def main():
    """Test the parser with a sample file"""
    import sys
    import json
    
    if len(sys.argv) < 2:
        print("Usage: python markdown_parser.py <markdown-file>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    parser = MarkdownParser()
    options = {
        'owner': 'Test User',
        'target_date': '2025-11-02',
        'start_date': '2025-10-19',
        'priority': 'medium'
    }
    
    result = parser.parse_file(content, options)
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()

