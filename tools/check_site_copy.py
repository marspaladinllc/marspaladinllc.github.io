# -*- coding: utf-8 -*-
"""
Verify the copy on westwarddash.com (index.html) against the decisions on record.

    python tools/check_site_copy.py            # this repo's index.html
    python tools/check_site_copy.py <file>     # or any file

Checks, in order:
  1. aboutTilesData is valid JSON and every tile covers all 18 languages.
  2. The retired 09-23 wording is absent (invented childhood details, 局局博心跳,
     the old spellings of the wife's name).
  3. The canonical wording is present (one-yuan board game, Lingrujiang,
     局局都心跳), and the 简繁/ru/uk forms of her name are the ones the game credits use.
  4. No studio copy claims a team when the studio is one person.

Exit code 0 = everything passed. Non-zero = the report lists what failed.
Facts come from westjourneychess CommunityPosts/13_website_story.md on origin/main.
"""
import io, json, re, sys

LANGS = ["zh", "tc", "en", "ja", "ko", "fr", "de", "es", "it", "pt",
         "ru", "pl", "cs", "uk", "tr", "th", "vi", "id"]

# text that must NOT appear -> why it was retired
FORBIDDEN = {
    "泛黄磨破":        "invented detail, cut 09-23 (the board was bought for one yuan, not yellowed/worn)",
    "放学后":          "invented detail, cut 09-23 (he rounded up 1-3 friends; 'after school' was made up)",
    "筋斗云腾空":      "invented detail, cut 09-23 (clouds)",
    "简陋图纸":        "invented detail, cut 09-23 (hand-drawn sheet)",
    "小鬼缠住":        "invented detail, cut 09-23 (imps)",
    "局局博心跳":      "push-your-luck wording: must be 局局都心跳",
    "Lingru-chan":     "her name is romanized Lingrujiang",
    "リンルーちゃん":  "her name is romanized Lingrujiang",
    "링루짱":          "her name is romanized Lingrujiang",
    "Линжу-чан":       "ru form is Линжуцзян",
    "Лінжу-чан":       "uk form is Лінжуцзян",
    "Linh Như Tương":  "her name is romanized Lingrujiang",
    "一群热爱游戏":    "one-person studio, not a group",
    "一群纯粹玩家":    "one-person studio, not a group",
    "lifelong gamers": "one-person studio, not a group",
    "by gamers for gamers": "one-person studio, not a group",
    "die-hard gamers": "one-person studio, not a group",
    "逼氪":            "monetization pledges are not part of the studio copy",
    "钱包":            "monetization pledges are not part of the studio copy",
    "錢包":            "monetization pledges are not part of the studio copy",
}

# text that MUST appear -> how many times at least
REQUIRED = {
    "一块钱":      1,   # the one-yuan board game
    "Lingrujiang": 1,
    "局局都心跳":  1,
    "灵如酱":      1,   # 简体 keeps her Chinese name, as the game credits do
    "靈如醬":      1,
    "Линжуцзян":   1,
    "Лінжуцзян":   1,
}


def load(path):
    with io.open(path, "r", encoding="utf-8", newline="") as f:
        return f.read()


def about_tiles(s):
    """Parse the aboutTilesData array out of the page."""
    i = s.index("aboutTilesData = [")
    j = s.index("[", i)
    depth = 0
    for k in range(j, len(s)):
        if s[k] == "[":
            depth += 1
        elif s[k] == "]":
            depth -= 1
            if depth == 0:
                break
    return json.loads(s[j:k + 1])


def main(path):
    s = load(path)
    problems = []
    notes = []

    # 1. structure
    try:
        tiles = about_tiles(s)
        notes.append("aboutTilesData parses, %d tiles" % len(tiles))
        for n, tile in enumerate(tiles):
            for field in ("titles", "desc1", "desc2", "authors"):
                if field not in tile:
                    continue
                missing = [L for L in LANGS if L not in tile[field]]
                extra = [L for L in tile[field] if L not in LANGS]
                if missing:
                    problems.append("tile %d %s: missing %s" % (n, field, " ".join(missing)))
                if extra:
                    problems.append("tile %d %s: unexpected %s" % (n, field, " ".join(extra)))
        notes.append("all tiles cover the 18 languages")
    except ValueError as e:
        problems.append("aboutTilesData does not parse: %s" % e)

    # 2. retired wording
    for bad, why in FORBIDDEN.items():
        n = s.count(bad)
        if n:
            lines = [str(i + 1) for i, L in enumerate(s.split("\n")) if bad in L][:5]
            problems.append("%r appears %dx (line %s) - %s"
                            % (bad, n, ",".join(lines), why))

    # 3. canonical wording
    for good, least in REQUIRED.items():
        n = s.count(good)
        if n < least:
            problems.append("%r appears %dx, expected at least %d" % (good, n, least))

    # report
    print("checked %s" % path)
    for line in notes:
        print("  ok   %s" % line)
    if problems:
        print()
        for p in problems:
            print("  FAIL %s" % p)
        print("\n%d problem(s)." % len(problems))
        return 1
    print("\nAll checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "index.html"))
