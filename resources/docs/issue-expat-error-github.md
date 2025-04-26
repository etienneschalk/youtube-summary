<!-- DO NOT DELETE THIS! Please take the time to fill this out properly. I am not able to help you if I do not know what you are executing and what error messages you are getting. If you are having problems with a specific video make sure to **include the video id**. -->

# To Reproduce

For context, I am trying to automatically fetch transcripts for a given input list of video urls.

This bug is not reproducible consistently as it only appears after having queried transcripts for many videos (sometimes a few hundreds, sometimes a few thousands).

However, when fetching transcripts for the input list of video urls, this bug is systematically
the cause of failure of my script, so I can qualify it as a "natural outcome of querying many video transcripts".

I suspect that my requests are blocked, but the error is obscure and not meaningful and results in a raw stacktrace.

### What code / cli command are you executing?

The function `get_youtube_transcript_internal` returns a `Transcript` (not yet fetched). I then call `.fetch()` on the returned `Transcript`. There is a small mechanism to automatically translate to the first available preferred language in case of the unavailability of an already existing transcript in any of the preferred languages.

```python

def get_youtube_transcript_internal(
    video_id: str,
    preferred_languages: tuple[str, ...] | str,
) -> Transcript:
    ytt_api = YouTubeTranscriptApi()
    transcript_list = ytt_api.list(video_id)
    try:
        result = transcript_list.find_transcript(preferred_languages)
        return result
    except YouTubeTranscriptApiException:
        first_available_transcript = next(iter(transcript_list))
        print(first_available_transcript.language_code)
        available_translation_languages_codes = set(
            t.language_code for t in first_available_transcript.translation_languages
        )
        for preferred_language in preferred_languages:
            if preferred_language in available_translation_languages_codes:
                translated_transcript = first_available_transcript.translate(
                    preferred_language
                )
                result = translated_transcript
                print(
                    f"Translated transcript from {first_available_transcript.language_code} to {preferred_language}."
                )
                return result
        raise
```

So I use `.list`, then `.find_transcription`, and potentially `translate`.

### Which Python version are you using?

```python
python --version
Python 3.13.2
```

### Which version of youtube-transcript-api are you using?

```toml
[[package]]
name = "youtube-transcript-api"
version = "1.0.3"
```

# Expected behavior

Describe what you expected to happen: I expect that if my requests get blocked by youtube (in the case this is the root cause of the error), then `youtube_transcript_api` prints a meaningful error message clearly stating that the request failed for being blocked, instead of the low-level "ExpatError".

Note that I only suspect this root cause because of the bug occuring after many runs. I may be wrong it the cause might be something else. In all case, the error seems to come from an unexpected response from youtube. But maybe, the response contains a meaningful error message, in that case it should be relayed by `youtube_transcript_api`.

# Actual behaviour

Describe what is happening instead of the **Expected behavior**. Add **error messages** if there are any.

For example: Instead I received the following error message:

<details><summary> FULL STACKTRACE </summary>

