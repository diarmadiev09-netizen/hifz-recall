# Hifz Recall

Memorise the Quran with active recall and spaced review, on your phone, without internet.
Interface in Kazakh, Russian and English.

**Open the app:** https://diarmadiev09-netizen.github.io/hifz-recall/

## Install on a phone

- **Android (Chrome):** open the app link, then tap **Install app** (or browser menu ⋮ → Install app).
- **iPhone (Safari):** open the app link, tap **Share** → **Add to Home Screen**.

After the first visit the app works fully offline. Recitation plays offline for sūrahs you download in the Listen tab.

## Practice modes

- **Listen:** Mishary Alafasy's recitation with each word highlighted as it is read. Repeat every āyah 1–10 times and the range 1–3 times or endlessly, slow it down, and turn on a pause after each āyah to recite it back. Download a sūrah once to play it without internet.
- **Recall:** see the end of the previous āyah, recite the next one from memory, reveal it and grade yourself. Your grade schedules the next review.
- **Fade:** the chosen range with a share of its words hidden (25–100%), optionally showing first letters. Tap a gap to check it.
- **Next word:** build each āyah by picking the next word from four options. Āyāt with slips can be sent to Recall.
- **Word grammar:** tap any word (or rest the pointer on it on a computer) to see its sarf (word type, root and its class, bāb, wazn, person) and its nahw (iʿrāb of each part of the word).
- **Progress:** memory map of the sūrah and the āyāt due for review today.

Progress stays on the device. Use Settings → Backup to move it to a new phone.

## Sources

- Arabic text and font: King Fahd Glorious Quran Printing Complex (Madinah Mushaf, Hafs ʿan ʿĀṣim), via the Quran.com API.
- Translations: Saheeh International (English), Elmir Kuliev (Russian), Khalifa Altay (Kazakh), via Quran.com.
- Word-by-word meanings: Quran.com (English).
- Recitation: Mishary Rashid Alafasy, streamed from Quran.com.
- Word meanings in Russian and Kazakh: an automatic (AI) translation of the 1,000 most frequent dictionary entries, which cover 89% of all words (`src/lemma_meanings.txt`). They may contain mistakes; the other words show the English meaning only.
- Word grammar: the Quranic Arabic Corpus 0.4 (root, lemma, verb form, aspect, voice, person) and the MASAQ dataset (iʿrāb role, case and case marker). See the notices below.

## Rebuilding

```
python src/fetch_quran.py raw                  # download text and translations from api.quran.com
python src/build_data.py raw src/quran.json    # clean and check the data
python src/build.py                            # writes docs/ (web app) and dist/ (single offline file)
```

The word grammar is rebuilt from two files placed in `grammar/`: `quranic-corpus-morphology-0.4.txt`
(from https://corpus.quran.com/download/) and `MASAQ.csv` (from https://data.mendeley.com/datasets/9yvrzxktmr/5).
Then run `python src/build_grammar.py` before `python src/build.py`.
`python src/lemmas.py 1001 1250` prints the next dictionary entries to translate into `src/lemma_meanings.txt`.

`docs/` is what GitHub Pages serves. To redraw the icons, run `python src/save_icons.py`,
open http://127.0.0.1:8770/icons.html and call `saveAll()` in the page.

## Grammar data notices

**Quranic Arabic Corpus.** The sarf data is derived from the Quranic Arabic Corpus (morphology, version 0.4),
Copyright (C) 2011 Kais Dukes, licensed under the GNU General Public License. The annotation can be used in any
website or application provided its source is clearly indicated and linked: https://corpus.quran.com.
The corpus builds on the verified Arabic text of the Tanzil project (https://tanzil.net).

**MASAQ.** The nahw (iʿrāb) data is derived from MASAQ, the Morphologically-Analyzed and Syntactically-Annotated
Quran Dataset (Mendeley Data, version 5, doi:10.17632/9yvrzxktmr.5), licensed under CC BY 4.0
(https://creativecommons.org/licenses/by/4.0/). Changes: the per-segment tags were turned into Arabic iʿrāb
sentences and aligned to Quran.com's word numbering.
