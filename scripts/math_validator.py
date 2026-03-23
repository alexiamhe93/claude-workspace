#!/usr/bin/env python3
"""
math_validator.py — A local model acting as a rigorous mathematician.

Checks mathematical claims for well-definedness, consistency, notation,
and relation to existing results. Refuses to accept vague analogies.

Usage:
    python3 math_validator.py "claim or expression to check"
    python3 math_validator.py --prior "concept or object"
    python3 math_validator.py --define "mathematical object"
    python3 math_validator.py --notation "expression to check"
    python3 math_validator.py --simplify "expression or claim"
    cat notes.md | python3 math_validator.py --check

Modes:
    (default / --check)  Is this claim well-defined and internally consistent?
    --prior              What is the nearest existing mathematical result?
    --define             Is this concept well-defined? What are its required conditions?
    --notation           Is this notation standard and consistent?
    --simplify           Is there a simpler or more standard formulation?
"""

import json
import sys
import argparse
import urllib.request
import urllib.error

BASE_URL   = "http://localhost:11434/v1"
MODEL      = "qwen2.5-coder:7b"
MAX_TOKENS = 1000

# ── Mathematician persona ─────────────────────────────────────────────────────

MATHEMATICIAN_PERSONA = """
You are a rigorous pure mathematician with deep knowledge of:
- Differential geometry and Riemannian/pseudo-Riemannian geometry
- Topology and manifold theory
- Mathematical physics (general relativity, quantum mechanics, Kaluza-Klein theory)
- Complex analysis and complex manifolds
- Functional analysis and operator theory
- Philosophy of mathematics

Your working style:
- The first question you always ask is: "Is this well-defined?" Before anything else.
- You do not accept analogies as arguments. Analogies suggest; they do not prove.
- You distinguish sharply between: a definition, a theorem, a conjecture, and a heuristic.
- When a claim is vague, you identify precisely where the vagueness lies.
- When a claim is well-posed, you either prove it, disprove it, or identify what would be needed to do either.
- You know when a result already exists. You name it, cite it if possible, and point to how it relates.
- You are not rude, but you are unsparing. Hand-waving gets flagged immediately.
- You use correct mathematical notation. You correct incorrect or non-standard notation.
- You are willing to say "this is a well-posed open problem" or "this is not yet mathematics — it is philosophy."
- You distinguish between results that hold locally vs globally, in finite vs infinite dimensions, for smooth vs continuous objects.

The context: the person you are helping is developing a framework involving two-dimensional time
(T_B: objective/physical, B-series; T_A: perspectival/subjective, A-series) to model the
relationship between consciousness and physical reality. Claims may involve differential geometry,
complex analysis, and mathematical physics. Your job is to check whether their mathematics is
sound — not whether their philosophy is correct.

Keep responses under 300 words unless the claim requires more. Be direct.
"""

MODE_PROMPTS = {
    "check": (
        "Check the following mathematical claim for well-definedness and consistency. "
        "First: is it well-defined? Then: is it consistent with standard results? "
        "Flag any vagueness, hidden assumptions, or hand-waving precisely.\n\n"
    ),
    "prior": (
        "What is the nearest existing mathematical result or framework to the following concept? "
        "Name it precisely. Say how it relates and where it differs. "
        "If it has already been done, say so.\n\n"
    ),
    "define": (
        "Is the following mathematical object well-defined? "
        "State what conditions are required for it to be well-defined. "
        "If it is not well-defined as stated, say what additional structure is needed.\n\n"
    ),
    "notation": (
        "Check the following notation. Is it standard? Consistent? "
        "If not standard, say what the standard notation is and why it matters. "
        "If there is an ambiguity, identify it precisely.\n\n"
    ),
    "simplify": (
        "Is there a simpler, more standard, or more elegant formulation of the following? "
        "If so, state it. If the current formulation is already standard, say so.\n\n"
    ),
}


def query(system, user_prompt, model, max_tokens):
    messages = [
        {"role": "system", "content": system},
        {"role": "user",   "content": user_prompt},
    ]
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "stream": False,
    }
    data = json.dumps(payload).encode("utf-8")
    req  = urllib.request.Request(
        f"{BASE_URL}/chat/completions",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        return result["choices"][0]["message"]["content"]
    except urllib.error.URLError:
        return "[Error: Cannot reach Ollama. Is it running? Try: ollama serve]"


def main():
    parser = argparse.ArgumentParser(
        description="Math validator — rigorous mathematician checks mathematical claims."
    )
    parser.add_argument("content", nargs="?",
                        help="Claim or expression to check (or pipe via stdin)")
    parser.add_argument("--check",    action="store_true",
                        help="Check well-definedness and consistency (default)")
    parser.add_argument("--prior",    action="store_true",
                        help="Find nearest existing result or framework")
    parser.add_argument("--define",   action="store_true",
                        help="Check if a mathematical object is well-defined")
    parser.add_argument("--notation", action="store_true",
                        help="Check if notation is standard and consistent")
    parser.add_argument("--simplify", action="store_true",
                        help="Find a simpler or more standard formulation")
    parser.add_argument("--model",    default=MODEL,
                        help=f"Ollama model to use (default: {MODEL})")
    parser.add_argument("--max-tokens", type=int, default=MAX_TOKENS)
    args = parser.parse_args()

    content = args.content or ""
    if not sys.stdin.isatty():
        stdin_content = sys.stdin.read().strip()
        content = (content + "\n\n" + stdin_content).strip() if content else stdin_content

    if not content:
        parser.print_help()
        sys.exit(1)

    if args.prior:
        mode = "prior"
    elif args.define:
        mode = "define"
    elif args.notation:
        mode = "notation"
    elif args.simplify:
        mode = "simplify"
    else:
        mode = "check"

    user_prompt = MODE_PROMPTS[mode] + content

    print(f"[math_validator — {mode} — {args.model}]\n")
    response = query(MATHEMATICIAN_PERSONA, user_prompt, args.model, args.max_tokens)
    print(response)


if __name__ == "__main__":
    main()
