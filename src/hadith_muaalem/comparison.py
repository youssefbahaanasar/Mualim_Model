"""Word edit alignment; this does not assess articulation or diacritics."""

import unicodedata


def tokenize(text: str) -> list[str]:
    # Keep hamza distinctions, ta marbuta and alif maqsura. Normalize only
    # presentation forms, marks, tatweel and the wasla spelling of alif.
    text = unicodedata.normalize("NFKC", text).replace("ـ", "").replace("ٱ", "ا")
    chars = []
    for char in text:
        category = unicodedata.category(char)
        if category.startswith("M"):
            continue
        chars.append(char if category.startswith(("L", "N")) else " ")
    return "".join(chars).split()


def compare_texts(reference: str, predicted: str) -> dict:
    expected, actual = tokenize(reference), tokenize(predicted)
    if not expected:
        raise ValueError("Reference must contain words")
    if len(expected) > 2000 or len(actual) > 2000:
        raise ValueError("Compare at most 2000 words at a time")
    costs = [list(range(len(actual) + 1))]
    for i, word in enumerate(expected, 1):
        row = [i]
        for j, spoken in enumerate(actual, 1):
            row.append(min(costs[i - 1][j] + 1, row[j - 1] + 1,
                           costs[i - 1][j - 1] + (word != spoken)))
        costs.append(row)
    i, j = len(expected), len(actual)
    alignment = []
    while i or j:
        if i and j and costs[i][j] == costs[i - 1][j - 1] + (expected[i - 1] != actual[j - 1]):
            kind = "equal" if expected[i - 1] == actual[j - 1] else "replace"
            i, j = i - 1, j - 1
            alignment.append(dict(type=kind, reference_index=i, predicted_index=j,
                                  expected=expected[i], predicted=actual[j]))
        elif i and costs[i][j] == costs[i - 1][j] + 1:
            i -= 1
            alignment.append(dict(type="delete", reference_index=i, predicted_index=j,
                                  expected=expected[i], predicted=""))
        else:
            j -= 1
            alignment.append(dict(type="insert", reference_index=i, predicted_index=j,
                                  expected="", predicted=actual[j]))
    alignment.reverse()
    errors = [item for item in alignment if item["type"] != "equal"]
    return {"reference": reference, "transcript": predicted,
            "reference_word_count": len(expected), "word_error_rate": len(errors) / len(expected),
            "errors": errors, "alignment": alignment}
