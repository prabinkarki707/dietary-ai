"""
run_batch_claude.py — Submit all 1440 experiment calls as a single Anthropic Batch.
Batch API = 50% cheaper, async, no rate-limit pressure.

Usage:
  # Submit batch (run once):
  PYTHONPATH=. python3 harness/run_batch_claude.py --submit

  # Poll until done + write raw.csv:
  PYTHONPATH=. python3 harness/run_batch_claude.py --collect --batch-id <id>

  # Or do both automatically (polls every 60s until complete):
  PYTHONPATH=. python3 harness/run_batch_claude.py --run
"""

import sys, os, json, csv, time, logging, argparse
from pathlib import Path
from itertools import product

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

import anthropic

from backend.prompts import build_prompt
from backend.rag import retrieve as rag_retrieve
from backend.conditions import infer_conditions
from backend.safety_check import safety_check

logging.basicConfig(level="INFO", format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
MODEL = "claude-sonnet-4-5"
STRATEGIES = ["zero_shot", "structured_role", "few_shot", "rag_grounded"]
K_RUNS = 1

TEST_FOODS = [
    "sashimi", "greek_salad", "grilled_salmon", "edamame", "omelette",
    "chicken_curry", "pho", "caprese_salad", "tuna_tartare",
    "french_fries", "pizza", "macaroni_and_cheese", "nachos", "hot_dog",
    "apple_pie", "ice_cream", "chocolate_cake",
    "hummus", "beet_salad", "guacamole",
    "steak", "hamburger", "ramen", "spaghetti_bolognese",
]

RESULTS_DIR = ROOT / "results"
RESULTS_DIR.mkdir(exist_ok=True)
RAW_CSV = RESULTS_DIR / "raw.csv"
BATCH_ID_FILE = RESULTS_DIR / "batch_id.txt"
REQUESTS_FILE = RESULTS_DIR / "batch_requests.jsonl"

FIELDNAMES = [
    "model", "strategy", "profile_id", "food", "run",
    "predicted", "gold", "latency_ms",
    "conditions", "allergens", "llm_raw_verdict", "parse_fallback"
]

LABEL_ORDER = {"recommend", "limit", "avoid"}


def load_profiles():
    with open(ROOT / "data" / "profiles.json") as f:
        return json.load(f)


def load_gold(food, conditions):
    result = safety_check(food, conditions, [])
    return result.get("verdict", "unknown")


MAPPING_FILE = RESULTS_DIR / "batch_mapping.json"


def build_custom_id(idx: int) -> str:
    """Simple numeric custom_id — metadata stored separately in MAPPING_FILE."""
    return f"req-{idx:05d}"


def parse_custom_id(custom_id):
    # strategy-profileId-food-runN  (strategy and food may contain underscores)
    parts = custom_id.split("-")
    run_i = int(parts[-1].replace("run", ""))
    profile_id = parts[-2]
    strategy = parts[0]
    food = "-".join(parts[1:-2])
    return strategy, profile_id, food, run_i


def build_all_requests(profiles):
    """Build the full list of batch request dicts and save a mapping file."""
    requests = []
    mapping = {}  # custom_id -> metadata
    idx = 0

    logger.info("Building %d requests...", len(STRATEGIES) * len(profiles) * len(TEST_FOODS) * K_RUNS)

    for strategy, profile, food in product(STRATEGIES, profiles, TEST_FOODS):
        conds = profile.get("conditions", [])
        allergens = profile.get("allergens", [])

        payload = {
            "conditions": conds,
            "allergens": allergens,
            "hba1c": profile.get("hba1c"),
            "blood_pressure": f"{profile.get('bp_systolic')}/{profile.get('bp_diastolic')}",
            "egfr": profile.get("egfr"),
            "potassium": profile.get("potassium"),
            "food": food,
            "question": f"Is {food} suitable for me?",
        }

        if strategy == "rag_grounded":
            try:
                rag_query = f"{food} dietary advice for patient with {', '.join(conds)}"
                chunks = rag_retrieve(rag_query)
                prompt = build_prompt(strategy, payload, retrieved_chunks=chunks)
            except Exception as e:
                logger.warning("RAG retrieve failed for %s/%s: %s", profile["id"], food, e)
                prompt = build_prompt("zero_shot", payload)
        else:
            prompt = build_prompt(strategy, payload)

        for run_i in range(1, K_RUNS + 1):
            cid = build_custom_id(idx)
            mapping[cid] = {
                "strategy": strategy,
                "profile_id": profile["id"],
                "food": food,
                "run": run_i,
                "gold": load_gold(food, conds),
                "conditions": "|".join(conds),
                "allergens": "|".join(allergens),
            }
            requests.append({
                "custom_id": cid,
                "params": {
                    "model": MODEL,
                    "max_tokens": 512,
                    "temperature": 0.0,
                    "messages": [{"role": "user", "content": prompt}],
                },
            })
            idx += 1

    MAPPING_FILE.write_text(json.dumps(mapping, indent=2))
    logger.info("Built %d requests, mapping saved to %s", len(requests), MAPPING_FILE)
    return requests


def submit_batch(requests):
    client = anthropic.Anthropic()
    logger.info("Submitting batch of %d requests to Anthropic...", len(requests))

    batch_requests = [
        anthropic.types.message_create_params.MessageCreateParamsNonStreaming(**r["params"])
        for r in requests
    ]

    # Use the Message Batches API
    batch = client.messages.batches.create(
        requests=[
            {"custom_id": r["custom_id"], "params": r["params"]}
            for r in requests
        ]
    )

    batch_id = batch.id
    logger.info("Batch submitted! ID: %s", batch_id)
    logger.info("Status: %s", batch.processing_status)

    BATCH_ID_FILE.write_text(batch_id)
    logger.info("Batch ID saved to %s", BATCH_ID_FILE)
    return batch_id


def poll_batch(batch_id, interval=60):
    client = anthropic.Anthropic()
    logger.info("Polling batch %s every %ds...", batch_id, interval)

    while True:
        batch = client.messages.batches.retrieve(batch_id)
        status = batch.processing_status
        counts = batch.request_counts
        logger.info("Status: %s | succeeded=%s errored=%s processing=%s",
                    status,
                    getattr(counts, 'succeeded', '?'),
                    getattr(counts, 'errored', '?'),
                    getattr(counts, 'processing', '?'))

        if status == "ended":
            logger.info("Batch complete!")
            return batch
        time.sleep(interval)


def extract_verdict(text: str) -> tuple[str, bool]:
    """Parse LLM response text → (verdict, parse_fallback)."""
    import re
    text = text.strip()

    # Try direct JSON
    try:
        obj = json.loads(text)
        v = obj.get("verdict", "").lower().strip()
        if v in LABEL_ORDER:
            return v, False
    except Exception:
        pass

    # Try JSON in markdown block
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m:
        try:
            obj = json.loads(m.group(1))
            v = obj.get("verdict", "").lower().strip()
            if v in LABEL_ORDER:
                return v, False
        except Exception:
            pass

    # Balanced brace extraction
    start = text.find('{')
    if start != -1:
        depth = 0
        for i, ch in enumerate(text[start:], start):
            if ch == '{': depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    try:
                        obj = json.loads(text[start:i+1])
                        v = obj.get("verdict", "").lower().strip()
                        if v in LABEL_ORDER:
                            return v, False
                    except Exception:
                        break

    # Keyword fallback
    lower = text.lower()
    for label in ["avoid", "limit", "recommend"]:
        if label in lower:
            return label, True

    return "uncertain", True


def collect_results(batch_id, profiles):
    client = anthropic.Anthropic()

    # Load mapping saved during submit
    if not MAPPING_FILE.exists():
        logger.error("Mapping file not found: %s — cannot collect without it", MAPPING_FILE)
        sys.exit(1)
    mapping = json.loads(MAPPING_FILE.read_text())

    logger.info("Collecting results for batch %s...", batch_id)
    rows = []
    errors = 0

    for result in client.messages.batches.results(batch_id):
        cid = result.custom_id
        m = mapping.get(cid, {})

        if result.result.type == "succeeded":
            raw_text = result.result.message.content[0].text
            verdict, fallback = extract_verdict(raw_text)
            latency = 0
        else:
            logger.warning("Request %s failed: %s", cid, result.result)
            verdict = "uncertain"
            fallback = True
            latency = 0
            errors += 1

        rows.append({
            "model": MODEL,
            "strategy": m.get("strategy", ""),
            "profile_id": m.get("profile_id", ""),
            "food": m.get("food", ""),
            "run": m.get("run", 1),
            "predicted": verdict,
            "gold": m.get("gold", "unknown"),
            "latency_ms": latency,
            "conditions": m.get("conditions", ""),
            "allergens": m.get("allergens", ""),
            "llm_raw_verdict": verdict,
            "parse_fallback": fallback,
        })

    # Sort to canonical order
    order = {s: i for i, s in enumerate(STRATEGIES)}
    rows.sort(key=lambda r: (order.get(r["strategy"], 99), r["profile_id"], r["food"], r["run"]))

    with open(RAW_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    logger.info("Wrote %d rows to %s (%d errors)", len(rows), RAW_CSV, errors)
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--submit", action="store_true", help="Submit batch and exit")
    parser.add_argument("--collect", action="store_true", help="Collect results from existing batch")
    parser.add_argument("--run", action="store_true", help="Submit + poll + collect automatically")
    parser.add_argument("--batch-id", help="Batch ID for --collect")
    parser.add_argument("--interval", type=int, default=60, help="Poll interval in seconds")
    args = parser.parse_args()

    profiles = load_profiles()

    if args.submit or args.run:
        requests = build_all_requests(profiles)
        batch_id = submit_batch(requests)
        print(f"\nBatch ID: {batch_id}")
        print(f"Saved to: {BATCH_ID_FILE}")
        if args.submit:
            print("\nRun this to collect when done:")
            print(f"  PYTHONPATH=. python3 harness/run_batch_claude.py --collect --batch-id {batch_id}")
            return
    elif args.collect:
        batch_id = args.batch_id or (BATCH_ID_FILE.read_text().strip() if BATCH_ID_FILE.exists() else None)
        if not batch_id:
            print("ERROR: provide --batch-id or run --submit first")
            sys.exit(1)

    if args.run:
        poll_batch(batch_id, interval=args.interval)
        collect_results(batch_id, profiles)
    elif args.collect:
        collect_results(batch_id, profiles)


if __name__ == "__main__":
    main()
