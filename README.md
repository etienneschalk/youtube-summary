# Youtube Summarizer

## Summarize my YouTube history

Summarizing the history is a variant of summarizing a list of videos

Login and go to your [YouTube History](https://www.youtube.com/feed/history)

Open the console in the developers tools (F12) and run the following:

```javascript
JSON.stringify(
  Array.from(document.querySelectorAll("[id='video-title']"))
    .map((a) => ({ title: a.title, href: a.href }))
    .filter((a) => a.href)
);
```

Same but with pretty output:

```javascript
JSON.stringify(
  Array.from(document.querySelectorAll("[id='video-title']"))
    .map((a) => ({ title: a.title, href: a.href }))
    .filter((a) => a.href),
  null,
  4
);
```

Example output (3 elements, the actual length of the list for this example was 161)

```json
[
  {
    "title": "Une histoire de la guerre économique (2019) | ARTE",
    "href": "https://www.youtube.com/watch?v=7__pNSLVgsU"
  },
  {
    "title": "JE LIS 📚 au lieu de SCROLLER sur les réseaux sociaux",
    "href": "https://www.youtube.com/watch?v=WbWsiaEfWIo&t=105s"
  },
  {
    "title": "Comment nous sommes devenus si seuls",
    "href": "https://www.youtube.com/watch?v=88KJwEu5TRs&t=4s"
  }
]
```

Copy the output in a JSON file.

## TODO

- [ ] Use the retry lib for when the request to the LLM is stuck
- [ ] Have a more structured way to track progress and failures (currently, a hardcoded "skip count" is very low-tech...)
- [ ] Independant command line tool to quickly fetch a transcript (sometimes it is good to just copy paste and generate the summary manually)
- [ ] Connect to Obsidian to ingest automatically summaries into th eVault
- [ ] Improve the javascript snippet to only fetch the daily history with some CSS selector magic and use the session cookie from youtube.
- [ ] Include timestamp and video id in the summaries
- [ ] Make english summaries for english videos and french summaries for french videos (needs to detect the native lang of the video)
- [ ] Use all input json files as a database, using video IDs as primary key
- [ ] Add multi-language processing (eg, I want to generate everything twice, in french and english. Or add a translation prompt from french to english and vice-versa)
- [ ] Support Shorts
