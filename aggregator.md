# Aggregator Prompt & Plan

## INPUT PROMPT:
I'd like to explore creating an "agent" for doing a specific composite task.
The task would involve the following tasks:
1. Target a specific textual information source, be it a local file system directory/glob, or a Google Docs file/folder, or a website with a specific text pattern for exhaustively searching for articles or posts, other targets could be explored.
2. With the collection of textual sources, assemble the text files into a single file, with chapters, sections, divisions by file/source.
3. Convert this final single file into a mobile format such as .epub or .mobi (or?).
4. The output is this mobile platform file for reading on a phone tablet or kindle.
5. OPTIONALLY: Determine a text-to-speech service (elevenlabs?, other?) that could convert the source file into an audio format suitable for streaming and/or publishing for download.
Please create a plan detailing how I might go about building such an agent.

## OUTPUT PLAN:
Agent Plan: Document Aggregator & Publisher

This is a well-scoped project with clear stages. Here's a realistic architectural plan.
System Overview
  ::view-transition-group(*),
  ::view-transition-old(*),
  ::view-transition-new(*) {
    animation-duration: 0.25s;
    animation-timing-function: cubic-bezier(0.19, 1, 0.22, 1);
  }

The stack, stage by stage
Stage 1 — Source ingestion is where most of the complexity lives. The right tool depends on the source type:

Local files: Python's pathlib with glob patterns. Dead simple.
Google Docs/Drive: Google Drive API v3 with a service account. You authenticate once, then list files in a folder or fetch individual docs as plain text or Markdown via the export endpoint (?mimeType=text/plain).
Websites: httpx + BeautifulSoup or playwright (for JS-heavy sites). You define a URL pattern (e.g. https://example.com/posts/*) and crawl exhaustively. For Substack specifically, their sitemap at /sitemap.xml lists all posts.
Newsletters/RSS: feedparser handles RSS/Atom. For email newsletters, IMAP access via imaplib is surprisingly workable.

Stage 2 — Assembly is the easiest stage technically, but getting the structure right matters for the downstream eBook quality. The key tool is pandoc — it can convert almost anything (HTML, DOCX, RST, plain text) into Markdown. Then you concatenate with a header structure:
# [Source Name]
## [Article Title]
[content]
---
Stage 3 — eBook conversion has two solid paths. pandoc alone handles .epub natively. For Kindle formats, either use Calibre's ebook-convert CLI (installable headlessly on a server) or Amazon's KindleGen (deprecated but still works). For a clean epub, pass a metadata.yaml and a CSS file to pandoc for formatting control.
Stage 4b — TTS (optional) has real options now. ElevenLabs produces the most natural output but has cost per character. OpenAI TTS (tts-1-hd) is cheaper and very good. Both have Python SDKs. The smart approach is to split chapters into chunks, generate per-chapter MP3s, then stitch with pydub. To publish as a podcast, upload MP3s to S3 and generate an RSS feed XML — any podcast app can then subscribe.
Recommended implementation approach
Orchestration: Write it as a Python script with a simple config file (YAML) specifying sources, output path, and format options. For scheduling, a cron job or a simple webhook (Flask app with a /run endpoint) is sufficient — you don't need LangChain or an LLM in the loop unless you want the agent to make decisions (e.g. "summarize this before including it").
Technology choices:

Runtime: Python 3.11+
HTTP: httpx (async-native)
HTML parsing: BeautifulSoup4
Format conversion: pandoc (system binary, called via subprocess)
Google APIs: google-api-python-client
TTS: elevenlabs or openai SDK
Audio stitching: pydub
Scheduling: APScheduler or cron

Project structure to keep it clean:
aggregator/
  config.yaml           # source definitions, output settings
  sources/              # one module per source type
    local_fs.py
    google_drive.py
    web_scraper.py
  pipeline/
    normalize.py        # → markdown
    assemble.py         # → single structured doc
    package.py          # → epub/mobi
    tts.py              # → mp3 chapters
  main.py               # orchestrates the pipeline
What to build first
Start with local filesystem → epub. That path has zero external auth, validates the whole pipeline in an hour, and gives you something to read on day one. Layer in Google Drive next (auth is the annoying part, but it's one-time setup). Add the web scraper last since it requires the most per-site tuning.
The TTS output is genuinely a separate project — worth a second pass once the reading format works well.
