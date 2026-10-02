# evals/metrics.py

def chunk_matches(meta: dict, rel: dict) -> bool:
    """Does this chunk's metadata satisfy one 'relevant' entry?"""
    if meta.get("source") != rel["source"]:
        return False
    if "section_number" in rel:
        return meta.get("section_number") == rel["section_number"]
    if "heading_prefix" in rel:
        trail = meta.get("heading", "")
        return any(part.strip().startswith(rel["heading_prefix"]) for part in trail.split(" > "))
    return False