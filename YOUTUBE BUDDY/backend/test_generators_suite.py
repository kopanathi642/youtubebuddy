"""
YouTube Buddy — Complete App & All Generators Automated Test Suite.
Tests every generator with dedicated prompts, verifies database persistence,
checks image rendering to disk, and outputs a complete diagnostic report.
"""
import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

import httpx
from httpx import ASGITransport

# Set UTF-8 for Windows console
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Ensure backend directory is in sys.path
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.main import app
from app.core.database import init_db
from app.core.cache import init_cache


# ── Test Prompts Catalog ──────────────────────────────────────────────────

IMAGE_GENERATORS = [
    {
        "tool_id": "create",
        "name": "AI Image Generator",
        "prompt": "Hyper-realistic cyberpunk coding setup with glowing cyan and purple neon reflections on glass desk, 8k",
        "style": "cinematic",
        "aspect_ratio": "16:9",
    },
    {
        "tool_id": "cineshot",
        "name": "Cinematic Photos",
        "prompt": "Anamorphic wide shot of an astronaut gazing at an alien solar eclipse on a red desert planet, cinematic bokeh",
        "style": "cinematic",
        "aspect_ratio": "16:9",
    },
    {
        "tool_id": "moodboard",
        "name": "AI Moodboard",
        "prompt": "Minimalist Scandinavian design moodboard, warm oak textures, ceramic vases, earthy tones and sage green swatches",
        "style": "editorial",
        "aspect_ratio": "16:9",
    },
    {
        "tool_id": "character",
        "name": "Character Designer",
        "prompt": "Futuristic cyborg ronin with weathered carbon-fiber armor, glowing orange katana, concept art sheet",
        "style": "concept art",
        "aspect_ratio": "16:9",
    },
    {
        "tool_id": "persona",
        "name": "Influencer Creator",
        "prompt": "Charismatic tech creator smiling in studio with acoustic foam panels, soft keylight and Sony FX3 on desk",
        "style": "photorealistic",
        "aspect_ratio": "16:9",
    },
    {
        "tool_id": "aesthetic",
        "name": "Style Finder",
        "prompt": "Vintage 1970s analog recording studio with tube amplifiers, magnetic tape reels, and golden sun dust motes",
        "style": "vintage",
        "aspect_ratio": "16:9",
    },
    {
        "tool_id": "fashion",
        "name": "Fashion Designer",
        "prompt": "Avant-garde streetwear jacket with modular magnetic pouches, translucent polymer collar, and reflective seams",
        "style": "editorial",
        "aspect_ratio": "16:9",
    },
    {
        "tool_id": "draw",
        "name": "Sketch to Art",
        "prompt": "Hand-sketched architectural elevation transformed into a luxury waterfall glass villa surrounded by rainforest",
        "style": "architectural",
        "aspect_ratio": "16:9",
    },
    {
        "tool_id": "inpaint",
        "name": "Object Eraser",
        "prompt": "Studio portrait with distracting background microphones and cables removed, leaving pure velvet gradient backdrop",
        "style": "clean",
        "aspect_ratio": "16:9",
    },
    {
        "tool_id": "faceswap",
        "name": "Face Swapper",
        "prompt": "Executive profile headshot in dark navy suit with clean corporate lighting and subtle bokeh",
        "style": "corporate",
        "aspect_ratio": "16:9",
    },
    {
        "tool_id": "charswap",
        "name": "Replace Character",
        "prompt": "Replace medieval blacksmith with a futuristic plasma weapons armorer inside an orbital shipyard foundry",
        "style": "sci-fi",
        "aspect_ratio": "16:9",
    },
    {
        "tool_id": "relight",
        "name": "Photo Lighting",
        "prompt": "Dramatic split lighting with vibrant blue rim light and warm amber key on a subject looking towards camera",
        "style": "dramatic",
        "aspect_ratio": "16:9",
    },
    {
        "tool_id": "upscale",
        "name": "Photo Upscaler",
        "prompt": "Macro photo of human iris with intricate crystalline patterns, enhanced sharpness and restored micro-contrast",
        "style": "macro",
        "aspect_ratio": "16:9",
    },
]

