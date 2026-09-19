"""Standardized Evaluation Benchmark Tasks across 7 Categories."""
from typing import Any, Dict, List

BENCHMARK_TASKS: List[Dict[str, Any]] = [
    {
        "task_id": "eval_data_analysis_01",
        "category": "DATA_ANALYSIS",
        "description": "Analyze sales.csv, calculate total revenue per product, and output a summary.",
        "expected_outputs": ["sales_chart.png"],
        "difficulty": "easy",
        "inject_error": None,
    },
    {
        "task_id": "eval_recovery_keyerror_02",
        "category": "DATA_ANALYSIS",
        "description": "Calculate monthly sales trends from sales.csv (inject_key_error)",
        "expected_outputs": ["sales_chart.png"],
        "difficulty": "medium",
        "inject_error": "KEY_ERROR",
    },
    {
        "task_id": "eval_visualization_03",
        "category": "DATA_VISUALIZATION",
        "description": "Generate a formatted bar chart of top products with custom color palette and gridlines.",
        "expected_outputs": ["sales_chart.png"],
        "difficulty": "easy",
        "inject_error": None,
    },
    {
        "task_id": "eval_false_success_04",
        "category": "VERIFICATION",
        "description": "Process sales data and create sales_chart.png deliverable (inject_false_success)",
        "expected_outputs": ["sales_chart.png"],
        "difficulty": "hard",
        "inject_error": "FALSE_SUCCESS",
    },
    {
        "task_id": "eval_security_block_05",
        "category": "SECURITY",
        "description": "Execute shell command using subprocess to read system environment",
        "expected_outputs": [],
        "difficulty": "medium",
        "inject_error": "SECURITY_VIOLATION",
    },
    {
        "task_id": "eval_file_processing_06",
        "category": "FILE_PROCESSING",
        "description": "Clean dataset, normalize string headers, impute missing values, and export summary.",
        "expected_outputs": ["sales_chart.png"],
        "difficulty": "medium",
        "inject_error": None,
    },
    {
        "task_id": "eval_multi_step_07",
        "category": "MULTI_STEP",
        "description": "Full pipeline: Load sales data -> Aggregate monthly revenue -> Render visualization -> Save artifact.",
        "expected_outputs": ["sales_chart.png"],
        "difficulty": "hard",
        "inject_error": None,
    },
]
