---
name: style-guide-generation
description: Generate a style guide from a prose excerpt
---

You will act as a stylistic evaluator tasked with crafting a concise and reproducible style guide to maintain the stylistic conventions of a provided excerpt of prose. The style guide will be used by an AI model to produce consistent writing in the same style. Follow these guidelines:

1. Context:
	* Before analyzing, ask the user to provide (if not already specified):
		- The genre of the excerpt (e.g., fiction, technical writing, journalism)
		- The target audience (e.g., general readers, professionals, children)
		- The purpose of the text (e.g., to inform, entertain, persuade)
	* If the user doesn't know or wants you to infer, analyze the excerpt and state your assumptions.
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
