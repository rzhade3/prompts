#!/usr/bin/env python3
"""Install prompts as GitHub Copilot CLI skills.

Skills are installed following the Agent Skills standard:
https://docs.github.com/en/copilot/concepts/agents/about-agent-skills

Each skill is installed as a subdirectory containing a SKILL.md file with
YAML frontmatter (name, description) and markdown instructions.
"""

import argparse
import re
from pathlib import Path


def install_skills(dest_dir: Path | None = None, force: bool = False) -> None:
    """Copy prompts to Copilot skills directory as SKILL.md files.
    
    Each prompt is installed as:
        ~/.copilot/skills/{skill-name}/SKILL.md
    
    The SKILL.md file includes YAML frontmatter with name and description.
    """
    script_dir = Path(__file__).parent.resolve()
    prompts_dir = script_dir / "prompts"
    
    if dest_dir is None:
        dest_dir = Path.home() / ".copilot" / "skills"
    
    dest_dir.mkdir(parents=True, exist_ok=True)
    print(f"Installing Copilot skills to {dest_dir}...")
    
    installed = 0
    skipped = 0
    for prompt_file in sorted(prompts_dir.glob("*.md")):
        content = prompt_file.read_text(encoding="utf-8")
        skill_name = _get_name_from_frontmatter(content)
        if not skill_name:
            print(f"  ⚠️  {prompt_file.name} has no 'name' in frontmatter, skipping")
            continue
        
        skill_dir = dest_dir / skill_name
        skill_dir.mkdir(parents=True, exist_ok=True)
        dest_file = skill_dir / "SKILL.md"
        
        if dest_file.exists() and not force:
            print(f"  ⏭ {skill_name}/SKILL.md (exists, use --force to overwrite)")
            skipped += 1
            continue
        
        dest_file.write_text(content, encoding="utf-8")
        print(f"  → {skill_name}/SKILL.md")
        installed += 1
    
    print(f"\n✅ Installed {installed} skills to {dest_dir}")
    if skipped:
        print(f"⚠️  Skipped {skipped} existing skills (use --force to overwrite)")
    print("\nCopilot will automatically load relevant skills when needed.")


def _get_name_from_frontmatter(content: str) -> str | None:
    """Extract 'name' field from YAML frontmatter."""
    frontmatter_pattern = re.compile(r"^---\n(.*?)\n---", re.DOTALL)
    match = frontmatter_pattern.match(content)
    if not match:
        return None
    
    frontmatter = match.group(1)
    name_match = re.search(r"^name:\s*(.+)$", frontmatter, re.MULTILINE)
    if not name_match:
        return None
    
    name = name_match.group(1).strip()
    name = re.sub(r"\s*#.*$", "", name)  # Remove comments
    name = name.strip("\"'")  # Remove quotes
    name = name.replace(" ", "-")  # Replace spaces with hyphens
    return name or None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Install prompts as GitHub Copilot CLI skills.")
    parser.add_argument("--force", "-f", action="store_true", help="Overwrite existing skill files")
    args = parser.parse_args()
    install_skills(force=args.force)
