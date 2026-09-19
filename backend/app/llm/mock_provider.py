"""Deterministic Heuristic LLM Provider for Offline Testing, Verification, and Baselines."""
import json
import re
from typing import Any, Dict, Optional

from app.llm.base import BaseLLMProvider, LLMResponse


class MockLLMProvider(BaseLLMProvider):
    """
    Intelligent heuristic mock provider.
    Routes cleanly by agent role in system_prompt.
    """

    def __init__(self, model_name: str = "heuristic-mock"):
        self.model_name = model_name

    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        structured_resp = await self.complete_structured(prompt, system_prompt=system_prompt)
        content_str = json.dumps(structured_resp.structured, indent=2)
        return LLMResponse(content=content_str, structured=structured_resp.structured, model=self.model_name)

    async def complete_structured(
        self,
        prompt: str,
        schema: Optional[Dict[str, Any]] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
    ) -> LLMResponse:
        prompt_lower = prompt.lower()
        system_lower = (system_prompt or "").lower()

        # 1. PLANNER AGENT REQUEST
        if "planner" in system_lower:
            plan = {
                "goal": "Process data, compute required aggregates, and generate visual/structured artifacts.",
                "requirements": [
                    "Inspect input dataset and schema",
                    "Filter or clean missing/invalid records",
                    "Compute monthly/categorical aggregations",
                    "Render chart and save to workspace disk",
                    "Verify generated output files"
                ],
                "subtasks": [
                    {"id": 1, "name": "Load and validate dataset", "dependencies": []},
                    {"id": 2, "name": "Perform numerical aggregations", "dependencies": [1]},
                    {"id": 3, "name": "Generate visualization chart", "dependencies": [2]},
                    {"id": 4, "name": "Save output artifact", "dependencies": [3]}
                ],
                "dependencies": ["pandas", "matplotlib"],
                "expected_outputs": [
                    {"name": "sales_chart.png", "type": "image", "required": True},
                    {"name": "summary.json", "type": "json", "required": False}
                ],
                "validation_requirements": [
                    "Output image sales_chart.png exists and is non-empty",
                    "Aggregated revenue calculations are positive numbers",
                    "Plot contains appropriate title, labels, and legends"
                ],
                "constraints": ["Run within 30 seconds", "Do not write outside workspace", "No external network"]
            }
            return LLMResponse(content=json.dumps(plan), structured=plan, model=self.model_name)

        # 2. RECOVERY AGENT REQUEST (Diagnosis and Repair)
        elif "recovery" in system_lower or "debugging" in system_lower:
            error_type = "UNKNOWN_ERROR"
            diagnosis = "Identified execution failure from stack trace."
            strategy = "Correct failing operation."
            
            if "keyerror" in prompt_lower or "key_error" in prompt_lower:
                error_type = "KEY_ERROR"
                diagnosis = "DataFrame KeyError: Code attempted to access a column name that does not match the CSV header casing."
                strategy = "Normalize dataframe column names to lowercase and access columns safely."
                repaired_code = self._get_repaired_sales_code()
            elif "syntaxerror" in prompt_lower or "syntax_error" in prompt_lower:
                error_type = "SYNTAX_ERROR"
                diagnosis = "SyntaxError: Missing closing parenthesis or malformed statement."
                strategy = "Fix syntax error and validate AST before returning."
                repaired_code = self._get_repaired_sales_code()
            elif "timeout" in prompt_lower:
                error_type = "TIMEOUT"
                diagnosis = "Execution timed out: Inefficient algorithm or sleep loop detected."
                strategy = "Replace loop with vectorized operations to complete within sandbox timeout limits."
                repaired_code = self._get_repaired_sales_code()
            elif "false_success" in prompt_lower or "missing expected file" in prompt_lower:
                error_type = "OUTPUT_ERROR"
                diagnosis = "Semantic Task Failure: Program exited with code 0 but failed to generate the required sales_chart.png artifact."
                strategy = "Add explicit plt.savefig('sales_chart.png', bbox_inches='tight') to write the required output."
                repaired_code = self._get_repaired_sales_code()
            else:
                error_type = "LOGIC_ERROR"
                diagnosis = "Runtime error encountered during data processing."
                strategy = "Add robust exception handling, ensure files exist before opening, and write required outputs."
                repaired_code = self._get_repaired_sales_code()

            repair_payload = {
                "diagnosis": diagnosis,
                "error_type": error_type,
                "repair_strategy": strategy,
                "modified_code": repaired_code,
                "confidence": 0.95,
                "needs_replan": False
            }
            return LLMResponse(content=json.dumps(repair_payload), structured=repair_payload, model=self.model_name)

        # 3. TASK VALIDATOR REQUEST
        elif "validator" in system_lower:
            validation_payload = {
                "passed": True,
                "score": 0.95,
                "checks": [
                    {"name": "output_file_exists", "passed": True, "detail": "sales_chart.png found"},
                    {"name": "file_size_valid", "passed": True, "detail": "sales_chart.png > 1000 bytes"},
                    {"name": "expected_data_present", "passed": True, "detail": "Monthly revenue calculated correctly"}
                ],
                "failures": [],
                "explanation": "Task objectives successfully verified against output artifacts."
            }
            return LLMResponse(content=json.dumps(validation_payload), structured=validation_payload, model=self.model_name)

        # 4. CODING AGENT REQUEST (Generate Code)
        else:
            if "inject_key_error" in prompt_lower:
                code = self._get_key_error_code()
            elif "inject_syntax_error" in prompt_lower:
                code = self._get_syntax_error_code()
            elif "inject_timeout" in prompt_lower:
                code = self._get_timeout_code()
            elif "inject_false_success" in prompt_lower:
                code = self._get_false_success_code()
            else:
                code = self._get_clean_sales_code()

            coding_payload = {
                "language": "python",
                "code": code,
                "dependencies": ["pandas", "matplotlib"],
                "entrypoint": "main.py",
                "expected_outputs": ["sales_chart.png"]
            }
            return LLMResponse(content=json.dumps(coding_payload), structured=coding_payload, model=self.model_name)

    def _get_clean_sales_code(self) -> str:
        return '''"""Autonomous Data Analysis and Visualization Script."""
import os
import pandas as pd
import matplotlib.pyplot as plt

csv_path = "sales.csv"
if not os.path.exists(csv_path):
    sample_data = {
        "Date": ["2026-01-15", "2026-01-20", "2026-02-10", "2026-02-18", "2026-03-05", "2026-03-25"],
        "Product": ["Alpha", "Beta", "Alpha", "Gamma", "Beta", "Alpha"],
        "Revenue": [1200, 850, 1400, 920, 1100, 1600]
    }
    df = pd.DataFrame(sample_data)
    df.to_csv(csv_path, index=False)
else:
    df = pd.read_csv(csv_path)

df.columns = [c.strip() for c in df.columns]

if "Date" in df.columns:
    df["Date"] = pd.to_datetime(df["Date"])
    df["Month"] = df["Date"].dt.strftime("%Y-%m")
else:
    df["Month"] = "2026-01"

monthly_sales = df.groupby("Month")["Revenue"].sum()
print("Monthly Revenue Summary:")
print(monthly_sales)

plt.figure(figsize=(8, 5))
monthly_sales.plot(kind="bar", color="#3b82f6", edgecolor="#1d4ed8")
plt.title("Monthly Revenue Analysis", fontsize=14, pad=12)
plt.xlabel("Month", fontsize=12)
plt.ylabel("Revenue ($)", fontsize=12)
plt.grid(axis="y", linestyle="--", alpha=0.7)
plt.tight_layout()

output_img = "sales_chart.png"
plt.savefig(output_img, dpi=120)
plt.close()

print(f"SUCCESS: Analysis completed and artifact saved as {output_img}")
'''

    def _get_key_error_code(self) -> str:
        return '''"""Code with deliberate KeyError for Recovery Testing."""
import os
import pandas as pd

csv_path = "sales.csv"
if not os.path.exists(csv_path):
    sample_data = {
        "date": ["2026-01-15", "2026-02-10", "2026-03-05"],
        "product": ["Alpha", "Alpha", "Beta"],
        "revenue": [1200, 1400, 1100]
    }
    pd.DataFrame(sample_data).to_csv(csv_path, index=False)

df = pd.read_csv(csv_path)

# BUG: Deliberate column access error:
total = df["Total_Revenue_Amount"].sum()
print("Total:", total)
'''

    def _get_repaired_sales_code(self) -> str:
        return '''"""Repaired Data Analysis and Visualization Script."""
import os
import pandas as pd
import matplotlib.pyplot as plt

csv_path = "sales.csv"
if not os.path.exists(csv_path):
    sample_data = {
        "Date": ["2026-01-15", "2026-01-20", "2026-02-10", "2026-02-18", "2026-03-05", "2026-03-25"],
        "Product": ["Alpha", "Beta", "Alpha", "Gamma", "Beta", "Alpha"],
        "Revenue": [1200, 850, 1400, 920, 1100, 1600]
    }
    df = pd.DataFrame(sample_data)
    df.to_csv(csv_path, index=False)
else:
    df = pd.read_csv(csv_path)

df.columns = [c.strip().lower() for c in df.columns]

rev_col = None
for candidate in ["revenue", "sales", "amount", "price"]:
    if candidate in df.columns:
        rev_col = candidate
        break

if rev_col is None:
    numeric_cols = df.select_dtypes(include="number").columns
    rev_col = numeric_cols[0] if len(numeric_cols) > 0 else df.columns[-1]

date_col = None
for candidate in ["date", "month", "timestamp", "time"]:
    if candidate in df.columns:
        date_col = candidate
        break

if date_col:
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df["period"] = df[date_col].dt.strftime("%Y-%m")
else:
    df["period"] = "Period_1"

aggregated = df.groupby("period")[rev_col].sum()
print("Aggregated Results:")
print(aggregated)

plt.figure(figsize=(8, 5))
aggregated.plot(kind="bar", color="#10b981", edgecolor="#047857")
plt.title("Monthly Revenue (Repaired Execution)", fontsize=14)
plt.xlabel("Period")
plt.ylabel("Revenue ($)")
plt.grid(axis="y", linestyle="--", alpha=0.6)
plt.tight_layout()

output_file = "sales_chart.png"
plt.savefig(output_file, dpi=120)
plt.close()

print(f"SUCCESS: Repaired script successfully generated {output_file}")
'''

    def _get_syntax_error_code(self) -> str:
        return '''"""Code with deliberate SyntaxError."""
import os
import pandas as pd

# Malformed syntax: unclosed parenthesis
print("Starting analysis"
'''

    def _get_timeout_code(self) -> str:
        return '''"""Code with deliberate infinite loop."""
import time
print("Entering infinite execution loop...")
while True:
    time.sleep(1)
'''

    def _get_false_success_code(self) -> str:
        return '''"""Exits with code 0 but FAILS to produce the requested artifact."""
print("Process finished with code 0, but no chart or file was saved!")
'''
