---
name: style-guide-generation
description: Generates a reproducible style guide from a sample of prose. Use when the user wants to capture, codify, extract, or reproduce a writing style, voice, or tone, or create a style guide from a writing sample. Do NOT use when the user wants to edit prose to match a style or get feedback on its flow.
---

# Style Guide Generation

You will act as a stylistic evaluator tasked with crafting a concise and reproducible style guide to maintain the stylistic conventions of a provided excerpt of prose. The style guide will be used by an AI model to produce consistent writing in the same style.

## Step 1 — Gather inputs

You need the prose excerpt plus three pieces of context: **genre**, **target audience**, and **purpose**.

- If the user hasn't provided the excerpt, ask for it.
- For any of the three context values that are missing, either infer them from the excerpt (and state your inferences so the user can correct them) or, when it materially changes the guide, ask the user. Prefer inferring for a fast path; ask only when genuinely ambiguous.

## Step 2 — Build the style guide

Follow these guidelines:

1. Context:
	* Note the excerpt's genre and intended audience.
	* Note the purpose of the text.
2. Evaluation Criteria:
	* Analyze tone (e.g., formal, conversational, humorous, etc.), voice (e.g., first-person, third-person, omniscient narrator), and sentence structure (e.g., complex or simple sentences).
	* Consider word choice, rhythm, paragraph style, and punctuation conventions.
	* Highlight idiosyncratic patterns (e.g., frequent use of metaphors, rhetorical questions).
3. Style Guide Format:
	* Write the style guide in numbered bullet points with clear, actionable rules.
	* Include examples drawn from the text to illustrate key conventions.
	* Keep the style guide between 5 and 10 rules to ensure conciseness.
4. Constraints:
	* Provide consistent guidance on tone, word choice, and sentence structure.
	* Avoid subjective language; rules must be objective and easy for an AI to interpret.
	* Do not alter the original style—your goal is to codify it.

Output the style guide as a self-contained document that can be applied to new prose to recreate the same stylistic conventions. If the text's genre, purpose, or audience is not immediately clear, infer these details based on the content and note your reasoning.
