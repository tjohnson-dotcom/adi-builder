def build_mcqs_ai_free(text: str, n: int, glossary: dict[str, list[str]]|None=None) -> list[dict]:
    text = (text or "").strip()
    if not text:
        return []

    # 1) Candidate terms & sentences
    keyphrases = extract_keyphrases(text, top_k=25)
    sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if 50 <= len(s) <= 220][:400]

    mcqs = []
    used_stems = set()

    random.shuffle(sents)
    for sent in sents:
        # pick a phrase present in the sentence
        term = next((k for k in keyphrases if re.search(rf"\\b{re.escape(k)}\\b", sent, re.I)), None)
        if not term:
            continue

        # 2) Stem (cloze or direct)
        stem = re.sub(rf"\\b{re.escape(term)}\\b", "_____", sent, flags=re.I, count=1)
        if stem in used_stems:
            continue

        # 3) Distractors
        pool = [k for k in keyphrases if k.lower() != term.lower()]
        distractors = make_distractors(term, glossary or DEFAULT_GLOSSARY, pool)[:3]
        if len(distractors) < 3:
            # catch-all: sample from pool
            extra = [p for p in pool[:8] if p.lower() != term.lower()]
            for e in extra:
                if len(distractors) >= 3: break
                distractors.append(e)

        options = distractors + [term]
        random.shuffle(options)
        answer_idx = options.index(term)

        # 4) Lint & keep only clean items
        issues = lint_item(stem, options, answer_idx)
        if issues:
            continue

        mcqs.append({
            "stem": stem,
            "options": options,
            "answer": answer_idx
        })
        used_stems.add(stem)

        if len(mcqs) >= n:
            break

    # Fallback if we couldn’t reach n
    while len(mcqs) < n and sents:
        s = sents.pop()
        fake_term = random.choice(keyphrases)
        stem = re.sub(rf"\\b{re.escape(fake_term)}\\b", "_____", s, flags=re.I, count=1)
        opts = make_distractors(fake_term, DEFAULT_GLOSSARY, keyphrases)[:3] + [fake_term]
        random.shuffle(opts)
        ans = opts.index(fake_term)
        if not lint_item(stem, opts, ans):
            mcqs.append({"stem": stem, "options": opts, "answer": ans})

    # index + simple Bloom tag (optional)
    blooms = ["define","identify","apply","analyse","evaluate","justify"]
    out = []
    for i, q in enumerate(mcqs[:n], 1):
        q["index"] = i
        q["bloom"] = random.choice(blooms)
        out.append(q)
    return out
