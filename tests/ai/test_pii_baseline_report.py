import json
import time
from typing import Dict, List

import pytest

from src.ai.pii_scrubber import detect_pii, redact_pii


def load_jsonl(path: str) -> List[Dict]:
    data = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            data.append(json.loads(line))
    return data


def _canon(s: str) -> str:
    # Canonicalize tokens for fair matching across formatting variants
    s = s.strip().rstrip(".,;")

    # For names, remove common prefixes and normalize spacing
    if any(prefix in s.lower() for prefix in ["patient", "name:", "contact:"]):
        # Remove prefixes and extra whitespace
        s_lower = s.lower()
        for prefix in ["patient", "name:", "contact:"]:
            if s_lower.startswith(prefix):
                s = s[len(prefix) :].strip()
                break

    # Remove spaces for phone numbers and other identifiers
    # But keep single space for names
    if any(char.isdigit() for char in s):
        # Likely a phone number or ID - remove all spaces
        return s.replace(" ", "")
    else:
        # Likely a name - normalize to single spaces
        return " ".join(s.split())


def test_pii_precision_recall_baseline(tmp_path):
    samples = load_jsonl("tests/fixtures/pii_synthetic_samples.jsonl")

    tp = 0
    fp = 0
    fn = 0

    for s in samples:
        text = s["text"]
        expected = set(_canon(x) for x in s.get("pii", []))
        detected = detect_pii(text)
        # Flatten detected values
        detected_values = set()
        for vals in detected.values():
            for v in vals:
                detected_values.add(_canon(v))

        tp += len(expected & detected_values)
        fp_items = detected_values - expected
        fn_items = expected - detected_values
        fp += len(fp_items)
        fn += len(fn_items)
        if fp_items or fn_items:
            print("FP:", sorted(fp_items))
            print("FN:", sorted(fn_items))

        redacted, details = redact_pii(text)
        # Ensure no expected PII remains in redacted text
        for v in expected:
            assert v not in redacted

    precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 1.0
    f1_score = (
        2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    )

    # Generate detailed report for QA evidence
    report_path = tmp_path / "pii_baseline_report.json"
    report = {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1_score, 4),
        "metrics": {
            "true_positives": tp,
            "false_positives": fp,
            "false_negatives": fn,
            "total_samples": len(samples),
        },
        "thresholds": {"precision_min": 0.95, "recall_min": 0.95, "f1_score_min": 0.95},
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "test_version": "1.0",
    }

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    # Print summary for CI visibility
    print("\n" + "=" * 60)
    print("PII DETECTION BASELINE REPORT")
    print("=" * 60)
    print(f"Precision: {precision:.4f} (threshold: ≥0.95)")
    print(f"Recall:    {recall:.4f} (threshold: ≥0.95)")
    print(f"F1 Score:  {f1_score:.4f} (threshold: ≥0.95)")
    print(f"Samples:   {len(samples)}")
    print(f"TP/FP/FN:  {tp}/{fp}/{fn}")
    print("=" * 60)

    if precision < 0.95 or recall < 0.95:
        print("\n⚠️  WARNING: Thresholds not met!")
        if precision < 0.95:
            print(f"  - Precision {precision:.4f} < 0.95")
        if recall < 0.95:
            print(f"  - Recall {recall:.4f} < 0.95")
        print("\nRecommendations:")
        print("  1. Review FP/FN cases in test output")
        print("  2. Update PII patterns in src/ai/pii_scrubber.py")
        print("  3. Add more test cases to fixtures")

    # Also save HTML report for better visualization
    html_report_path = tmp_path / "pii_baseline_report.html"
    with open(html_report_path, "w", encoding="utf-8") as f:
        f.write(generate_html_report(report))

    print(f"\nReports saved:")
    print(f"  - JSON: {report_path}")
    print(f"  - HTML: {html_report_path}")

    # Threshold gate (can be tightened as patterns improve)
    assert precision >= 0.95, f"Precision {precision:.4f} < 0.95 threshold"
    assert recall >= 0.95, f"Recall {recall:.4f} < 0.95 threshold"


def generate_html_report(report: Dict) -> str:
    """Generate HTML report for PII baseline results."""
    status = (
        "PASS" if (report["precision"] >= 0.95 and report["recall"] >= 0.95) else "FAIL"
    )
    status_color = "green" if status == "PASS" else "red"

    return f"""
<!DOCTYPE html>
<html>
<head>
    <title>PII Detection Baseline Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .header {{ background: #f5f5f5; padding: 20px; border-radius: 5px; }}
        .metrics {{ display: flex; gap: 20px; margin: 20px 0; }}
        .metric-card {{ 
            flex: 1; padding: 20px; border: 1px solid #ddd; 
            border-radius: 5px; text-align: center;
        }}
        .pass {{ background: #d4edda; border-color: #c3e6cb; }}
        .fail {{ background: #f8d7da; border-color: #f5c6cb; }}
        .status {{ 
            padding: 10px 20px; border-radius: 5px; 
            color: white; font-weight: bold;
            background: {status_color};
        }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #f5f5f5; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>PII Detection Baseline Report</h1>
        <p>Generated: {report["timestamp"]}</p>
        <div class="status">{status}</div>
    </div>
    
    <div class="metrics">
        <div class="metric-card {"pass" if report["precision"] >= 0.95 else "fail"}">
            <h3>Precision</h3>
            <h2>{report["precision"]:.4f}</h2>
            <p>Threshold: ≥{report["thresholds"]["precision_min"]}</p>
        </div>
        <div class="metric-card {"pass" if report["recall"] >= 0.95 else "fail"}">
            <h3>Recall</h3>
            <h2>{report["recall"]:.4f}</h2>
            <p>Threshold: ≥{report["thresholds"]["recall_min"]}</p>
        </div>
        <div class="metric-card {"pass" if report["f1_score"] >= 0.95 else "fail"}">
            <h3>F1 Score</h3>
            <h2>{report["f1_score"]:.4f}</h2>
            <p>Threshold: ≥{report["thresholds"]["f1_score_min"]}</p>
        </div>
    </div>
    
    <h2>Detailed Metrics</h2>
    <table>
        <tr>
            <th>Metric</th>
            <th>Value</th>
            <th>Threshold</th>
            <th>Status</th>
        </tr>
        <tr>
            <td>True Positives</td>
            <td>{report["metrics"]["true_positives"]}</td>
            <td>-</td>
            <td>-</td>
        </tr>
        <tr>
            <td>False Positives</td>
            <td>{report["metrics"]["false_positives"]}</td>
            <td>-</td>
            <td>-</td>
        </tr>
        <tr>
            <td>False Negatives</td>
            <td>{report["metrics"]["false_negatives"]}</td>
            <td>-</td>
            <td>-</td>
        </tr>
        <tr>
            <td>Total Samples</td>
            <td>{report["metrics"]["total_samples"]}</td>
            <td>-</td>
            <td>-</td>
        </tr>
    </table>
    
    <h2>Recommendations</h2>
    <ul>
        <li>Review FP/FN cases in test output for pattern improvements</li>
        <li>Update PII patterns in <code>src/ai/pii_scrubber.py</code> if needed</li>
        <li>Add more diverse test cases to fixtures for better coverage</li>
        <li>Consider adding medical-specific PII patterns (PHI)</li>
    </ul>
    
    <footer>
        <p>Test Version: {report["test_version"]}</p>
        <p>Generated by QA Test Suite</p>
    </footer>
</body>
</html>
"""
