from __future__ import annotations
from datetime import date
import json
from pathlib import Path

def main(out_json: str, artist: str, title: str, album: str, genre: str, mood: list[str], description: str) -> None:
    Path(out_json).parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "artist": artist,
        "title": title,
        "album": album,
        "genre": genre,
        "mood": mood,
        "release_date": str(date.today()),
        "description": description,
        "explicit": False,
        "language": "Instrumental/None"
    }
    Path(out_json).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Metadata written: {out_json}")

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--out", required=True)
    p.add_argument("--artist", required=True)
    p.add_argument("--title", required=True)
    p.add_argument("--album", required=True)
    p.add_argument("--genre", default="Ambient")
    p.add_argument("--mood", nargs="*", default=["Sleep"])
    p.add_argument("--description", default="")
    args = p.parse_args()
    main(args.out, args.artist, args.title, args.album, args.genre, args.mood, args.description)
