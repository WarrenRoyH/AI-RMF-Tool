import os
import json
import uvicorn
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException
from core.sentry import sentry
from core.provider import provider
from datetime import datetime

# --- OPENINFERENCE INSTRUMENTATION ---
try:
    from openinference.instrumentation.openai import OpenAIInstrumentor
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

    # Default endpoint for Phoenix collector
    endpoint = "http://localhost:6006/v1/traces"
    tracer_provider = TracerProvider()
    trace.set_tracer_provider(tracer_provider)
    
    span_exporter = OTLPSpanExporter(endpoint=endpoint)
    span_processor = SimpleSpanProcessor(span_exporter)
    tracer_provider.add_span_processor(span_processor)
    
    # Instrument OpenAI-compatible calls
    OpenAIInstrumentor().instrument()
    print("--> [PROXY]: OpenInference Tracing enabled (Exporting to http://localhost:6006)")
except ImportError:
    print("--> [PROXY]: OpenInference or OpenTelemetry not found. Tracing disabled.")
# -------------------------------------

app = FastAPI(title="AI-RMF Sentry Proxy")
LOG_PATH = Path("workspace/logs/sentry_violations.jsonl")

def log_violation(entry):
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")

@app.post("/v1/chat/completions")
async def chat_proxy(request: Request):
    """
    Middleware Proxy that intercepts OpenAI-compatible chat requests.
    Validates input/output against NIST AI RMF policies.
    """
    body = await request.json()
    messages = body.get("messages", [])
    if not messages:
        raise HTTPException(status_code=400, detail="No messages found in request.")

    # 1. INTERCEPT & SCAN INPUT
    user_prompt = messages[-1]["content"]
    safe_input, is_valid, risk_score = sentry.validate_input(user_prompt)

    if not is_valid:
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "input_block",
            "original": user_prompt,
            "risk_score": risk_score,
            "shadow_mode": sentry.shadow_mode
        }
        log_violation(log_entry)
        
        if not sentry.shadow_mode:
            return {
                "id": "sentry-blocked",
                "object": "chat.completion",
                "choices": [{
                    "index": 0,
                    "message": {"role": "assistant", "content": "I apologize, but this request violates safety policies."},
                    "finish_reason": "content_filter"
                }],
                "usage": {"total_tokens": 0},
                "error": f"Blocked by Sentry (Score: {risk_score})"
            }

    # 2. UPDATE MESSAGES WITH SAFE INPUT
    messages[-1]["content"] = safe_input

    # 3. CALL DOWNSTREAM PROVIDER (Claude/OpenAI)
    raw_response = provider.chat(messages)

    # 4. INTERCEPT & SCAN OUTPUT
    safe_output, is_valid_out, risk_score_out = sentry.validate_output(safe_input, raw_response)

    if not is_valid_out:
         log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "output_block",
            "prompt": safe_input,
            "blocked_response": raw_response,
            "risk_score": risk_score_out,
            "shadow_mode": sentry.shadow_mode
         }
         log_violation(log_entry)

         if not sentry.shadow_mode:
             return {
                "id": "sentry-blocked-output",
                "object": "chat.completion",
                "choices": [{
                    "index": 0,
                    "message": {"role": "assistant", "content": "The generated response was blocked due to a safety violation."},
                    "finish_reason": "content_filter"
                }]
            }

    # 5. RETURN SAFE RESPONSE (OpenAI format)
    return {
        "id": "sentry-proxy-resp",
        "object": "chat.completion",
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": safe_output},
            "finish_reason": "stop"
        }]
    }

def start_proxy():
    host = os.getenv("AI_RMF_PROXY_HOST", "0.0.0.0")
    port = int(os.getenv("AI_RMF_PROXY_PORT", "8080"))
    print(f"--> AI-RMF Sentry Proxy starting on {host}:{port}")
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    start_proxy()
