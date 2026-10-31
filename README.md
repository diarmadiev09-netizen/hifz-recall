# Hifz Recall

Memorise the Quran with active recall and spaced review, on your phone, without internet.
Interface in Kazakh, Russian and English.

**Open the app:** https://diarmadiev09-netizen.github.io/hifz-recall/

## Install on a phone

- **Android (Chrome):** open the app link, then tap **Install app** (or browser menu ⋮ → Install app).
- **iPhone (Safari):** open the app link, tap **Share** → **Add to Home Screen**.

After the first visit the app works fully offline. Listening to recitation needs internet.

## Practice modes

- **Recall:** see the end of the previous āyah, recite the next one from memory, reveal it and grade yourself. Your grade schedules the next review.
- **Fade:** the chosen range with a share of its words hidden (25–100%), optionally showing first letters. Tap a gap to check it.
- **Next word:** build each āyah by picking the next word from four options. Āyāt with slips can be sent to Recall.
- **Progress:** memory map of the sūrah and the āyāt due for review today.

Progress stays on the device. Use Settings → Backup to move it to a new phone.

## Sources

- Arabic text and font: King Fahd Glorious Quran Printing Complex (Madinah Mushaf, Hafs ʿan ʿĀṣim), via the Quran.com API.
- Translations: Saheeh International (English), Elmir Kuliev (Russian), Khalifa Altay (Kazakh), via Quran.com.
- Word-by-word meanings: Quran.com (English).
- Recitation: Mishary Rashid Alafasy, streamed from Quran.com.

## Rebuilding

```
python src/fetch_quran.py raw                  # download text and translations from api.quran.com
python src/build_data.py raw src/quran.json    # clean and check the data
python src/build.py                            # writes docs/ (web app) and dist/ (single offline file)
```

`docs/` is what GitHub Pages serves. To redraw the icons, run `python src/save_icons.py`,
open http://127.0.0.1:8770/icons.html and call `saveAll()` in the page.
