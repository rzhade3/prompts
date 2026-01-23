# Prompts

This repository contains many of the AI prompts that I use for common tasks. I use them primarily with OpenAI's GPT4o model, but they should work with any GPT model.

Some of these system prompts will require some customization to work with your specific use case. Skills that need additional context (like genre or ticket template) will ask you for this information when invoked.

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
