import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from slidemaker.llm.adapters.api.vertex_gemini import VertexGeminiAdapter

async def debug_response():
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
    adapter = VertexGeminiAdapter(
        model="gemini-3-pro-image-preview",
        project_id=project_id,
        location="global",
        api_version="v1beta1",
        use_global_endpoint=True,
    )
    
    prompt = "Analyze the layout of a slide. Output valid JSON with a 'title' field."
    print(f"Prompt: {prompt}")
    
    # We want to see the raw text response
    payload = adapter._build_request_payload(prompt)
    response_data = await adapter._make_request(payload)
    
    print("\n--- API RESPONSE DATA START ---")
    import json
    print(json.dumps(response_data, indent=2))
    print("--- API RESPONSE DATA END ---")
    
    if "candidates" in response_data and response_data["candidates"]:
        content = response_data["candidates"][0].get("content", {})
        parts = content.get("parts", [])
        print(f"\nNumber of parts: {len(parts)}")
        for i, part in enumerate(parts):
            print(f"\n--- PART {i} START ---")
            if "text" in part:
                print(part["text"])
            elif "thought" in part:
                print(f"[THOUGHT] {part['thought']}")
            else:
                print(part)
            print(f"--- PART {i} END ---")
    
    raw_text = adapter._extract_text_response(response_data)
    
    extracted_json = adapter._extract_json(raw_text)
    print("\n--- EXTRACTED JSON START ---")
    print(extracted_json)
    print("--- EXTRACTED JSON END ---")

if __name__ == "__main__":
    asyncio.run(debug_response())

