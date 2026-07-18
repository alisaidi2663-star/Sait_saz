"""Shared HTML generation utilities to reduce template duplication."""

import html as html_module


def list_to_html(items):
    """Convert a list of strings to an HTML unordered list.

    Returns empty string if items is empty.
    """
    if not items:
        return ""
    escaped = [f"  <li>{html_module.escape(item)}</li>" for item in items]
    return "<ul>\n" + "\n".join(escaped) + "\n</ul>\n"


def build_section_html(section_id, title, content_html):
    """Generate a standard card section with the given id, title, and inner HTML.

    This pattern was duplicated for about/services/orders sections.
    """
    return f"""
        <section id="{section_id}" class="card">
            <h2>{html_module.escape(title)}</h2>
            {content_html}
        </section>
        """


def hex_to_rgb(hex_color):
    """Convert a hex color string (#RRGGBB) to 'R, G, B' string.

    Returns '0, 149, 255' as fallback on parse failure.
    """
    try:
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
        return f"{r}, {g}, {b}"
    except (ValueError, IndexError):
        return "0, 149, 255"