TEXT_AND_VIDEO_GENERATORS = [
    {
        "tool_id": "script",
        "name": "AI Video Script Generator",
        "prompt": "Write a 60-second high-retention video script about 3 AI breakthroughs in 2026 that will replace smartphones",
        "style": "viral",
    },
    {
        "tool_id": "seo",
        "name": "YouTube SEO Optimizer",
        "prompt": "Optimize SEO for a video titled 'I Built an AI Video Generator in 24 Hours' covering nextjs, fastapi, langgraph",
        "style": "high ctr",
    },
    {
        "tool_id": "trend",
        "name": "Trending Topics Analyzer",
        "prompt": "Analyze current breakout creator trends in AI productivity tools and workflow automation",
        "style": "analytical",
    },
    {
        "tool_id": "viral",
        "name": "Viral Clip & Hook Generator",
        "prompt": "Create 5 irresistible psychological video hooks for a finance video about compound interest vs real estate",
        "style": "viral hook",
    },
    {
        "tool_id": "cinematic",
        "name": "Cinematic Scene Planner",
        "prompt": "High-octane night car chase through neo-Seoul under torrential neon rain, panning from bumper cam to crane shot",
        "style": "cinematic action",
    },
    {
        "tool_id": "voiceover",
        "name": "AI Voiceover Script Generator",
        "prompt": "Dramatic BBC-style nature documentary narration exploring deep ocean bioluminescent creatures",
        "style": "documentary",
    },
    {
        "tool_id": "upload",
        "name": "Upload Metadata Generator",
        "prompt": "Create complete upload metadata package for a full-length Next.js 15 crash course with chapters and tags",
        "style": "educational",
    },
    {
        "tool_id": "ads",
        "name": "Video Ad Maker",
        "prompt": "High-converting 15-second TikTok/Reels direct response video ad for a noise-cancelling AI podcast microphone",
        "style": "direct response",
    },
    {
        "tool_id": "canvas",
        "name": "Video Idea Canvas",
        "prompt": "Mind-map concept breakdown exploring 'Can AI Think Like a Human?' across philosophy, neuroscience, and LLMs",
        "style": "conceptual",
    },
    {
        "tool_id": "ugc",
        "name": "AI Human Presenter / UGC",
        "prompt": "Authentic creator monologue review talking to camera: 'This tool saved my channel 15 hours every single week'",
        "style": "ugc casual",
    },
    {
        "tool_id": "motion",
        "name": "Motion Graphics Planner",
        "prompt": "Kinetic typography and animated statistic callouts explaining the exponential curve of GPU computing power",
        "style": "motion design",
    },
    {
        "tool_id": "animate",
        "name": "Video Animation Planner",
        "prompt": "Morphing transitions from a physical retro camera lens into digital pixels and exploding into an AI galaxy",
        "style": "3d animation",
    },
    {
        "tool_id": "mixed",
        "name": "Style Blender",
        "prompt": "Blend 1930s rubber-hose black and white animation with modern synthwave neon color palettes and 60fps physics",
        "style": "hybrid blend",
    },
    {
        "tool_id": "sketch",
        "name": "Drawing to Video",
        "prompt": "Storyboard sketch of a tiny seedling growing into a colossal bioluminescent tree spanning the cloud cover",
        "style": "storyboard",
    },
]

AGENT_GENERATORS = [
    {
        "agent_name": "trend",
        "name": "LangGraph Trend Intelligence Agent",
        "prompt": "Identify unsaturated high-growth content niches in AI automation for YouTube 2026",
    },
    {
        "agent_name": "script",
        "name": "LangGraph Viral Script Agent",
        "prompt": "Write a retention-optimized 3-minute video on How to Build Your First LangGraph Agent",
    },
    {
        "agent_name": "seo",
        "name": "LangGraph Algorithmic SEO Agent",
        "prompt": "Complete metadata optimization for 'Mastering Python for AI Engineers'",
    },
    {
        "agent_name": "shorts",
        "name": "LangGraph Shorts & Viral Moment Agent",
        "prompt": "Extract 3 viral short-form clips with high rewatchability from a 20-minute founder interview",
    },
    {
        "agent_name": "upload",
        "name": "LangGraph Publishing & Upload Agent",
        "prompt": "Prepare launch packaging for a premier YouTube tech video on autonomous agents",
    },
    {
        "agent_name": "pipeline",
        "name": "LangGraph End-to-End Autonomous Pipeline",
        "prompt": "Building High-Profit Micro-SaaS in 2026 with AI",
    },
]


