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
