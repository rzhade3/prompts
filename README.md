# Prompts

This repository contains AI prompts I use for common tasks. I primarily use them as [Agent Skills](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills) with [GitHub Copilot CLI](https://docs.github.com/en/copilot/github-copilot-in-the-cli), but they should work with any LLM.

Skills that need additional context (like genre or ticket template) will ask you for this information when invoked.

## Installation as Copilot Agent Skills

Run the install script to add these prompts as [Agent Skills](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills):

```bash
python3 install.py
```

This installs each prompt to `~/.copilot/skills/{skill-name}/SKILL.md`. Copilot automatically loads relevant skills based on their descriptions when performing tasks.

### Available Skills

- **copyediting** - Edit prose for grammar and style
- **daily-dashboard** - Create a prioritized GitHub dashboard
- **prompt-improvement** - Improve AI prompts
- **prose-evaluation** - Evaluate prose for consistency and flow
- **secondhand-goods-research** - Research secondhand goods deals
- **style-guide-generation** - Generate a style guide from prose
- **writeup-github-issues** - Create detailed issue tickets
