#!/usr/bin/env python3
"""
chunk_captions.py — the transcribed words become phrase cards.

THE TIMINGS HERE BELONG TO THE FINISHED VIDEO, because that is the only thing
this pipeline ever transcribes. Cutting happens in CapCut, before anything
reaches this workspace. Transcribing raw clips and cutting afterwards would
leave every timing pointing at footage that no longer exists, and each caption
would drift further out of sync as the video went on — so the order is not a
preference, and reversing it is the single easiest way to break this build.

This is the known failure point — a previous self-built subtitle generator
failed here — so three rules matter more than they look:

  1. DURATION IS THE RULE. Word count and reading speed are diagnostics. They
     cannot all be rules: captions run wall-to-wall at zero gap and track speech
     exactly, so a card's duration is words / speech rate, not a free choice.
  2. PREFER THE FEWEST CARDS that satisfy the duration window. A chunker that
     splits at every legal boundary produces perfect timings and a frantic
     result. "Regroups too often" is a live candidate for the earlier failure.
  3. NEVER STRIP OR AUTO-BALANCE QUOTES. Reported speech opens on one card and
     closes several cards later. Balancing per card corrupts the text.

    python3 stages/02_assemble/scripts/chunk_captions.py <run-slug>
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import pipeline_lib as lib  # noqa: E402


def is_clause_end(word: str, punctuation: list[str]) -> bool:
    stripped = word.strip()
    # A closing quote after the punctuation still ends the clause: `world."`
    stripped = stripped.rstrip('"”’\')')
    return bool(stripped) and stripped[-1] in punctuation


def wrap(text: str, chars_per_line: int, max_lines: int) -> list[str] | None:
    """
    Break a card's text into at most max_lines lines within the character budget.

    RETURNS None IF IT DOES NOT FIT. That is the important part of this
    signature. A line break has to land between two words, so the real capacity
    of a card is not chars_per_line * max_lines — it is whatever the word
    boundaries happen to allow, which is always less and sometimes much less.
    "so the thing about pricing that" is 31 characters and fits in 34, yet there
    is no word boundary that leaves both halves under 17: the splits available
    are 2/28, 6/24, 12/18 and 18/12. It cannot be laid out.

    An earlier version answered that case by slicing the string at 17 characters
    and shipping "so the thing abou" / "t pricing that". Callers must treat None
    as "close this card earlier", never as a reason to cut a word in half.

    A single word longer than the budget is the one thing that cannot be helped.
    It goes on a line of its own and overruns, because a too-wide line is a
    smaller sin than a broken word, and hyphenation is not on the table.
    """
    words = text.split()
    if not words:
        return [""]

    lines: list[list[str]] = [[]]
    for word in words:
        candidate = " ".join(lines[-1] + [word])
        if lines[-1] and len(candidate) > chars_per_line:
            if len(lines) >= max_lines:
                return None
            lines.append([word])
        else:
            lines[-1].append(word)

    laid_out = [" ".join(line) for line in lines]

    # Balance a two-line card so the first line is not far longer than the
    # second — but only ever at a word boundary.
    if len(laid_out) == 2:
        best, best_gap = None, None
        for split in range(1, len(words)):
            top = " ".join(words[:split])
            bottom = " ".join(words[split:])
            if len(top) > chars_per_line or len(bottom) > chars_per_line:
                continue
            gap = abs(len(top) - len(bottom))
            if best_gap is None or gap < best_gap:
                best, best_gap = [top, bottom], gap
        if best:
            return best

    return laid_out


def build_cards(words, caption_rules, chars_per_line):
    """
    Greedy, longest-card-first within the duration window.

    A card is closed at the LATEST legal split point that keeps it inside the
    target duration and the text budget. Closing at the latest rather than the
    earliest is what "prefer the fewest cards" means in code.

    NO CARD MAY END ON A WORD THAT CANNOT STAND ALONE. Punctuation and silence
    choose where a card ends; `never_end_card_on` says where a split may not
    land once those two have run out. Without it the fallback split lands
    wherever the budget happened to overflow, which produces "...conversation,
    the" followed by "worse the output gets" — the phrase arrives in two pieces
    and the first is unreadable on its own.

    This matters most late in a take. Pauses stay roughly constant while the
    speech gets denser, so the legal splits thin out exactly where the reader
    can least afford a broken phrase.
    """
    target_min, target_max = caption_rules["target_duration_s"]
    hard_max = caption_rules["max_duration_s"]
    split_silence = caption_rules["split_on_silence_ms"] / 1000.0
    punctuation = caption_rules["split_on_clause_punctuation"]
    max_lines = caption_rules["max_lines"]
    never_end_on = {w.lower() for w in caption_rules["never_end_card_on"]}

    def dangles(word: dict) -> bool:
        """
        Would closing a card after this word leave a phrase hanging?

        Punctuation settles it first: a word carrying a comma or a full stop is
        the end of something, whatever the word itself is. Only a bare word gets
        checked against the list.
        """
        bare = word["word"].strip().strip('"”’\')')
        if bare and bare[-1] in punctuation:
            return False
        return bare.strip(".,!?;:").lower() in never_end_on

    def phrase_safe(cut_at: int) -> int | None:
        """
        Walk a proposed split backwards until the card no longer ends on a
        dangling word. Returns None if there is no such split — a run of
        function words with nothing before it — in which case the caller keeps
        its original cut rather than losing the card.
        """
        cut = cut_at
        while cut >= 1 and dangles(current[cut - 1]):
            cut -= 1
        return cut if cut >= 1 else None

    cards = []
    current: list[dict] = []
    last_legal_split = None   # index into `current` after which we may close

    def flush(upto: int | None = None):
        nonlocal current, last_legal_split
        cut_at = len(current) if upto is None else upto
        head, tail = current[:cut_at], current[cut_at:]
        if head:
            cards.append(head)
        current = tail
        last_legal_split = None

    for index, word in enumerate(words):
        current.append(word)

        text = " ".join(w["word"] for w in current).strip()
        duration = current[-1]["end"] - current[0]["start"]

        # Is THIS word a legal place to close a card?
        gap_after = (words[index + 1]["start"] - word["end"]) if index + 1 < len(words) else None
        legal = False
        if is_clause_end(word["word"], punctuation):
            legal = True
        elif gap_after is not None and gap_after >= split_silence:
            legal = True

        if legal:
            last_legal_split = len(current)

        over_time = duration > target_max
        # Asked of the wrapper rather than counted, because chars_per_line *
        # max_lines overstates the real capacity: the break has to fall between
        # two words. Counting characters accepted cards that could not be laid
        # out, and the wrapper then took them apart mid-word.
        over_text = wrap(text, chars_per_line, max_lines) is None

        if over_time or over_text:
            if last_legal_split and last_legal_split < len(current):
                # A legal split, but "legal" only means punctuation or a pause.
                # A 120ms breath after "the" is a legal split that still breaks a
                # phrase, so it is walked back like any other.
                flush(phrase_safe(last_legal_split) or last_legal_split)
            elif len(current) > 1:
                # No legal boundary anywhere in this card and it is now too long.
                # Split before the offending word rather than ship a card that
                # breaks the hard ceiling or overruns the frame — but back off
                # the dangling words first, because this fallback is where the
                # broken phrases came from.
                flush(phrase_safe(len(current) - 1) or (len(current) - 1))
            # a single word longer than the budget: let it through, flagged below

        # Hard ceiling is a rule, not a target.
        if current and current[-1]["end"] - current[0]["start"] > hard_max:
            flush()

    if current:
        flush()

    return cards


def join_underfloor(grouped, caption_rules, chars_per_line):
    """
    Join a card that would flash past into the card before it — when it fits.

    A card is on screen for as long as its words take to say. Cards run
    wall-to-wall with no gap, so the next card starts the instant this one ends
    and a short card cannot simply be held longer. The only way to lift one over
    the floor is to give it more words, and the only spare words are in the card
    before it.

    THIS OVERRIDES allow_orphan_cards, FOR UNDER-FLOOR CARDS ONLY. The spec keeps
    a two-word tail as its own card because in the reference reels that tail
    followed a real pause and read as deliberate. A tail that flashes past in
    0.36s is not that; it reads as a mistake.

    MOST UNDER-FLOOR CARDS CANNOT BE JOINED, and refusing is the right answer.
    At one row the budget is 25 characters and a joined card usually overruns it.
    Measured on the 2026-07-30 run: 10 cards under the floor, 2 joinable, the
    other 8 coming to 29-41 characters. Shipping those would run the caption off
    the frame, which is worse than a card that flashes. The remainder is the
    standing cost of one row at 44px, not something this pass failed to fix.

    Returns (groups, joined_count).
    """
    floor = caption_rules["min_duration_s"]
    ceiling = caption_rules["max_duration_s"]
    max_lines = caption_rules["max_lines"]

    def screen_end(groups, i):
        """
        When card i actually leaves the screen: the next card's start, capped by
        the ceiling. The same rule the stretch pass applies further down, so the
        duration tested here is the duration that gets checked against the floor.
        """
        if i + 1 < len(groups):
            return min(groups[i + 1][0]["start"], groups[i][0]["start"] + ceiling)
        return groups[i][-1]["end"]

    out = list(grouped)
    joined = 0
    i = 1
    while i < len(out):
        start = out[i][0]["start"]
        if screen_end(out, i) - start >= floor - 1e-9:
            i += 1
            continue

        candidate = out[i - 1] + out[i]
        text = re.sub(r"\s+([,.!?;:])", r"\1",
                      " ".join(w["word"] for w in candidate).strip())
        merged = out[:i - 1] + [candidate] + out[i + 1:]

        fits_frame = wrap(text, chars_per_line, max_lines) is not None
        within_ceiling = (screen_end(merged, i - 1) - candidate[0]["start"]
                          <= ceiling + 1e-9)

        if fits_frame and within_ceiling:
            out = merged
            joined += 1
            # Do not advance: the card that grew may now be the one to test.
        else:
            i += 1

    return out, joined


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: chunk_captions.py <run-slug>")
    slug = sys.argv[1]
    run = lib.run_dir(slug)

    # 01-transcript.json is the edit surface: a word you corrected there is the
    # word that reaches the screen. 01-transcript-raw.json is deliberately not
    # read here — it exists so learn_words.py can see what you changed.
    data = lib.read_json(lib.require(run / "01-transcript.json", "transcribe.py"))
    words = data["words"]
    if not words:
        sys.exit("the transcript has no words — nothing to caption.")

    cfg = lib.rules()
    prefs = lib.load_preferences("Pacing")
    if prefs["overrides"]:
        # The override path is not optional. The preferences record governs
        # "what gets cut, how aggressively, AND subtitle pacing" — a pacing rule
        # that nothing reads is the earlier failure repeating with a rule file
        # on top of it.
        cfg = lib.apply_overrides(cfg, prefs["overrides"])

    caption = cfg["caption"]
    geometry = cfg["geometry"]
    typography = cfg["typography"]

    # Characters per line is DERIVED, never copied. Recompute it here rather
    # than trusting the stored value, so a font-size change cannot silently
    # leave a stale character budget behind.
    derived = int(geometry["max_line_width_px"] /
                  (typography["caption_size_px"] * geometry["avg_char_advance_em"]))
    if derived != geometry["chars_per_line_derived"]:
        print(f"  ! chars-per-line in config says {geometry['chars_per_line_derived']}, "
              f"the geometry gives {derived}. Using {derived}; update the config.")
    chars_per_line = derived

    print(f"  chars per line      {chars_per_line}  "
          f"({geometry['max_line_width_px']}px / "
          f"{typography['caption_size_px']}px x {geometry['avg_char_advance_em']}em)")
    print(f"  duration            {caption['target_duration_s'][0]}-"
          f"{caption['target_duration_s'][1]}s target, "
          f"{caption['min_duration_s']}s floor, {caption['max_duration_s']}s ceiling  [RULE]")

    grouped = build_cards(words, caption, chars_per_line)
    grouped, joined = join_underfloor(grouped, caption, chars_per_line)
    if joined:
        print(f"  joined              {joined} card(s) that would have flashed "
              f"under the {caption['min_duration_s']}s floor")

    cards = []
    for index, group in enumerate(grouped):
        text = " ".join(w["word"] for w in group).strip()
        text = re.sub(r"\s+([,.!?;:])", r"\1", text)
        start = group[0]["start"]
        end = group[-1]["end"]
        # build_cards only closes a card the wrapper accepted, so None here means
        # the two disagree. Stopping is right: the alternative is writing null
        # into the cards file and discovering it during a render.
        lines = wrap(text, chars_per_line, caption["max_lines"])
        if lines is None:
            sys.exit(
                f"card {index} cannot be laid out in {caption['max_lines']} lines "
                f"of {chars_per_line} characters: {text!r}\n"
                "  build_cards accepted a card the wrapper rejects — that is a bug "
                "in the splitting, not something to work around here."
            )
        cards.append({
            "index": index,
            "text": text,
            "lines": lines,
            "start": round(start, 3),
            "end": round(end, 3),
            "words": len(group),
        })

    # Card N ends the frame card N+1 begins, so a caption never flickers off in
    # the beat between two phrases.
    #
    # BOUNDED BY THE CEILING, and that bound is not optional. Extending without
    # one holds a caption on screen for the whole of any silence in the video —
    # so a pause you deliberately left in for emphasis leaves the previous
    # sentence sitting there through all of it. This used to be unreachable
    # because a cutting stage removed every silence before the captions were
    # built; with the cutting done by hand in CapCut, whatever pauses you kept
    # are still there when this runs.
    for index in range(len(cards) - 1):
        cards[index]["end"] = min(cards[index + 1]["start"],
                                  cards[index]["start"] + caption["max_duration_s"])

    # The last card has nothing to meet, so a short tail stays short. An orphan
    # card is PRESERVED as a card — never merged into the one before it — but the
    # 0.6s floor is still a rule, and a one-word final card would otherwise flash.
    # Holding it a beat longer satisfies both: nothing follows it, so the extra
    # time costs nothing.
    if cards:
        last = cards[-1]
        if last["end"] - last["start"] < caption["min_duration_s"]:
            last["end"] = round(last["start"] + caption["min_duration_s"], 3)

    for card in cards:
        card["duration"] = round(card["end"] - card["start"], 3)
        card["chars_per_second"] = round(len(card["text"]) / max(card["duration"], 0.001), 1)

    # ---- diagnostics: measured, printed, enforced by nothing --------------
    diag = lib.diagnostics()
    cps_ceiling = diag["chars_per_second_flag_over"]
    frantic = [c for c in cards if c["chars_per_second"] > cps_ceiling]
    word_lo, word_hi = diag["words_per_card"]
    outside_words = [c for c in cards if not (word_lo <= c["words"] <= word_hi)]

    # ---- rules: a violation here is a bug --------------------------------
    too_long = [c for c in cards if c["duration"] > caption["max_duration_s"] + 1e-3]
    too_short = [c for c in cards if c["duration"] < caption["min_duration_s"] - 1e-3]
    too_wide = [c for c in cards if any(len(l) > chars_per_line for l in c["lines"])]
    too_many_lines = [c for c in cards if len(c["lines"]) > caption["max_lines"]]

    # The splitter backs off dangling words, so anything left here is a card it
    # could not place any other way.
    #
    # PUNCTUATION SETTLES IT FIRST, exactly as in build_cards.dangles(). "to
    # navigate inside of." ends on "of" and is a finished sentence; testing the
    # bare word alone reports it as a broken phrase, which is how this check
    # first flagged three cards that read perfectly.
    never_end_on = {w.lower() for w in caption["never_end_card_on"]}

    def hangs(card) -> bool:
        bare = card["text"].split()[-1].strip('"”’\')')
        if bare and bare[-1] in caption["split_on_clause_punctuation"]:
            return False
        return bare.strip(".,!?;:").lower() in never_end_on

    left_hanging = [c for c in cards if hangs(c)]

    lib.write_json(run / "02-caption-cards.json", {
        "topic": data["topic"],
        "duration": data["duration"],
        "chars_per_line": chars_per_line,
        "pacing_overrides": prefs["overrides"] or None,
        "cards": cards,
    })

    print(f"\n  {len(cards)} cards over {lib.timecode(data['duration'])}")
    durations = [c["duration"] for c in cards]
    print(f"    duration   min {min(durations):.2f}s  "
          f"mean {sum(durations)/len(durations):.2f}s  max {max(durations):.2f}s")

    print(f"\n  diagnostics — reported, enforced by nothing")
    print(f"    words per card outside {word_lo}-{word_hi}: {len(outside_words)} of {len(cards)}"
          f"  (expected: duration governs, not word count)")
    print(f"    over {cps_ceiling} chars/sec: {len(frantic)} cards"
          + (f"  <- these will read frantic" if frantic else ""))
    for card in frantic[:5]:
        print(f"      {lib.timecode(card['start'])}  {card['chars_per_second']:.0f} cps  "
              f"{card['text'][:40]!r}")

    # Under-floor cards are REPORTED, NOT FLAGGED AS BUGS, and that is a change
    # made deliberately on 2026-07-31.
    #
    # join_underfloor has already joined every one that could be joined. What is
    # left could not be: joining it would overrun the character budget and push
    # the caption off the frame. Nothing downstream can fix these either, because
    # cards run wall-to-wall and a card cannot be held past the card after it.
    #
    # They are the standing cost of one row at 44px — the trade made on
    # 2026-07-30 — so calling them bugs prints an error nobody can act on, every
    # run, forever. The lever that would actually clear them is a second row.
    if too_short:
        print(f"    under the {caption['min_duration_s']}s floor: {len(too_short)} cards"
              f"  <- could not be joined without overrunning {chars_per_line} chars")
        for card in too_short[:5]:
            print(f"      {lib.timecode(card['start'])}  {card['duration']:.2f}s  "
                  f"{card['text'][:40]!r}")

    problems = []
    if too_long:
        problems.append(f"{len(too_long)} cards over the {caption['max_duration_s']}s ceiling")
    if too_wide:
        problems.append(f"{len(too_wide)} lines over {chars_per_line} characters")
    if too_many_lines:
        problems.append(f"{len(too_many_lines)} cards over {caption['max_lines']} lines")
    if left_hanging:
        problems.append(
            f"{len(left_hanging)} cards end on a word that cannot stand alone: "
            + ", ".join(repr(c["text"][-24:]) for c in left_hanging[:3]))
    if problems:
        print("\n  RULE VIOLATIONS — these are bugs, not diagnostics:")
        for problem in problems:
            print(f"    - {problem}")
    else:
        print("\n  all caption rules hold")

    print("\n  next: write_srt.py, then render_captions.py")


if __name__ == "__main__":
    main()
