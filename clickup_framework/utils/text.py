"""
Text Utilities

Helper functions for text formatting and manipulation.
"""

import re
from typing import List, Optional


def truncate(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum length (default: 100)
        suffix: Suffix to add if truncated (default: "...")

    Returns:
        Truncated text

    Examples:
        >>> truncate("This is a long text", 10)
        'This is...'
    """
    if not text or len(text) <= max_length:
        return text

    return text[: max_length - len(suffix)] + suffix


def format_list(items: List[str], max_items: int = 5, separator: str = ", ") -> str:
    """
    Format list of items with optional truncation.

    Args:
        items: List of items to format
        max_items: Maximum items to show (default: 5)
        separator: Separator between items (default: ", ")

    Returns:
        Formatted string

    Examples:
        >>> format_list(["a", "b", "c"])
        'a, b, c'
        >>> format_list(["a", "b", "c", "d", "e", "f"], max_items=3)
        'a, b, c, +3 more'
    """
    if not items:
        return "None"

    if len(items) <= max_items:
        return separator.join(items)

    shown = items[:max_items]
    remaining = len(items) - max_items
    return f"{separator.join(shown)}, +{remaining} more"


def pluralize(count: int, singular: str, plural: Optional[str] = None) -> str:
    """
    Pluralize word based on count.

    Args:
        count: Number of items
        singular: Singular form
        plural: Plural form (defaults to singular + 's')

    Returns:
        Pluralized string with count

    Examples:
        >>> pluralize(1, "task")
        '1 task'
        >>> pluralize(5, "task")
        '5 tasks'
        >>> pluralize(2, "box", "boxes")
        '2 boxes'
    """
    if plural is None:
        plural = singular + "s"

    word = singular if count == 1 else plural
    return f"{count} {word}"


def clean_html(text: str) -> str:
    """
    Remove HTML tags from text.

    Args:
        text: HTML text

    Returns:
        Plain text

    Examples:
        >>> clean_html("<p>Hello <b>world</b></p>")
        'Hello world'
    """
    if not text:
        return ""

    # Simple HTML tag removal (not perfect but works for basic cases)
    import re

    # Remove tags
    text = re.sub(r"<[^>]+>", "", text)

    # Decode common HTML entities
    text = text.replace("&nbsp;", " ")
    text = text.replace("&lt;", "<")
    text = text.replace("&gt;", ">")
    text = text.replace("&amp;", "&")
    text = text.replace("&quot;", '"')
    text = text.replace("&#39;", "'")

    # Clean up whitespace
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def strip_markdown(text: str) -> str:
    """
    Remove markdown formatting from text.

    Args:
        text: Markdown text

    Returns:
        Plain text with markdown syntax removed

    Examples:
        >>> strip_markdown("**bold** and *italic*")
        'bold and italic'
        >>> strip_markdown("# Header\\nSome text")
        'Header\\nSome text'
    """
    if not text:
        return ""

    # Remove headers
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)

    # Remove bold (**text** or __text__)
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'__(.+?)__', r'\1', text)

    # Remove italic (*text* or _text_)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'_(.+?)_', r'\1', text)

    # Remove strikethrough (~~text~~)
    text = re.sub(r'~~(.+?)~~', r'\1', text)

    # Remove inline code (`text`)
    text = re.sub(r'`(.+?)`', r'\1', text)

    # Remove code blocks (```text```)
    text = re.sub(r'```[\s\S]*?```', '', text)

    # Remove links [text](url)
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)

    # Remove images ![alt](url)
    text = re.sub(r'!\[([^\]]*)\]\([^\)]+\)', r'\1', text)

    # Remove bullet points
    text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)

    # Remove numbered lists
    text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)

    # Remove blockquotes
    text = re.sub(r'^\s*>\s+', '', text, flags=re.MULTILINE)

    # Remove horizontal rules
    text = re.sub(r'^[\s-]{3,}$', '', text, flags=re.MULTILINE)

    return text.strip()


def indent(text: str, level: int = 1, char: str = "  ") -> str:
    """
    Indent text by specified level.

    Args:
        text: Text to indent
        level: Indentation level (default: 1)
        char: Indentation character (default: 2 spaces)

    Returns:
        Indented text

    Examples:
        >>> indent("Hello", 2)
        '    Hello'
    """
    prefix = char * level
    lines = text.split("\n")
    return "\n".join(prefix + line for line in lines)


def format_user_list(users: List[dict], max_users: int = 5) -> str:
    """
    Format list of user objects to names.

    Args:
        users: List of user dictionaries with 'username' key
        max_users: Maximum users to show

    Returns:
        Formatted user names

    Examples:
        >>> format_user_list([{"username": "John"}, {"username": "Jane"}])
        'John, Jane'
    """
    if not users:
        return "None"

    names = [user.get("username", "Unknown") for user in users]
    return format_list(names, max_items=max_users)
