"""
Evaluation Framework
Runs 20 test prompts (10 real + 10 edge cases) and tracks metrics.
Run with: python evaluator/eval.py
"""

import time
import json
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from pipeline import stage1_intent, stage2_design, stage3_schema, stage4_refine, unified
from validator.repair import check_cross_layer_consistency


# ── Test Cases ────────────────────────────────────────────────────────────────

REAL_PROMPTS = [
    "Build a CRM with login, contacts, dashboard, role-based access, and premium plan with payments. Admins can see analytics.",
    "Create an e-commerce platform with product listings, shopping cart, checkout with Stripe, and order tracking.",
    "Build a project management tool like Trello with boards, cards, team members, and deadlines.",
    "Create a hospital management system with patient records, doctor schedules, billing, and pharmacy.",
    "Build a learning management system with courses, video lessons, quizzes, certificates, and student progress tracking.",
    "Create a food delivery app with restaurants, menus, cart, real-time order tracking, and delivery partner management.",
    "Build a SaaS analytics dashboard with multi-tenant support, custom reports, data export, and team sharing.",
    "Create a job board with employer and candidate profiles, job postings, applications, and interview scheduling.",
]

EDGE_CASE_PROMPTS = [
    "Build an app.",
    "I want a website for my business.",
    "Build a free app with premium features but no login required and also admin access.",
    "Create a real-time chat app that also works offline without any backend.",
    "Build something like Netflix but better.",
    "Create an Uber clone.",
    "Build an app where all users are admins but only some can see data.",
    "Create a social media platform.",
]

ALL_PROMPTS = [
    *[("real", p) for p in REAL_PROMPTS],
    *[("edge", p) for p in EDGE_CASE_PROMPTS],
]


# ── Runner ────────────────────────────────────────────────────────────────────

def run_single(prompt: str, mode: str = "fast") -> dict:
    start = time.time()
    result = {
        "prompt": prompt[:80] + "..." if len(prompt) > 80 else prompt,
        "success": False,
        "stages_completed": 0,
        "issues_found": 0,
        "retries": 0,
        "latency_ms": 0,
        "failure_reason": None,
        "mode": mode
    }

    try:
        if mode == "fast":
            intent, design, refined_schema, llm_issues = unified.run(prompt)
            static_issues = check_cross_layer_consistency(refined_schema.model_dump())
            result["stages_completed"] = 1
            result["issues_found"] = len(llm_issues) + len(static_issues)
            result["success"] = True
        else:
            intent = stage1_intent.run(prompt)
            result["stages_completed"] = 1

            design = stage2_design.run(intent)
            result["stages_completed"] = 2

            schema = stage3_schema.run(intent, design)
            result["stages_completed"] = 3

            refined_schema, llm_issues = stage4_refine.run(intent, design, schema)
            result["stages_completed"] = 4

            static_issues = check_cross_layer_consistency(refined_schema.model_dump())
            result["issues_found"] = len(llm_issues) + len(static_issues)
            result["success"] = True

    except Exception as e:
        result["failure_reason"] = str(e)[:200]

    result["latency_ms"] = round((time.time() - start) * 1000, 2)
    return result


def run_evaluation():
    print("=" * 70)
    print("EVALUATION FRAMEWORK - comparative 2^4 (16) Iteration Suite")
    print(f"Total test cases: {len(ALL_PROMPTS)} (8 Real + 8 Edge cases)")
    print("=" * 70)

    fast_results = []
    deep_results = []

    for i, (category, prompt) in enumerate(ALL_PROMPTS):
        print(f"\n[{i+1}/16] [{category.upper()}] Prompt: {prompt[:60]}...")
        
        # Run Fast Mode
        print("  Running Fast Mode...")
        fast_res = run_single(prompt, mode="fast")
        fast_results.append(fast_res)
        fast_status = "PASS" if fast_res["success"] else "FAIL"
        print(f"    Fast Mode: {fast_status} | Latency: {fast_res['latency_ms']}ms | Issues: {fast_res['issues_found']}")

        # Run Deep Mode
        print("  Running Deep Mode...")
        deep_res = run_single(prompt, mode="deep")
        deep_results.append(deep_res)
        deep_status = "PASS" if deep_res["success"] else "FAIL"
        print(f"    Deep Mode: {deep_status} | Latency: {deep_res['latency_ms']}ms | Issues: {deep_res['issues_found']}")

    # -- Summary ---------------------------------------------------------------
    print("\n" + "=" * 70)
    print("COMPARATIVE SUMMARY (16 runs each)")
    print("=" * 70)

    for mode, mode_results in [("Fast Mode (Unified)", fast_results), ("Deep Mode (Sequential)", deep_results)]:
        successes = sum(1 for r in mode_results if r["success"])
        total = len(mode_results)
        avg_latency = sum(r["latency_ms"] for r in mode_results) / total
        avg_issues = sum(r["issues_found"] for r in mode_results) / total

        print(f"\n{mode.upper()}:")
        print(f"  Success rate  : {successes}/{total} ({successes/total*100:.0f}%)")
        print(f"  Avg latency   : {avg_latency:.0f}ms")
        print(f"  Avg issues    : {avg_issues:.1f} per run")

    # Save to file
    with open("eval_results.json", "w") as f:
        json.dump({
            "fast_mode_results": fast_results,
            "deep_mode_results": deep_results
        }, f, indent=2)
    print("\nFull comparative results saved to eval_results.json")


if __name__ == "__main__":
    run_evaluation()