from datetime import datetime
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from src.domain.services.policy_verifier import VerificationReport

class PolicyReportGenerator:
    def __init__(self):
        template_dir = Path(__file__).parent / "templates"
        self.jinja_env = Environment(loader=FileSystemLoader(str(template_dir)))
        self.template = self.jinja_env.get_template("policy_report.html")

    def generate_html(self, report: VerificationReport) -> str:
        """Generate HTML report string."""
        return self.template.render(
            report=report,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

    def write_report(self, report: VerificationReport, output_path: str):
        """Write HTML report to file."""
        html = self.generate_html(report)
        with open(output_path, "w") as f:
            f.write(html)
