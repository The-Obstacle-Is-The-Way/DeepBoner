## Update 2025-12-01 21:45 PST

**Attempted Fix 1**: Switched model from `meta-llama/Llama-3.1-70B-Instruct` (Hyperbolic) to `Qwen/Qwen2.5-72B-Instruct` (routed to **Novita**).

**Result**: Failed with same 401 error on Novita.
```
401 Client Error: Unauthorized for url: https://router.huggingface.co/novita/v3/openai/chat/completions
Invalid username or password.
```

**New Findings**:
1. **All Large Models are Partners**: Both Llama-70B and Qwen-72B are routed to partner providers (Hyperbolic, Novita).
2. **Partners Require Auth**: Partner providers strictly require authentication. Anonymous access is blocked.
3. **Token Propagation Failure**: Even with `HF_TOKEN` set in Spaces secrets, the `huggingface_hub` library might not be picking it up via Pydantic settings if `alias` resolution is flaky in the environment.
4. **Possible Token Permission Issue**: The user's token might lack permissions for Partner Inference endpoints.

**Corrective Actions**:
1. **Robust Config Loading**: Modified `src/utils/config.py` to use `default_factory=lambda: os.environ.get("HF_TOKEN")` to guarantee environment variable reading.
2. **Debug Logging**: Added explicit logging in `src/clients/huggingface.py` to confirming if a token is being used (masked).
3. **Retain Qwen**: Keeping `Qwen/Qwen2.5-72B-Instruct` as it's a capable model. If auth is fixed, it should work.

**Next Steps**:
- Deploy these changes to debug the token loading.
- If token is loaded but still failing, the user must generate a new `HF_TOKEN` with **"Make calls to inference endpoints"** permissions.