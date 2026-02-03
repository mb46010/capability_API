"""Custom format for mermaid diagrams in pymdownx.superfences."""

def mermaid_format(source, language, css_class, options, md, **kwargs):
    """Format mermaid code blocks without nested code tags.

    This creates <pre class="mermaid"> directly without <code> tag,
    which is what the mermaid.js library expects.
    """
    return f'<pre class="{css_class}">{source}</pre>'
