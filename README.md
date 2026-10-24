# Short-Projects

The main intention of this repository is to store some of the short projects that I work by learning from others. Each folder is one project — mostly hands-on notebooks from [deeplearning.ai](https://www.deeplearning.ai) short courses, plus a few original tools and experiments.

## 1. Build Systems using ChatGPT

This is a project that I have learnt from [deeplearning.ai](https://www.deeplearning.ai) course ["Build System with the ChatGPT API"](https://www.deeplearning.ai/short-courses/building-systems-with-chatgpt/)<br>
It's a great start to learn on how to use OpenAI APIs. One notebook per lesson (L1–L9), covering classification and moderation of inputs, chain-of-thought reasoning, chaining prompts, output checks, an end-to-end customer service example, and evaluating model outputs.

#### Credits
It was taught by [Andrew Ng](https://www.andrewng.org) and [Isha Fulford](https://www.coursera.org/instructor/~137229549) who collaborated with [deeplearning.ai](https://www.deeplearning.ai) to create the "Build System with the ChatGPT API" course.<br> and all credits goes to them.

## 2. Prompt Engineering using ChatGPT

This is a project that I have learnt from [deeplearning.ai](https://www.deeplearning.ai) course ["ChatGPT Prompte Engineering for Developers"](https://learn.deeplearning.ai/courses/chatgpt-prompt-eng/lesson/4/summarizing/)<br>
It's a great start to learn on how to work with Prompts using OpenAI APIs. One notebook per lesson (L2–L8), covering guidelines, iterative prompt development, summarizing, inferring, transforming, expanding, and building a chatbot.

#### Credits
It was taught by [Andrew Ng](https://www.andrewng.org) and [Isha Fulford](https://www.coursera.org/instructor/~137229549) who collaborated with [deeplearning.ai](https://www.deeplearning.ai) to create the "ChatGPT Prompte Engineering for Developers" course.<br> and all credits goes to them.

## 3. Generative AI with LLMs (using AWS)

This is a project that I have learnt from [deeplearning.ai](https://www.deeplearning.ai) course in collaboration with AWS ["Generative AI with LLMs"](https://www.deeplearning.ai/courses/generative-ai-with-llms/) <br>
Its a great start to learn Generative AI with good examples using AWS environment. Contains the labs worked on: Lab 1 (dialogue summarization) and Lab 2 (fine-tuning a generative AI model, initial version).

#### Credits
It was taught by [Antje Barth](https://www.linkedin.com/in/antje-barth/), [Chris Fregly](https://www.linkedin.com/in/cfregly/), [Shelbee Eigenbrode](https://www.linkedin.com/in/shelbee-eigenbrode/), [Mike Chambers](https://www.linkedin.com/in/mikegchambers/) who collaborated with [deeplearning.ai](https://www.deeplearning.ai) to create the "Generative AI with LLMs" course in collaboration with AWS.

## 4. Tic Tac Toe with Minimax AI
   - A Python-based Tic Tac Toe game featuring an unbeatable AI opponent
   - Implemented using the Minimax algorithm
   - Includes comprehensive unit testing
#### Credits
   Developed by Codeium Cascade AI - [https://www.codeium.com](https://www.codeium.com)

## 5. LangChain for LLM Application Development

This is a project that I have learnt from [deeplearning.ai](https://www.deeplearning.ai) course ["LangChain for LLM Application Development"](https://learn.deeplearning.ai/courses/langchain/lesson/1/introduction)<br>
It helps to understand the concepts with examples of powerful and extensible LangChain framework, using prompts, parsing, memory, chains, question answering, and agents. One notebook per lesson (L1–L6), plus course screenshots.

#### Credits
It was taught by [Andrew Ng](https://www.andrewng.org) and [Harrison Chase](https://www.linkedin.com/in/harrison-chase-961287118/) who collaborated with [deeplearning.ai](https://www.deeplearning.ai)

## 6. LangChain Chat with your Data

This is a project that I have learnt from [deeplearning.ai](https://www.deeplearning.ai) course ["LangChain: Chat with Your Data"](https://www.deeplearning.ai/short-courses/langchain-chat-with-your-data/)<br>
Covers how to build a chatbot that answers questions about your own documents — document loading, splitting, vectorstores and embeddings, retrieval, question answering, and the final chat interface. One notebook per lesson.

#### Credits
It was taught by [Harrison Chase](https://www.linkedin.com/in/harrison-chase-961287118/) in collaboration with [deeplearning.ai](https://www.deeplearning.ai)

## 7. Building Adaptive AI Agents

This is a project that I have learnt from [deeplearning.ai](https://www.deeplearning.ai) course ["Building Adaptive AI Agents"](https://www.deeplearning.ai/courses/building-adaptive-ai-agents) <br>
It helps to understand the concept of adaptive agents both token based and weight based (1) updating skills based on traces and learnings (2) building code graph base knowledge for better retrival (3) weight adjsustments. but this sample folder contains only (1) (2) both are token based optimization — re-implemented locally with SQLite, NetworkX and scikit-learn.

#### Credits
It was taught by [Nacho Martínez](https://www.linkedin.com/in/jasperan/) and [Casius Lee](https://www.linkedin.com/in/casiusslee/) in collaboration with [deeplearning.ai](https://www.deeplearning.ai)

## 8. Building with Claude API

A hands-on Python project (uv-managed, `src/` layout) exploring the Anthropic Claude API. Covers simple and streaming API requests, structured output, prompt engineering exercises, prompt evaluations with generated datasets and running model evals, tool use (including in-built web search and text editor tools), RAG with semantic / BM25 / hybrid retrieval, extended thinking, and image and PDF features — plus smaller side experiments (`mcp_project`, `lab_chroma`, `educative_examples`, `app_starter`).

## 9. MCP: Build Rich Context AI Apps

This is a project that I have learnt from [deeplearning.ai](https://www.deeplearning.ai) course ["MCP: Build Rich Context AI Apps"](https://www.deeplearning.ai/short-courses/mcp-build-rich-context-ai-apps/)<br>
Learns the Model Context Protocol (MCP) — creating MCP servers and clients, connecting a chatbot to reference servers, adding prompt and resource features, and creating and deploying remote servers. One notebook per lesson (L3–L9) plus an appendix.

#### Credits
It was taught by [W. Isaac J. Singer](https://www.linkedin.com/in/wj-singer/) in collaboration with [deeplearning.ai](https://www.deeplearning.ai)

## 10. NewsLetter Distiller

An original Python 3.12+ CLI built and run exclusively with `uv`. Given a newsletter URL it fetches the page, strips boilerplate, extracts article text and image candidates, and sends them to a pluggable LLM backend (Anthropic or any OpenAI-compatible endpoint such as Ollama / DeepSeek) which decides which images are real charts vs. ads and writes a Markdown digest with local image files under `output/<slug>/`. Configuration via environment variables, with a full mocked pytest suite.

## 11. PlayWright Learning

This is a project that I have learnt from Claude to work with Playwright type-scripts. A day-by-day journal where each `Day-N` folder is a standalone Playwright project: Day-1 basics, Day-2 Page Object Model and auth, Day-3 advanced UI (iframes, uploads, network mocking), Day-4 API testing, and Day-8 Claude Code integration with Playwright Test Agents and the Playwright MCP server.

## 12. Youtube Transcript Fetcher

An original Python tool that turns any YouTube video into a Markdown study guide. Uses `yt-dlp` and `youtube-transcript-api` to fetch the transcript and chapters, then makes one Claude API call per chapter to generate enriched study notes (analogies, worked examples, Mermaid diagrams, real reference links via Claude's `web_search` tool) assembled into `ClaudeOutput/<Video Title>.md`. Modular codebase with a mocked pytest suite.

## 13. utils

A small helper script, `download_url_files.py`, that recursively downloads files and subfolders from a given URL.