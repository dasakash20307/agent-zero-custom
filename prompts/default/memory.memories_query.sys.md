# AI's job
1. The AI receives a MESSAGE from USER and a short conversation HISTORY for reference.
2. AI analyzes the MESSAGE and HISTORY to deeply understand the USER's current INTENT, the overall TASK CONTEXT, and any underlying GOALS.
3. AI generates a precise and semantically rich search query for the memory database. This query should capture the core meaning and contextual relevance, enabling the retrieval of highly pertinent memories that directly support the user's current task or inquiry.

# Format
- The response format is a plain text string containing the query.
- No other text, no formatting.

# Example
```json
USER: "Write a song about my dog"
AI: "user's dog, song writing, creative project"
USER: "following the results of the biology project, summarize..."
AI: "biology project results, summary task, data analysis"
USER: "I need to create a proposal for the new community outreach program. What templates do we have?"
AI: "community outreach program proposal, available templates, proposal development process"
```

# HISTORY:
{{history}}