async def run_full_suite() -> Dict[str, Any]:
    print("=" * 70)
    print("  🚀 YOUTUBE BUDDY — COMPLETE APP & ALL GENERATORS TEST SUITE")
    print("=" * 70)

    report: Dict[str, Any] = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "summary": {},
        "sections": {},
    }

    await init_db()
    await init_cache()

    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver", timeout=120.0) as client:
        # ── 1. System Health ──────────────────────────────────────────────
        print("\n[1/6] 🏥 Testing System Health...")
        health_resp = await client.get("/healthz")
        health_data = health_resp.json() if health_resp.status_code == 200 else {}
        print(f"  ✓ /healthz: Status {health_resp.status_code} | Engine: {health_data.get('ai_engine')} | Active Providers: {list(health_data.get('providers', {}).keys())}")
        report["sections"]["system_health"] = {
            "status_code": health_resp.status_code,
            "response": health_data,
            "passed": health_resp.status_code == 200,
        }

        # ── 2. Auth Flow ──────────────────────────────────────────────────
        print("\n[2/6] 🔐 Testing Authentication & User Profile...")
        user_email = f"suite_tester_{int(time.time())}@youtubebuddy.com"
        signup_payload = {
            "email": user_email,
            "password": "SecureTestPassword@2026",
            "display_name": "Generator Test Suite Runner",
        }
        signup_resp = await client.post("/api/v1/auth/signup", json=signup_payload)
        token = ""
        if signup_resp.status_code == 200:
            token = signup_resp.json().get("access_token", "")
            print(f"  ✓ User registered successfully: {user_email}")
        else:
            # Fallback to login
            login_resp = await client.post("/api/v1/auth/login", json={
                "email": "demo@youtubebuddy.com",
                "password": "Demo@12345",
            })
            if login_resp.status_code == 200:
                token = login_resp.json().get("access_token", "")
                print(f"  ✓ Demo login authenticated successfully.")
            else:
                print(f"  ✗ Auth failed: {login_resp.status_code} {login_resp.text}")

        headers = {"Authorization": f"Bearer {token}"} if token else {}

        # Profile check
        profile_resp = await client.get("/api/v1/auth/profile", headers=headers)
        profile_ok = profile_resp.status_code == 200
        print(f"  ✓ Profile check: status {profile_resp.status_code} | Email: {profile_resp.json().get('email') if profile_ok else 'N/A'}")
        report["sections"]["auth"] = {
            "signup_status": signup_resp.status_code,
            "profile_status": profile_resp.status_code,
            "passed": profile_ok,
        }

        # ── 3. Testing All Studio Image Generators ────────────────────────
        print("\n[3/6] 🎨 Testing Studio Image Generators (13 Tools)...")
        image_results = []
        for idx, item in enumerate(IMAGE_GENERATORS, 1):
            t0 = time.time()
            tool_id = item["tool_id"]
            name = item["name"]
            prompt = item["prompt"]
            req_body = {
                "tool_id": tool_id,
                "prompt": prompt,
                "style": item["style"],
                "aspect_ratio": item["aspect_ratio"],
                "provider": "auto",
            }

            resp = await client.post("/api/v1/studio/generate", headers=headers, json=req_body)
            duration = round(time.time() - t0, 3)
            passed = resp.status_code == 200

            file_exists = False
            file_size = 0
            res_data = {}

            if passed:
                res_data = resp.json()
                preview_url = res_data.get("preview_url") or ""
                # Check rendered file on disk
                if preview_url:
                    filename = preview_url.split("/")[-1]
                    file_path = BACKEND_DIR / "rendered" / filename
                    if file_path.exists():
                        file_exists = True
                        file_size = file_path.stat().st_size

            print(f"  [{idx:02d}/13] {name} ({tool_id}): {'✅ PASSED' if passed else '❌ FAILED'} ({duration}s)")
            if passed:
                print(f"         Preview: {res_data.get('preview_url')} | Disk File: {file_exists} ({file_size} bytes)")
            else:
                print(f"         Error: {resp.status_code} -> {resp.text[:120]}")

            image_results.append({
                "tool_id": tool_id,
                "name": name,
                "prompt": prompt,
                "duration_seconds": duration,
                "status_code": resp.status_code,
                "passed": passed,
                "file_exists_on_disk": file_exists,
                "file_size_bytes": file_size,
                "preview_url": res_data.get("preview_url"),
                "simulated": res_data.get("simulated", False),
            })

        report["sections"]["image_generators"] = {
            "total": len(IMAGE_GENERATORS),
            "passed": sum(1 for r in image_results if r["passed"]),
            "results": image_results,
        }

        # ── 4. Testing All Studio Video & Text Generators ──────────────────
        print("\n[4/6] 🎬 Testing Studio Video, Text & Content Generators (14 Tools)...")
        text_results = []
        for idx, item in enumerate(TEXT_AND_VIDEO_GENERATORS, 1):
            t0 = time.time()
            tool_id = item["tool_id"]
            name = item["name"]
            prompt = item["prompt"]
            req_body = {
                "tool_id": tool_id,
                "prompt": prompt,
                "style": item["style"],
                "aspect_ratio": "16:9",
                "duration": 10,
                "provider": "auto",
            }

            resp = await client.post("/api/v1/studio/generate", headers=headers, json=req_body)
            duration = round(time.time() - t0, 3)
            passed = resp.status_code == 200

            res_data = {}
            has_structured_output = False
            has_poster = False
            output_snippet = ""

            if passed:
                res_data = resp.json()
                model_output = res_data.get("model_output")
                has_structured_output = model_output is not None
                has_poster = bool(res_data.get("preview_url"))
                output_str = str(model_output if model_output else res_data.get("generated_text", ""))
                output_snippet = output_str[:120] + "..." if len(output_str) > 120 else output_str

            print(f"  [{idx:02d}/14] {name} ({tool_id}): {'✅ PASSED' if passed else '❌ FAILED'} ({duration}s)")
            if passed:
                print(f"         Poster: {has_poster} | Structured Output: {has_structured_output}")
                print(f"         Preview: {output_snippet}")
            else:
                print(f"         Error: {resp.status_code} -> {resp.text[:120]}")

            text_results.append({
                "tool_id": tool_id,
                "name": name,
                "prompt": prompt,
                "duration_seconds": duration,
                "status_code": resp.status_code,
                "passed": passed,
                "has_structured_output": has_structured_output,
                "has_poster_preview": has_poster,
                "output_snippet": output_snippet,
                "simulated": res_data.get("simulated", False),
            })

        report["sections"]["text_and_video_generators"] = {
            "total": len(TEXT_AND_VIDEO_GENERATORS),
            "passed": sum(1 for r in text_results if r["passed"]),
            "results": text_results,
        }

        # ── 5. Testing All LangGraph Multi-Agent Workflows ─────────────────
        print("\n[5/6] 🤖 Testing LangGraph Multi-Agent Workflows (6 Agents)...")
        agent_results = []
        for idx, item in enumerate(AGENT_GENERATORS, 1):
            t0 = time.time()
            agent_name = item["agent_name"]
            name = item["name"]
            prompt = item["prompt"]

            req_body = {
                "agent_name": agent_name,
                "prompt": prompt,
            }

            resp = await client.post("/api/v1/agents/run", headers=headers, json=req_body)
            duration = round(time.time() - t0, 3)
            passed = resp.status_code == 200

            res_data = {}
            status_val = ""
            output_keys = []

            if passed:
                res_data = resp.json()
                status_val = res_data.get("status", "")
                output = res_data.get("output")
                if isinstance(output, dict):
                    output_keys = list(output.keys())
                elif isinstance(output, str):
                    try:
                        decoded = json.loads(output)
                        if isinstance(decoded, dict):
                            output_keys = list(decoded.keys())
                    except Exception:
                        output_keys = ["raw_text"]

            print(f"  [{idx:02d}/06] {name} ({agent_name}): {'✅ PASSED' if passed else '❌ FAILED'} ({duration}s)")
            if passed:
                print(f"         Status: {status_val} | Schema Keys: {output_keys[:6]}")
            else:
                print(f"         Error: {resp.status_code} -> {resp.text[:120]}")

            agent_results.append({
                "agent_name": agent_name,
                "name": name,
                "prompt": prompt,
                "duration_seconds": duration,
                "status_code": resp.status_code,
                "passed": passed,
                "workflow_status": status_val,
                "output_keys": output_keys,
            })

        report["sections"]["agent_workflows"] = {
            "total": len(AGENT_GENERATORS),
            "passed": sum(1 for r in agent_results if r["passed"]),
            "results": agent_results,
        }

        # ── 6. Testing Dedicated Generator Endpoints & Persistence ────────
        print("\n[6/6] 📦 Testing Dedicated Endpoints & Database Persistence...")
        special_results = []

        # Dedicated Cinematic
        t0 = time.time()
        cin_resp = await client.post(
            "/api/v1/cinematic/generate",
            headers=headers,
            json={"prompt": "Tokyo cyberpunk street in neon rain", "duration": 6, "cameraMovement": "pan left"},
        )
        cin_passed = cin_resp.status_code == 200
        special_results.append({
            "endpoint": "/api/v1/cinematic/generate",
            "name": "Dedicated Cinematic Generator",
            "passed": cin_passed,
            "status_code": cin_resp.status_code,
            "duration": round(time.time() - t0, 3),
        })
        print(f"  ✓ /api/v1/cinematic/generate: {'✅ PASSED' if cin_passed else '❌ FAILED'}")

        # Create test upload to link captions
        upload_id = 1
        try:
            chunk_resp = await client.post(
                "/api/v1/uploads/chunk",
                headers=headers,
                files={"file": ("test_sample.mp4", b"\x00" * 4096, "video/mp4")},
            )
            if chunk_resp.status_code == 200:
                chunk_data = chunk_resp.json()
                meta_resp = await client.post(
                    "/api/v1/uploads/metadata",
                    headers=headers,
                    json={
                        "filename": "test_sample.mp4",
                        "storage_path": chunk_data["path"],
                        "content_type": "video/mp4",
                        "size_bytes": chunk_data["size_bytes"],
                        "duration_seconds": 30,
                    },
                )
                if meta_resp.status_code == 200:
                    upload_id = meta_resp.json()["id"]
                    print(f"  ✓ Linked test upload #{upload_id} created for captions.")
        except Exception as e:
            print(f"  ℹ Upload note: {e}")

        # Dedicated Captions VTT
        t0 = time.time()
        vtt_resp = await client.post(
            "/api/v1/captions/generate",
            headers=headers,
            json={
                "upload_id": upload_id,
                "transcript": "Welcome to YouTube Buddy. Learn AI creation today.",
                "format": "vtt",
            },
        )
        vtt_json = vtt_resp.json() if vtt_resp.status_code == 200 else {}
        vtt_passed = vtt_resp.status_code == 200 and "WEBVTT" in vtt_json.get("content", "")
        special_results.append({
            "endpoint": "/api/v1/captions/generate (VTT)",
            "name": "VTT Caption Generator",
            "passed": vtt_passed,
            "status_code": vtt_resp.status_code,
            "duration": round(time.time() - t0, 3),
        })
        print(f"  ✓ /api/v1/captions/generate (VTT): {'✅ PASSED' if vtt_passed else '❌ FAILED'}")

        # Dedicated Captions SRT
        t0 = time.time()
        srt_resp = await client.post(
            "/api/v1/captions/generate",
            headers=headers,
            json={
                "upload_id": upload_id,
                "transcript": "Step one install the app. Step two start creating.",
                "format": "srt",
            },
        )
        srt_json = srt_resp.json() if srt_resp.status_code == 200 else {}
        srt_passed = srt_resp.status_code == 200 and "-->" in srt_json.get("content", "")
        special_results.append({
            "endpoint": "/api/v1/captions/generate (SRT)",
            "name": "SRT Caption Generator",
            "passed": srt_passed,
            "status_code": srt_resp.status_code,
            "duration": round(time.time() - t0, 3),
        })
        print(f"  ✓ /api/v1/captions/generate (SRT): {'✅ PASSED' if srt_passed else '❌ FAILED'}")

        # Studio History Persistence
        hist_resp = await client.get("/api/v1/studio/history", headers=headers)
        hist_data = hist_resp.json() if hist_resp.status_code == 200 else {}
        hist_items = hist_data.get("data", [])
        hist_passed = hist_resp.status_code == 200 and len(hist_items) > 0
        special_results.append({
            "endpoint": "/api/v1/studio/history",
            "name": "Studio Generation Persistence & Query",
            "passed": hist_passed,
            "status_code": hist_resp.status_code,
            "persisted_count": len(hist_items),
        })
        print(f"  ✓ /api/v1/studio/history: {'✅ PASSED' if hist_passed else '❌ FAILED'} ({len(hist_items)} generations persisted)")

        # Agent History Persistence
        agent_list_resp = await client.get("/api/v1/agents/", headers=headers)
        agent_list_data = agent_list_resp.json() if agent_list_resp.status_code == 200 else {}
        agents_tracked = agent_list_data.get("data", [])
        agent_list_passed = agent_list_resp.status_code == 200 and len(agents_tracked) > 0
        special_results.append({
            "endpoint": "/api/v1/agents/",
            "name": "Agent Lifecycle & History Tracking",
            "passed": agent_list_passed,
            "status_code": agent_list_resp.status_code,
            "agents_tracked": len(agents_tracked),
        })
        print(f"  ✓ /api/v1/agents/: {'✅ PASSED' if agent_list_passed else '❌ FAILED'} ({len(agents_tracked)} agents tracked)")

        report["sections"]["dedicated_and_persistence"] = {
            "total": len(special_results),
            "passed": sum(1 for r in special_results if r["passed"]),
            "results": special_results,
        }

        # ── Grand Summary ─────────────────────────────────────────────────
        total_generators_tested = (
            len(IMAGE_GENERATORS) + len(TEXT_AND_VIDEO_GENERATORS) + len(AGENT_GENERATORS) + 3
        )
        total_generators_passed = (
            report["sections"]["image_generators"]["passed"]
            + report["sections"]["text_and_video_generators"]["passed"]
            + report["sections"]["agent_workflows"]["passed"]
            + sum(1 for r in special_results[:3] if r["passed"])
        )

        overall_score = round((total_generators_passed / total_generators_tested) * 100, 1)

        report["summary"] = {
            "total_generators_tested": total_generators_tested,
            "total_generators_passed": total_generators_passed,
            "pass_rate_percentage": overall_score,
            "image_generators_passed": f"{report['sections']['image_generators']['passed']}/{len(IMAGE_GENERATORS)}",
            "text_generators_passed": f"{report['sections']['text_and_video_generators']['passed']}/{len(TEXT_AND_VIDEO_GENERATORS)}",
            "agents_passed": f"{report['sections']['agent_workflows']['passed']}/{len(AGENT_GENERATORS)}",
            "database_persistence_verified": hist_passed and agent_list_passed,
        }

        print("\n" + "=" * 70)
        print(f"  📊 FINAL SCORE: {total_generators_passed}/{total_generators_tested} Generators Passed ({overall_score}%)")
        print("=" * 70)

    # Save JSON report
    report_file = BACKEND_DIR / "test_report.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\n[REPORT SAVED] -> {report_file}")

    return report


if __name__ == "__main__":
    asyncio.run(run_full_suite())
