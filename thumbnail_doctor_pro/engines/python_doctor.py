"""
Python Code Analysis Engine for Thumbnail Doctor Pro Ultimate
Performs AST analysis, Ruff, Pylint, Bandit, and Radon analysis
"""
import ast
import os
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass
from pathlib import Path
import json
from utils.logger import get_logger

logger = get_logger()

@dataclass
class CodeIssue:
    issue_type: str
    severity: str
    message: str
    line_number: int
    column: int
    file_path: str
    suggestion: Optional[str] = None

class ASTCodeAnalyzer:
    def __init__(self):
        self.issues: List[CodeIssue] = []
    
    def analyze_file(self, file_path: str) -> List[CodeIssue]:
        self.issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            
            tree = ast.parse(source_code, filename=file_path)
            
            self._check_unused_imports(tree, file_path)
            self._check_large_functions(tree, source_code, file_path)
            self._check_large_classes(tree, file_path)
            self._check_complex_functions(tree, source_code, file_path)
            self._check_duplicate_code(source_code, file_path)
            self._check_unused_variables(tree, file_path)
            
        except SyntaxError as e:
            self.issues.append(CodeIssue(
                issue_type='syntax_error',
                severity='critical',
                message=f'Syntax error: {str(e)}',
                line_number=e.lineno or 0,
                column=e.offset or 0,
                file_path=file_path
            ))
        except Exception as e:
            logger.error(f"AST analysis failed for {file_path}: {e}")
        
        return self.issues
    
    def _check_unused_imports(self, tree: ast.AST, file_path: str):
        imported_names: Set[str] = set()
        used_names: Set[str] = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname or alias.name.split('.')[0]
                    imported_names.add(name)
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    name = alias.asname or alias.name
                    imported_names.add(name)
            elif isinstance(node, ast.Name):
                used_names.add(node.id)
        
        unused = imported_names - used_names
        for name in unused:
            if not name.startswith('_'):
                self.issues.append(CodeIssue(
                    issue_type='unused_import',
                    severity='warning',
                    message=f'Unused import: {name}',
                    line_number=0,
                    column=0,
                    file_path=file_path,
                    suggestion=f'Remove "import {name}" or use it in the code'
                ))
    
    def _check_large_functions(self, tree: ast.AST, source_code: str, file_path: str):
        lines = source_code.split('\n')
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                start_line = node.lineno
                end_line = node.end_lineno or start_line
                function_lines = end_line - start_line
                
                if function_lines > 50:
                    self.issues.append(CodeIssue(
                        issue_type='large_function',
                        severity='warning',
                        message=f'Function "{node.name}" is too large ({function_lines} lines)',
                        line_number=start_line,
                        column=node.col_offset,
                        file_path=file_path,
                        suggestion='Consider breaking this function into smaller functions'
                    ))
    
    def _check_large_classes(self, tree: ast.AST, file_path: str):
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = [n for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
                
                if len(methods) > 20:
                    self.issues.append(CodeIssue(
                        issue_type='large_class',
                        severity='warning',
                        message=f'Class "{node.name}" has too many methods ({len(methods)})',
                        line_number=node.lineno,
                        column=node.col_offset,
                        file_path=file_path,
                        suggestion='Consider splitting this class into smaller classes'
                    ))
    
    def _check_complex_functions(self, tree: ast.AST, source_code: str, file_path: str):
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                complexity = self._calculate_complexity(node)
                
                if complexity > 10:
                    self.issues.append(CodeIssue(
                        issue_type='high_complexity',
                        severity='warning',
                        message=f'Function "{node.name}" has high cyclomatic complexity ({complexity})',
                        line_number=node.lineno,
                        column=node.col_offset,
                        file_path=file_path,
                        suggestion='Reduce branching and simplify logic'
                    ))
    
    def _calculate_complexity(self, node: ast.AST) -> int:
        complexity = 1
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler,
                                 ast.With, ast.Assert, ast.comprehension)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity
    
    def _check_duplicate_code(self, source_code: str, file_path: str):
        lines = source_code.split('\n')
        line_groups: Dict[str, List[int]] = {}
        
        window_size = 5
        for i in range(len(lines) - window_size + 1):
            window = '\n'.join(lines[i:i+window_size]).strip()
            if len(window) > 50 and not window.startswith('#'):
                if window not in line_groups:
                    line_groups[window] = []
                line_groups[window].append(i + 1)
        
        for window, line_nums in line_groups.items():
            if len(line_nums) > 1:
                self.issues.append(CodeIssue(
                    issue_type='duplicate_code',
                    severity='info',
                    message=f'Duplicate code block found at lines {line_nums}',
                    line_number=line_nums[0],
                    column=0,
                    file_path=file_path,
                    suggestion='Consider extracting this code into a reusable function'
                ))
    
    def _check_unused_variables(self, tree: ast.AST, file_path: str):
        assigned_vars: Dict[str, int] = {}
        used_vars: Set[str] = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        assigned_vars[target.id] = node.lineno
            elif isinstance(node, ast.AnnAssign) and node.target:
                if isinstance(node.target, ast.Name):
                    assigned_vars[node.target.id] = node.lineno
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                used_vars.add(node.id)
        
        for var_name, line_num in assigned_vars.items():
            if var_name not in used_vars and not var_name.startswith('_'):
                self.issues.append(CodeIssue(
                    issue_type='unused_variable',
                    severity='info',
                    message=f'Unused variable: {var_name}',
                    line_number=line_num,
                    column=0,
                    file_path=file_path,
                    suggestion=f'Remove unused variable "{var_name}"'
                ))

