from difflib import SequenceMatcher


# -------------------------------
# SIMILARITY FUNCTION
# -------------------------------

def similarity(a, b):
    """
    Calculate similarity between two strings (0 to 1)
    """
    return SequenceMatcher(None, a, b).ratio()


# -------------------------------
# SMART TARGET FINDER 🔥
# -------------------------------

def find_target(target, ocr_data, min_score=0.5):
    """
    Find best matching UI element from OCR results

    Priority:
    1. Exact match
    2. Partial match
    3. Fuzzy match

    Returns:
        Best matching bbox dict or None
    """

    target = target.lower().strip()

    best_match = None
    best_score = 0

    for item in ocr_data:
        text = item["text"].lower().strip()

        # Exact match (highest priority)
        if text == target:
            return item

        # Partial match
        if target in text:
            score = len(target) / len(text)
        else:
            # Fuzzy similarity
            score = similarity(target, text)

        # 🔥 Boost clickable words
        if any(word in text for word in ["login", "submit", "search", "ok", "next", "yes"]):
            score += 0.1

        # Track best
        if score > best_score:
            best_score = score
            best_match = item

    if best_score >= min_score:
        return best_match

    return None


# -------------------------------
# FIND ALL MATCHES (OPTIONAL)
# -------------------------------

def find_all_targets(target, ocr_data, min_score=0.5):
    """
    Return all matching elements
    """
    target = target.lower().strip()
    matches = []

    for item in ocr_data:
        text = item["text"].lower().strip()

        if target in text or similarity(target, text) >= min_score:
            matches.append(item)

    return matches


# -------------------------------
# FIND TARGET WITH SCORE
# -------------------------------

def find_target_with_score(target, ocr_data):
    """
    Returns (best_match, score)
    """
    target = target.lower().strip()

    best = None
    best_score = 0

    for item in ocr_data:
        text = item["text"].lower().strip()

        score = similarity(target, text)

        if score > best_score:
            best_score = score
            best = item

    return best, best_score


# -------------------------------
# GET CENTER POINT
# -------------------------------

def get_center(bbox):
    """
    Get center coordinates of bounding box
    """
    return (
        int(bbox["x"] + bbox["w"] // 2),
        int(bbox["y"] + bbox["h"] // 2)
    )


# -------------------------------
# GET TOP MATCHES (RANKED)
# -------------------------------

def rank_targets(target, ocr_data):
    """
    Returns sorted matches (best first)
    """
    target = target.lower().strip()

    scored = []

    for item in ocr_data:
        text = item["text"].lower().strip()

        score = similarity(target, text)

        scored.append((score, item))

    scored.sort(reverse=True, key=lambda x: x[0])

    return scored


# -------------------------------
# DEBUG PRINT (OPTIONAL)
# -------------------------------

def print_matches(target, ocr_data, top_n=5):
    """
    Print top matches for debugging
    """
    ranked = rank_targets(target, ocr_data)

    print(f"\n🔍 Top matches for '{target}':\n")

    for i, (score, item) in enumerate(ranked[:top_n], 1):
        print(f"{i}. {item['text']} → score: {score:.2f}")