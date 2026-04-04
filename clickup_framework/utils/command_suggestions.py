"""Helpers for suggesting likely CLI commands from mistyped input."""

from dataclasses import dataclass
from typing import Iterable, Mapping


COMMON_COMMAND_MISTAKES = {
    "serch": "search",
    "srch": "search",
    "tsk": "task",
    "tk": "task_create",
}


@dataclass(frozen=True)
class SuggestionChoice:
    """A canonical command choice plus its aliases."""

    canonical: str
    aliases: tuple[str, ...] = ()

    @property
    def all_tokens(self) -> tuple[str, ...]:
        """Return canonical plus alias tokens for matching."""
        return (self.canonical, *self.aliases)

    @property
    def invocation_token(self) -> str:
        """Return the token users should type for the suggestion."""
        if self.aliases and len(self.canonical) > 8:
            return sorted(self.aliases, key=lambda value: (len(value), value))[0]
        return self.canonical

    @property
    def annotation(self) -> str | None:
        """Return optional explanatory text for the suggestion."""
        if self.invocation_token != self.canonical:
            return self.canonical
        return None


def _normalize_token(value: str) -> str:
    """Normalize a token for similarity matching."""
    return value.lower().replace("-", "").replace("_", "")


def levenshtein_distance(left: str, right: str) -> int:
    """Compute Levenshtein edit distance between two strings."""
    if left == right:
        return 0
    if not left:
        return len(right)
    if not right:
        return len(left)

    previous = list(range(len(right) + 1))
    for i, left_char in enumerate(left, start=1):
        current = [i]
        for j, right_char in enumerate(right, start=1):
            insertion = current[j - 1] + 1
            deletion = previous[j] + 1
            substitution = previous[j - 1] + (left_char != right_char)
            current.append(min(insertion, deletion, substitution))
        previous = current
    return previous[-1]


def suggest_command_choices(
    user_input: str,
    choices: Iterable[SuggestionChoice],
    *,
    max_suggestions: int = 3,
    common_mistakes: Mapping[str, str] | None = None,
) -> list[SuggestionChoice]:
    """Return the most plausible command choices for a mistyped token."""
    normalized_input = _normalize_token(user_input)
    available = list(choices)
    common_mistakes = common_mistakes or COMMON_COMMAND_MISTAKES

    common_target = common_mistakes.get(normalized_input)
    if common_target:
        normalized_target = _normalize_token(common_target)
        for choice in available:
            if any(_normalize_token(token) == normalized_target for token in choice.all_tokens):
                return [choice]

    if not normalized_input:
        return []

    threshold = 1 if len(normalized_input) <= 3 else 2 if len(normalized_input) <= 6 else 3
    ranked = []

    for choice in available:
        normalized_tokens = [_normalize_token(token) for token in choice.all_tokens]
        distances = [levenshtein_distance(normalized_input, token) for token in normalized_tokens]
        best_distance = min(distances)
        contains = any(
            normalized_input in token or token in normalized_input
            for token in normalized_tokens
        )
        if best_distance > threshold and not contains:
            continue

        min_length_delta = min(abs(len(normalized_input) - len(token)) for token in normalized_tokens)
        same_initial = any(token[:1] == normalized_input[:1] for token in normalized_tokens)
        ranked.append(
            (
                best_distance,
                0 if same_initial else 1,
                min_length_delta,
                len(choice.canonical),
                choice.canonical,
                choice,
            )
        )

    ranked.sort()
    return [entry[-1] for entry in ranked[:max_suggestions]]