```python
---------------------------------------------------------------------------
ExpatError                                Traceback (most recent call last)
File ~/.pyenv/versions/3.13.2/lib/python3.13/xml/etree/ElementTree.py:1720, in XMLParser.close(self)
   1719 try:
-> 1720     self.parser.Parse(b"", True) # end of data
   1721 except self._error as v:

ExpatError: no element found: line 1, column 0

During handling of the above exception, another exception occurred:

ParseError                                Traceback (most recent call last)
    [... skipping hidden 1 frame]

Cell In[3], line 7
      6 db = db.refresh()
----> 7 db.fetch_missing_transcripts()

File ~/dev/ai-xp/ai_xp/database.py:189, in FileDatabase.fetch_missing_transcripts(self, sleep_seconds)
    188 title = str(missing_transcripts.loc[video_id]["title"])
--> 189 self.fetch_one_transcript(video_id, title)
    190 print(f"Sleep for {sleep_seconds} seconds...")

File ~/dev/ai-xp/ai_xp/database.py:195, in FileDatabase.fetch_one_transcript(self, video_id, title)
    194 video_url = render_video_url(video_id)
--> 195 result = get_youtube_transcript(video_url, preferred_languages=("fr", "en"))
    196 title_slug = render_title_slug(title)

File ~/dev/ai-xp/ai_xp/transcript.py:148, in get_youtube_transcript(video_url, preferred_languages)
    144 try:
    145     # Try preferred language. If the language is not available this will fail.
    146     transcript = get_youtube_transcript_internal(
    147         video_id, preferred_languages
--> 148     ).fetch()
    149     return TranscriptSuccessResult(transcript=transcript)

File ~/.cache/pypoetry/virtualenvs/ai-xp-QtXkVPyw-py3.13/lib/python3.13/site-packages/youtube_transcript_api/_transcripts.py:134, in Transcript.fetch(self, preserve_formatting)
    133 response = self._http_client.get(self._url)
--> 134 snippets = _TranscriptParser(preserve_formatting=preserve_formatting).parse(
    135     _raise_http_errors(response, self.video_id).text,
    136 )
    137 return FetchedTranscript(
    138     snippets=snippets,
    139     video_id=self.video_id,
   (...)    142     is_generated=self.is_generated,
    143 )

File ~/.cache/pypoetry/virtualenvs/ai-xp-QtXkVPyw-py3.13/lib/python3.13/site-packages/youtube_transcript_api/_transcripts.py:474, in _TranscriptParser.parse(self, raw_data)
    467 def parse(self, raw_data: str) -> List[FetchedTranscriptSnippet]:
    468     return [
    469         FetchedTranscriptSnippet(
    470             text=re.sub(self._html_regex, "", unescape(xml_element.text)),
    471             start=float(xml_element.attrib["start"]),
    472             duration=float(xml_element.attrib.get("dur", "0.0")),
    473         )
--> 474         for xml_element in ElementTree.fromstring(raw_data)
    475         if xml_element.text is not None
    476     ]

File ~/.cache/pypoetry/virtualenvs/ai-xp-QtXkVPyw-py3.13/lib/python3.13/site-packages/defusedxml/common.py:127, in _generate_etree_functions.<locals>.fromstring(text, forbid_dtd, forbid_entities, forbid_external)
    126 parser.feed(text)
--> 127 return parser.close()

File ~/.pyenv/versions/3.13.2/lib/python3.13/xml/etree/ElementTree.py:1722, in XMLParser.close(self)
   1721 except self._error as v:
-> 1722     self._raiseerror(v)
   1723 try:

File ~/.pyenv/versions/3.13.2/lib/python3.13/xml/etree/ElementTree.py:1622, in XMLParser._raiseerror(self, value)
   1621 err.position = value.lineno, value.offset
-> 1622 raise err

ParseError: no element found: line 1, column 0 (<string>)

During handling of the above exception, another exception occurred:

TypeError                                 Traceback (most recent call last)
    [... skipping hidden 1 frame]

File ~/.cache/pypoetry/virtualenvs/ai-xp-QtXkVPyw-py3.13/lib/python3.13/site-packages/IPython/core/interactiveshell.py:2143, in InteractiveShell.showtraceback(self, exc_tuple, filename, tb_offset, exception_only, running_compiled_code)
   2138     return
   2140 if issubclass(etype, SyntaxError):
   2141     # Though this won't be called by syntax errors in the input
   2142     # line, there may be SyntaxError cases with imported code.
-> 2143     self.showsyntaxerror(filename, running_compiled_code)
   2144 elif etype is UsageError:
   2145     self.show_usage_error(value)

File ~/.cache/pypoetry/virtualenvs/ai-xp-QtXkVPyw-py3.13/lib/python3.13/site-packages/IPython/core/interactiveshell.py:2231, in InteractiveShell.showsyntaxerror(self, filename, running_compiled_code)
   2229 # If the error occurred when executing compiled code, we should provide full stacktrace.
   2230 elist = traceback.extract_tb(last_traceback) if running_compiled_code else []
-> 2231 stb = self.SyntaxTB.structured_traceback(etype, value, elist)
   2232 self._showtraceback(etype, value, stb)

File ~/.cache/pypoetry/virtualenvs/ai-xp-QtXkVPyw-py3.13/lib/python3.13/site-packages/IPython/core/ultratb.py:1240, in SyntaxTB.structured_traceback(self, etype, evalue, etb, tb_offset, context)
   1238         value.text = newtext
   1239 self.last_syntax_error = value
-> 1240 return super(SyntaxTB, self).structured_traceback(
   1241     etype, value, etb, tb_offset=tb_offset, context=context
   1242 )

File ~/.cache/pypoetry/virtualenvs/ai-xp-QtXkVPyw-py3.13/lib/python3.13/site-packages/IPython/core/ultratb.py:212, in ListTB.structured_traceback(self, etype, evalue, etb, tb_offset, context)
    210     out_list.extend(self._format_list(elist))
    211 # The exception info should be a single entry in the list.
--> 212 lines = "".join(self._format_exception_only(etype, evalue))
    213 out_list.append(lines)
    215 # Find chained exceptions if we have a traceback (not for exception-only mode)

File ~/.cache/pypoetry/virtualenvs/ai-xp-QtXkVPyw-py3.13/lib/python3.13/site-packages/IPython/core/ultratb.py:374, in ListTB._format_exception_only(self, etype, value)
    371     s = self._some_str(value)
    372 if s:
    373     output_list.append(
--> 374         theme_table[self._theme_name].format(
    375             stype_tokens
    376             + [
    377                 (Token.ExcName, ":"),
    378                 (Token, " "),
    379                 (Token, s),
    380                 (Token, "\n"),
    381             ]
    382         )
    383     )
    384 else:
    385     output_list.append("%s\n" % stype)

File ~/.cache/pypoetry/virtualenvs/ai-xp-QtXkVPyw-py3.13/lib/python3.13/site-packages/IPython/utils/PyColorize.py:66, in Theme.format(self, stream)
     63 def format(self, stream: TokenStream) -> str:
     64     style = self.as_pygments_style()
---> 66     return pygments.format(stream, Terminal256Formatter(style=style))

File ~/.cache/pypoetry/virtualenvs/ai-xp-QtXkVPyw-py3.13/lib/python3.13/site-packages/pygments/__init__.py:64, in format(tokens, formatter, outfile)
     62 if not outfile:
     63     realoutfile = getattr(formatter, 'encoding', None) and BytesIO() or StringIO()
---> 64     formatter.format(tokens, realoutfile)
     65     return realoutfile.getvalue()
     66 else:

File ~/.cache/pypoetry/virtualenvs/ai-xp-QtXkVPyw-py3.13/lib/python3.13/site-packages/pygments/formatters/terminal256.py:250, in Terminal256Formatter.format(self, tokensource, outfile)
    249 def format(self, tokensource, outfile):
--> 250     return Formatter.format(self, tokensource, outfile)

File ~/.cache/pypoetry/virtualenvs/ai-xp-QtXkVPyw-py3.13/lib/python3.13/site-packages/pygments/formatter.py:124, in Formatter.format(self, tokensource, outfile)
    121 if self.encoding:
    122     # wrap the outfile in a StreamWriter
    123     outfile = codecs.lookup(self.encoding)[3](outfile)
--> 124 return self.format_unencoded(tokensource, outfile)

File ~/.cache/pypoetry/virtualenvs/ai-xp-QtXkVPyw-py3.13/lib/python3.13/site-packages/pygments/formatters/terminal256.py:286, in Terminal256Formatter.format_unencoded(self, tokensource, outfile)
    283             # outfile.write( '!' + str(ottype) + '->' + str(ttype) + '!' )
    285     if not_found:
--> 286         outfile.write(value)
    288 if self.linenos:
    289     outfile.write("\n")

TypeError: string argument expected, got 'ExpatError'
```

</details>

PS : Thanks a lot for the lib, it is very straightforward to use :)
