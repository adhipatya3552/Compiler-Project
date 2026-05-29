import time
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from schemas.models import GenerateRequest, GenerateResponse, FinalOutput
from pipeline import stage1_intent, stage2_design, stage3_schema, stage4_refine
from validator.repair import check_cross_layer_consistency

app = FastAPI(title="App Compiler API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten this in production
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"status": "App Compiler API is running"}


@app.post("/generate", response_model=GenerateResponse)
def generate(request: GenerateRequest):
    start = time.time()
    retries = 0

    try:
        if request.mode == "fast":
            from pipeline import unified
            print(f"[Fast Mode] Compiling app in a single unified step from: {request.prompt[:80]}...")
            intent, design, refined_schema, llm_issues = unified.run(request.prompt)
            static_issues = check_cross_layer_consistency(refined_schema.model_dump())
            stages_completed = 1
        else:
            # ── Stage 1: Intent Extraction ────────────────────────────────
            print(f"[Stage 1] Extracting intent from: {request.prompt[:80]}...")
            intent = stage1_intent.run(request.prompt)

            # ── Stage 2: System Design ────────────────────────────────────
            print("[Stage 2] Generating system design...")
            design = stage2_design.run(intent)

            # ── Stage 3: Schema Generation ────────────────────────────────
            print("[Stage 3] Generating schemas (UI + API + DB + Auth)...")
            schema = stage3_schema.run(intent, design)

            # ── Stage 4: Refinement + Repair ─────────────────────────────
            print("[Stage 4] Refining and validating schemas...")
            refined_schema, llm_issues = stage4_refine.run(intent, design, schema)

            # ── Static Cross-Layer Checks ─────────────────────────────────
            static_issues = check_cross_layer_consistency(refined_schema.model_dump())
            stages_completed = 4

        # Build final output
        final = FinalOutput(
            intent=intent,
            system_design=design,
            schema=refined_schema,
            validation_issues=llm_issues,
            generation_metadata={
                "model": "openai/gpt-4o-mini",
                "stages_completed": stages_completed,
                "static_issues_found": len(static_issues),
                "llm_issues_found": len(llm_issues),
                "retries": retries,
                "latency_ms": round((time.time() - start) * 1000, 2),
                "compiler_mode": request.mode
            }
        )

        return GenerateResponse(
            success=True,
            output=final,
            retries=retries,
            latency_ms=round((time.time() - start) * 1000, 2)
        )

    except Exception as e:
        print(f"[ERROR] Pipeline failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "api_key_set": bool(os.getenv("OPENROUTER_API_KEY"))
    }