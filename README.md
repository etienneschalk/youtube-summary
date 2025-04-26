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
- [x] Support Shorts
- [ ] Check full Youtube History export helper lib: https://github.com/menggatot/youtube-watch-history-to-csv
- [ ] Use title tag from video to extract at least the title, and inspect the description manually. Code susceptible to break frequently. See example HTML File.
- [ ] Also use a pure txt file with list of videos as input source. To copy paste easily.

## Misc 

### Copy the diff of all python files into clipboard:


FR : 

> A partir de cet output de la commande git show, écris un titre et une description de Pull Request sur GitHub expliquant les modifications apportées.

EN : 

> From this output of the git show command, write a Pull Request title and description on GitHub explaining the changes made.


```bash
git ds -- '*.py' | xclip -sel clip
```

## [FR] Commentaire sur une vidéo YouTube

Je récupère les sous-titres de la vidéo que j'envoie ensuite à un modèle de langage à utilisation gratuite en lui demandant de le résumer.

Le modèle utilisé est : https://openrouter.ai/deepseek/deepseek-chat-v3-0324:free/api

Le prompt utilisé est :

"Tu es un assistant qui synthétises les transcripts vidéo.
Résume les points clefs du transcript qui suit.
Pour chaque point clef, écris une liste à puces de 3 à 5 éléments.
Le transcript est en français et je souhaite un résumé en français.
Voici le transcript:

{transcript}"

Et {transcript} est remplacé par l'ensemble des sous-titres, insérés tels quels.

Pour récupérer les transcripts (sous-titres) j'utilise une bibliothèque Python : https://pypi.org/project/youtube-transcript-api/

Note : en plus du prompt je rajoute un "assistant" (je ne connais pas trop les LLM, mais je laisse car ça marchait bien). Cet "assistant", je ne l'ai pas écrit contrairement au prompt. Je l'ai récupéré d'un "raisonnement" du modèle r1-1776 de "Perplexity AI": https://labs.perplexity.ai/ (à noter que ce modèle est aussi disponible pour utilisation automatique sur https://openrouter.ai/perplexity/r1-1776 mais il est payant)

"I need to structure these points concisely in French,
ensuring each major topic is covered with its key arguments and outcomes.
The user likely wants a clear, structured summary without missing critical debates or perspectives.
I should avoid personal opinions and stick to the transcript's content,
highlighting the main discussions, differing viewpoints, and conclusions where present.
Also, noting the cultural and political implications of each topic as discussed by the panelists."

Attention, il faut bien relire les résumés, car parfois des points-clefs sont oubliés ce qui introduit un "biais d'omission". En expérimentant avec les prompts, et sur une autre vidéo, j'avais remarqué que l'IA "oubliait" parfois de mentionner les points de vue de l'opposition... en ne mentionnant que le point de vue du groupe au pouvoir, ce qui biaisait énormément le résumé et le rendait inutilisable.

Les noms et prénoms sont aussi fréquemment charcutés, surtout lorsque les sous-titres sont générés automatiquement. Il faut repasser manuellement derrière, ou bien une autre solution serait de donner dans le prompt la liste des noms et prénoms des personnalités mentionnées dans une vidéo. Sur 28 minutes de Arte par exemple, la description contient toujours les 3 noms des intervenants, mais je n'ai hélas pas réussi à récupérer automatiquement les descriptions de vidéos youtube sans trop d'effort (les bibliothèques Python semblaient en panne).