class RuffAnalyzer:
    def analyze_file(self, file_path: str) -> List[Dict[str, Any]]:
        try:
            import subprocess
            result = subprocess.run(
                ['ruff', 'check', '--output-format=json', file_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.stdout:
                issues = json.loads(result.stdout)
                return [{
                    'type': 'ruff',
                    'code': issue.get('code', ''),
                    'message': issue.get('message', ''),
                    'line': issue.get('location', {}).get('row', 0),
                    'column': issue.get('location', {}).get('column', 0),
                    'severity': self._map_severity(issue.get('code', '')),
                    'fix': issue.get('fix')
                } for issue in issues]
        except Exception as e:
            logger.warning(f"Ruff analysis failed: {e}")
        
        return []
    
    def _map_severity(self, code: str) -> str:
        if code.startswith(('E', 'F')):
            return 'error'
        elif code.startswith('W'):
            return 'warning'
        return 'info'

class PylintAnalyzer:
    def analyze_file(self, file_path: str) -> List[Dict[str, Any]]:
        try:
            import subprocess
            result = subprocess.run(
                ['pylint', '--output-format=json', file_path],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.stdout:
                issues = json.loads(result.stdout)
                if isinstance(issues, list):
                    return [{
                        'type': 'pylint',
                        'message': issue.get('message', ''),
                        'symbol': issue.get('symbol', ''),
                        'line': issue.get('line', 0),
                        'column': issue.get('column', 0),
                        'severity': self._map_pylint_severity(issue.get('type', ''))
                    } for issue in issues]
        except Exception as e:
            logger.warning(f"Pylint analysis failed: {e}")
        
        return []
    
    def _map_pylint_severity(self, severity: str) -> str:
        mapping = {
            'error': 'error',
            'warning': 'warning',
            'convention': 'info',
            'refactor': 'info',
            'fatal': 'critical'
        }
        return mapping.get(severity, 'info')

class BanditAnalyzer:
    def analyze_file(self, file_path: str) -> List[Dict[str, Any]]:
        try:
            import subprocess
            result = subprocess.run(
                ['bandit', '-f', 'json', file_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.stdout:
                report = json.loads(result.stdout)
                issues = report.get('results', [])
                return [{
                    'type': 'bandit',
                    'test_id': issue.get('test_id', ''),
                    'message': issue.get('issue', ''),
                    'severity': issue.get('issue_severity', 'low').lower(),
                    'confidence': issue.get('issue_confidence', 'low').lower(),
                    'line': issue.get('line_number', 0)
                } for issue in issues]
        except Exception as e:
            logger.warning(f"Bandit analysis failed: {e}")
        
        return []

class RadonAnalyzer:
    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        try:
            from radon.complexity import cc_visit
            from radon.metrics import h_visit
            
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            
            complexity_results = cc_visit(source_code)
            metrics = h_visit(source_code)
            
            avg_complexity = (
                sum(r.complexity for r in complexity_results) / len(complexity_results)
                if complexity_results else 0
            )
            
            return {
                'cyclomatic_complexity': {
                    'average': round(avg_complexity, 2),
                    'max': max((r.complexity for r in complexity_results), default=0),
                    'functions': [{
                        'name': r.name,
                        'complexity': r.complexity,
                        'line': r.lineno
                    } for r in complexity_results]
                },
                'maintainability_index': round(metrics.mi, 2),
                'halstead_metrics': {
                    'volume': round(metrics.hv, 2),
                    'difficulty': round(metrics.hd, 2),
                    'effort': round(metrics.he, 2)
                }
            }
        except Exception as e:
            logger.warning(f"Radon analysis failed: {e}")
        
        return {
            'cyclomatic_complexity': {'average': 0, 'max': 0, 'functions': []},
            'maintainability_index': 0,
            'halstead_metrics': {'volume': 0, 'difficulty': 0, 'effort': 0}
        }

class PythonProjectDoctor:
    def __init__(self):
        self.ast_analyzer = ASTCodeAnalyzer()
        self.ruff_analyzer = RuffAnalyzer()
        self.pylint_analyzer = PylintAnalyzer()
        self.bandit_analyzer = BanditAnalyzer()
        self.radon_analyzer = RadonAnalyzer()
    
    def analyze_project(self, path: str) -> Dict[str, Any]:
        results = {
            'files_analyzed': 0,
            'ast_issues': [],
            'ruff_issues': [],
            'pylint_issues': [],
            'bandit_issues': [],
            'radon_metrics': {},
            'scores': {},
            'recommendations': [],
            'security_issues': []
        }
        
        python_files = self._find_python_files(path)
        results['files_analyzed'] = len(python_files)
        
        for file_path in python_files:
            results['ast_issues'].extend([vars(i) for i in self.ast_analyzer.analyze_file(file_path)])
            results['ruff_issues'].extend(self.ruff_analyzer.analyze_file(file_path))
            results['pylint_issues'].extend(self.pylint_analyzer.analyze_file(file_path))
            bandit_results = self.bandit_analyzer.analyze_file(file_path)
            results['bandit_issues'].extend(bandit_results)
            results['security_issues'].extend([i for i in bandit_results if i.get('severity') in ['high', 'critical']])
            results['radon_metrics'][file_path] = self.radon_analyzer.analyze_file(file_path)
        
        results['scores'] = self._calculate_scores(results)
        results['recommendations'] = self._generate_recommendations(results)
        
        return results
    
    def _find_python_files(self, path: str) -> List[str]:
        python_files = []
        path_obj = Path(path)
        
        if path_obj.is_file():
            if path.endswith('.py'):
                python_files.append(path)
        elif path_obj.is_dir():
            for py_file in path_obj.rglob('*.py'):
                if not any(part.startswith('.') for part in py_file.parts):
                    python_files.append(str(py_file))
        
        return python_files
    
    def _calculate_scores(self, results: Dict[str, Any]) -> Dict[str, float]:
        total_issues = (
            len(results['ast_issues']) +
            len(results['ruff_issues']) +
            len(results['pylint_issues'])
        )
        
        critical_issues = sum(1 for i in results['ast_issues'] if i.get('severity') == 'critical')
        critical_issues += sum(1 for i in results['bandit_issues'] if i.get('severity') == 'high')
        
        code_quality = max(0, 100 - total_issues * 2 - critical_issues * 10)
        
        security_score = max(0, 100 - len(results['security_issues']) * 15)
        
        avg_maintainability = 0
        if results['radon_metrics']:
            maintainabilities = [m.get('maintainability_index', 50) for m in results['radon_metrics'].values()]
            avg_maintainability = sum(maintainabilities) / len(maintainabilities)
        
        performance_score = 75
        avg_complexity = 0
        if results['radon_metrics']:
            complexities = []
            for metrics in results['radon_metrics'].values():
                cc = metrics.get('cyclomatic_complexity', {})
                if cc.get('average', 0) > 0:
                    complexities.append(cc['average'])
            if complexities:
                avg_complexity = sum(complexities) / len(complexities)
                performance_score = max(0, 100 - avg_complexity * 5)
        
        overall = (code_quality * 0.3 + security_score * 0.3 + 
                  avg_maintainability * 0.2 + performance_score * 0.2)
        
        return {
            'code_quality': round(code_quality, 1),
            'security': round(security_score, 1),
            'maintainability': round(avg_maintainability, 1),
            'performance': round(performance_score, 1),
            'overall': round(overall, 1)
        }
    
    def _generate_recommendations(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        recommendations = []
        
        if results['security_issues']:
            recommendations.append({
                'category': 'security',
                'priority': 'critical',
                'title': 'Fix Security Vulnerabilities',
                'description': f'Found {len(results["security_issues"])} high-severity security issues',
                'action': 'Review and fix all Bandit-reported security issues immediately'
            })
        
        high_complexity_funcs = []
        for file_metrics in results['radon_metrics'].values():
            for func in file_metrics.get('cyclomatic_complexity', {}).get('functions', []):
                if func.get('complexity', 0) > 10:
                    high_complexity_funcs.append(func)
        
        if high_complexity_funcs:
            recommendations.append({
                'category': 'complexity',
                'priority': 'high',
                'title': 'Reduce Function Complexity',
                'description': f'{len(high_complexity_funcs)} functions have high cyclomatic complexity',
                'action': 'Refactor complex functions to reduce branching and improve maintainability'
            })
        
        unused_imports = [i for i in results['ast_issues'] if i.get('issue_type') == 'unused_import']
        if unused_imports:
            recommendations.append({
                'category': 'clean_code',
                'priority': 'medium',
                'title': 'Remove Unused Imports',
                'description': f'Found {len(unused_imports)} unused imports',
                'action': 'Clean up unused imports to improve code clarity'
            })
        
        return recommendations
