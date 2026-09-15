# acquire/

Personal audio acquisition helpers (yt-dlp based). Output goes to `../music/` (gitignored, private).

Never re-expose the acquired full tracks to the public `duo-li` website — private/personal use only (see README.md at repo root for the reasoning).

Example:

```
yt-dlp -x --audio-format mp3 --audio-quality 0 --add-metadata --embed-thumbnail "<url>"
```

Nothing scripted here yet — first pass is manual, one track, to validate the rest of the pipeline end-to-end.
