Tool for faster knowledge learning ;
Essentially it is fed with the summary of a book, structured like chaptering & subchaptering,
and user use the tool, fed it with a chaptering of a book about what ever subject,
the user can click on any chapter and see a "one shot generation by AI about the chapter" , in a chat conversation with ai,
any message given from now on refer to the current conversation flow and therefore to the selected chapter,
User is mainly trying to understand the chapter and can ask question ,
Ai is acting as a learning assistant to explain concept, answer question etc...
Components ,
Database :
Books -> Chaptering tree -> conversation for each leaf of the chaptering tree
Front end :
Screen with the chaptering editor, like a tree with + node + branch, each node is a string "chapter name" + ( short descriptions ?) , user edit the chaptering manually to start with,
Importing markdown seems achievable to extract chaptering out of it,
Screen with a bread crumb of the current chaptering and chapter title, + conversation .
( NOT )Screen with a chaptering view only and details about what conversation "hang" for each chapter
Prompt engineering :
A prompt for "expanding" a subchapter, first time user opens it
A prompt for generally chatting with the current chapter of the book, (like a conversation seeded with the content + prompt + user question => answer )