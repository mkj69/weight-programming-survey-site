"""Keyword rules for relevance, categories and tags. Used by the daily job (no LLM) and as a
first pass before the LLM pass in the initial build."""
import re

I = re.I
CAT = {
    "wsp": [r"weight[- ]space programming", r"\bLLMs? (?:can )?(?:natively )?(?:read|write|edit)s? .{0,30}weights", r"qwenputer",
            r"read(?:s|ing)? (?:the )?(?:raw )?(?:neural network |model )?weights", r"(?:edit|rewrit)(?:e|es|ing) (?:the )?(?:model|network)'?s? weights",
            r"hand-?(?:written|crafted|set|coded) (?:neural network |transformer )?weights", r"weightprogrambench", r"wspbench"],
    "compile": [r"compiled transformers?", r"\bRASP\b", r"\btracr\b", r"transformer programs?", r"compil(?:e|es|ed|ing|er) .{0,40}(?:into|to) .{0,20}weights",
                r"looped transformers?", r"programmable computers?", r"computer (?:inside|in|into) .{0,25}weights", r"hand-?crafted transformers?",
                r"(?:analytically|explicitly) (?:constructed|set|compiled) weights", r"torchwright", r"qwen(?:fs|gpu|pu)\b", r"nesformer", r"transformer-vm"],
    "edit": [r"model editing", r"knowledge editing", r"edit(?:ing)? (?:factual )?(?:knowledge|facts|associations)", r"\bROME\b", r"\bMEMIT\b",
             r"locate[- ]then[- ]edit|locate[- ]and[- ]edit", r"task arithmetic", r"task vectors?", r"model merging", r"merg(?:e|es|ing) (?:fine-tuned |multiple |large language )?models",
             r"weight averaging", r"model soups?", r"model diffing", r"weight diff(?:erence)?s?", r"parameter difference", r"chat vector", r"rank-one (?:model )?edit"],
    "fast": [r"fast[- ]weights?", r"fast weight programmers?", r"self-referential", r"self-modifying (?:neural )?networks?", r"hyper-?networks?",
             r"delta rule", r"test-time training", r"learned optimizers?", r"learning to learn", r"meta-learn(?:s|ed|ing)? (?:the |an? )?(?:update|learning) rules?"],
    "wsl": [r"weight[- ]spaces?(?![- ]program)", r"neural functionals?", r"model zoos?", r"parameter generation", r"generat(?:e|es|ing|ive models? of) (?:neural network |model )?(?:weights|parameters|checkpoints)",
            r"network diffusion", r"weights as (?:input|data)", r"learning (?:on|from) (?:neural network |model )?weights", r"metanetworks?", r"equivariant .{0,30}weight",
            r"predict(?:ing)? .{0,40}from (?:its |the )?weights", r"hyper-representations?"],
}
TAGS = {
    "reading weights": r"read(?:s|ing)? .{0,20}weights|interpret(?:ing)? weights|from (?:the )?weights alone",
    "editing weights": r"edit(?:s|ing|ed)? .{0,20}weights|weight edit",
    "hand-written weights": r"hand-?(?:written|crafted|set|coded)|writ(?:e|es|ing) (?:the )?weights",
    "replication": r"replicat|reproduc",
    "critique": r"critiqu|memoriz|not superhuman|skeptic|limitation",
    "benchmark": r"benchmark|bench\b",
    "agent in the loop": r"\bagents?\b.{0,40}(?:optimi[sz]er|training loop)|reactive optimi[sz]er",
    "RASP / Tracr": r"\bRASP\b|\btracr\b",
    "compiler": r"compiler|compil(?:e|ed|ing)",
    "circuit injection": r"inject",
    "computer in weights": r"cpu|computer|risc-v|x86|gpu inside|filesystem|nintendo|doom",
    "provably correct": r"provabl|proof of correctness",
    "knowledge editing": r"knowledge editing|edit(?:ing)? (?:factual )?knowledge|factual associations?",
    "locate and edit": r"locat(?:e|ing)|causal tracing|\bROME\b|\bMEMIT\b",
    "task vectors": r"task (?:vectors?|arithmetic)",
    "model merging": r"merg(?:e|es|ing)|model soups?|weight averaging",
    "model diffing": r"diffing|weight diff|parameter difference|chat vector",
    "unlearning": r"unlearn",
    "sequential editing": r"sequential|lifelong|continual (?:model |knowledge )?edit",
    "fast weights": r"fast[- ]weight",
    "linear attention": r"linear attention|linear transformers?|delta rule|deltanet",
    "self-referential": r"self-referential|self-modifying",
    "hypernetworks": r"hyper-?networks?",
    "test-time training": r"test-time training|learn(?:s|ing)? at test time",
    "meta-learning": r"meta-learn|learning to learn|learned optimi",
    "weight representations": r"representation|embedding of (?:neural network )?weights|hyper-representation",
    "equivariant networks": r"equivarian|permutation symmetr|neural functional|metanetwork",
    "weight generation": r"generat(?:e|es|ing|ive)|diffusion",
    "model zoos": r"model zoos?",
    "predicting from weights": r"predict",
}
TAG_CAT = {
    "wsp": ["reading weights", "editing weights", "hand-written weights", "replication", "critique", "application", "agent in the loop", "benchmark"],
    "compile": ["RASP / Tracr", "compiler", "circuit injection", "computer in weights", "provably correct"],
    "edit": ["knowledge editing", "locate and edit", "task vectors", "model merging", "model diffing", "unlearning", "sequential editing"],
    "fast": ["fast weights", "linear attention", "self-referential", "hypernetworks", "test-time training", "meta-learning"],
    "wsl": ["weight representations", "equivariant networks", "weight generation", "model zoos", "predicting from weights"],
}
# Patterns that also appear outside ML (graph theory "hypernetworks", function spaces "weight space") or
# are too broad on their own. A title match on these only marks the item as uncertain.
AMBIGUOUS = {r"hyper-?networks?", r"weight[- ]spaces?(?![- ]program)", r"learning to learn", r"model zoos?", r"parameter generation", r"delta rule",
             r"task vectors?", r"weight averaging", r"self-referential", r"learned optimizers?", r"test-time training", r"transformer programs?",
             r"network diffusion", r"metanetworks?", r"equivariant .{0,30}weight", r"programmable computers?", r"\bRASP\b",
             r"predict(?:ing)? .{0,40}from (?:its |the )?weights", r"merg(?:e|es|ing) (?:fine-tuned |multiple |large language )?models", r"weight diff(?:erence)?s?",
             r"parameter difference", r"generat(?:e|es|ing|ive models? of) (?:neural network |model )?(?:weights|parameters|checkpoints)"}
_CAT = {c: [re.compile(p, I) for p in ps] for c, ps in CAT.items()}
_AMB = {c: [p in AMBIGUOUS for p in ps] for c, ps in CAT.items()}
_TAG = {t: re.compile(p, I) for t, p in TAGS.items()}


def score(title, text):
    """Return {cat: 2 if the title matches, 1 if only the body matches}."""
    out = {}
    if re.search(r"retract|corrigendum|erratum|gumm(?:y|ies)", title or "", I):
        return out
    for c, ps in _CAT.items():
        hit = [amb for p, amb in zip(ps, _AMB[c]) if p.search(title or "")]
        if hit and not all(hit):
            out[c] = 2
        elif hit or any(p.search(text or "") for p in ps):
            out[c] = 1
    return out


def tags_for(cats, title, text):
    blob = f"{title or ''} {text or ''}"
    tags = []
    for c in cats:
        for t in TAG_CAT[c]:
            if t in _TAG and _TAG[t].search(blob) and t not in tags:
                tags.append(t)
    return tags
