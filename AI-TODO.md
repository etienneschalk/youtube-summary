Okay, the user has a README file for their YouTube Summarizer project and wants to restructure the TODO list into GitHub issues. Let me start by understanding the existing TODOs and the project context.

First, looking at the TODO list in the README, there are several tasks listed as checkboxes. Each of these needs to be converted into a GitHub issue. The goal is to organize work into manageable issues that can be tracked and assigned.

I should go through each TODO item and think about how to phrase it as an issue. Each issue should have a clear title and a description that explains the task, possibly with acceptance criteria or additional context from the README.

For example, the first TODO is "Use the retry lib for when the request to the LLM is stuck." This can become an issue about implementing retry logic. The user mentioned using the retry library, so the issue should reference that and maybe suggest using a specific library or implementing custom retries.

Next, "Have a more structured way to track progress and failures." This seems like a task to improve error handling and logging. The issue should mention replacing the hardcoded skip count with a better system.

The third TODO is about a CLI tool to fetch transcripts. The user wants a standalone tool, so the issue should outline creating a command-line interface that allows quick fetching and manual summary generation.

Some TODOs might overlap or can be combined. For instance, "Include timestamp and video id in the summaries" and "Use all input json files as a database..." could be separate but related. It's better to keep them as separate issues for clarity.

The user also wants to connect to Obsidian for automatic ingestion. This would involve integrating with Obsidian's API or file system, which is a distinct feature.

Another point is improving the JavaScript snippet to fetch daily history using cookies. This is about enhancing the existing script, so the issue should detail the need for CSS selectors and session cookie handling.

Language detection for summaries and multi-language processing are related but separate. Detecting the video's language is a prerequisite for generating summaries in the correct language, while multi-language processing might involve generating summaries in both languages or translating them.

Support for Shorts is another feature. Since Shorts have different formats, the issue should address handling their specific URLs or content structures.

Checking the external library for YouTube history export is a research task. The issue would involve evaluating and integrating that library if suitable.

The TODO about using the video's title tag and description extraction is about robustness. The current code might break if YouTube's HTML changes, so the issue would focus on making this part more reliable.

Adding support for a plain text input source is another feature. The issue should allow users to input a list of videos via a text file, which adds flexibility.

Now, considering the user's comment in the README, they mentioned issues with the LLM omitting key points and mangling names. So, there might be an implicit need for issues related to improving the summary accuracy, maybe through better prompts or post-processing.

Also, the user's code is on GitHub, so cross-referencing the repository in the issues could be helpful. They might also need labels like 'enhancement', 'feature', 'bug', etc., but the answer doesn't need to include labels unless specified.

I should ensure each issue is actionable and clear. If a TODO is too vague, like "Improve the javascript snippet," I need to parse the README's context to add specifics, such as using session cookies and CSS selectors.

Finally, the user might benefit from a prioritized list, but since they didn't specify, the order in the answer can follow the original TODO list's sequence, grouping related tasks when appropriate.

So, converting each TODO into an issue with a title and description, using the context provided in the README, including code examples, and references to external libraries or tools mentioned. Each issue should be self-contained but reference related issues if needed.

Here’s a structured list of GitHub issues derived from your TODOs and README context. Each issue is categorized and includes actionable steps:

---

### **Core Functionality**

- [ ] **Issue: Implement Retry Logic for LLM Requests**

  - Add `retry` library to handle stuck LLM API requests.
  - Ensure exponential backoff and error logging.
  - _Related Code_: LLM API call section.

- [ ] **Issue: Improve Progress/Failure Tracking**

  - Replace hardcoded "skip count" with a structured system (e.g., SQLite database or JSON logs).
  - Track failed requests, retries, and successes.

- [ ] **Issue: Create CLI Tool for Manual Transcript Fetching**

  - Build a command-line tool to fetch transcripts via video URL.
  - Allow manual summarization (e.g., `python fetch_transcript.py --url VIDEO_URL`).

- [ ] **Issue: Support YouTube Shorts**
  - Modify transcript fetcher to handle Shorts URLs (e.g., `youtube.com/shorts/...`).
  - Test with example Shorts videos.

---

### **Data Management**

- [ ] **Issue: Use Video IDs as Primary Keys**

  - Treat input JSON files as a database, deduplicating entries using video IDs.
  - Add `video_id` extraction logic from URLs (e.g., `watch?v=ID`).

- [ ] **Issue: Include Timestamp and Video ID in Summaries**

  - Extract timestamps from transcripts.
  - Add `timestamp` and `video_id` fields to summary outputs.

- [ ] **Issue: Add Plain Text Input Support**
  - Allow `.txt` files as input (one video URL per line).
  - Auto-convert text files to JSON for processing.

---

### **Integration & Automation**

- [ ] **Issue: Auto-Ingest Summaries into Obsidian**

  - Connect to Obsidian via API or file system.
  - Save summaries as Markdown files in the vault with proper metadata.

- [ ] **Issue: Enhance JavaScript Snippet for Daily History**

  - Update snippet to filter history by date using CSS selectors.
  - Leverage session cookies for authentication.

- [ ] **Issue: Integrate YouTube History Export Helper**
  - Evaluate [`youtube-watch-history-to-csv`](https://github.com/menggatot/youtube-watch-history-to-csv) for bulk history processing.
  - Add support for CSV/JSON exports.

---

### **Localization & Accuracy**

- [ ] **Issue: Auto-Detect Video Language**

  - Use LLM or transcript analysis to detect video language.
  - Generate summaries in the detected language (French/English).

- [ ] **Issue: Add Multi-Language Summaries/Translations**

  - Allow generating summaries in both French and English.
  - Add translation prompts (e.g., "Translate this summary to French").

- [ ] **Issue: Improve Name/Key Point Accuracy**
  - Add prompt instructions to preserve names and opposition viewpoints.
  - Validate summaries against manual checks.

---

### **Robustness & Maintenance**

- [ ] **Issue: Extract Titles/Descriptions from YouTube HTML**

  - Use `BeautifulSoup` or `yt-dlp` to fetch video metadata.
  - Fallback to HTML parsing if API fails.

- [ ] **Issue: Handle Transcript Edge Cases**
  - Test auto-generated vs. manual subtitles.
  - Add error handling for missing/partial transcripts.

---

### **Documentation & Testing**

- [ ] **Issue: Write Unit Tests for Core Features**

  - Test transcript fetching, summarization, and error handling.

- [ ] **Issue: Update README with Usage Examples**
  - Add CLI instructions, JSON input formats, and Obsidian setup steps.

---

**Next Steps**:

- Prioritize issues (e.g., start with **Retry Logic** and **CLI Tool**).
- Use labels like `enhancement`, `bug`, and `documentation`.
- Link related issues (e.g., _Multi-Language Summaries_ depends on _Auto-Detect Language_).

Would you like me to draft a specific issue description for any of these?

---

undefined: https://labs.perplexity.ai/?utm_source=copy_output
