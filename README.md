# Tool for Faster Learning

This tool is designed to accelerate learning by using book summaries structured into chapters and subchapters. Users can feed the tool with the structure of a book on any subject. By clicking on a chapter, users can see a "one-shot AI generation" about that chapter in a conversation with the AI. Each message refers to the current conversation flow and thus to the selected chapter. The user mainly seeks to understand the chapter and can ask questions. The AI acts as a learning assistant to explain concepts and answer questions.

## Components

### Database
- Books -> Chapter tree -> Conversation for each leaf of the chapter tree

### Frontend
- Screen with a chapter editor, structured like a tree with nodes and branches. Each node is a string "chapter name" + (short descriptions?). The user manually edits the chapter structure initially.
- Markdown import to extract chapter structure.
- Screen with a breadcrumb of the current chapter and chapter title, + conversation.

### Prompt Engineering
- A prompt for "expanding" a subchapter, the first time the user opens it.
- A prompt for generally chatting with the current chapter of the book (like a conversation seeded with the content + prompt + user question => answer).
