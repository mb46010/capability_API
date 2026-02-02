import jinja2
from pathlib import Path

def get_jinja_env(template_dir: str = "scripts/templates") -> jinja2.Environment:
    """
    Get a configured Jinja2 environment.
    """
    template_path = Path(template_dir)
    if not template_path.is_absolute():
        # Try resolving relative to project root
        project_root = Path(__file__).resolve().parent.parent.parent
        template_path = project_root / template_dir
        
    loader = jinja2.FileSystemLoader(str(template_path))
    env = jinja2.Environment(
        loader=loader,
        autoescape=False,  # We are generating YAML/Markdown, not HTML
        trim_blocks=True,
        lstrip_blocks=True
    )
    
    # Add custom filters if needed
    def lower_filter(s):
        return s.lower() if isinstance(s, str) else str(s).lower()
        
    env.filters['lower'] = lower_filter
    
    return env
