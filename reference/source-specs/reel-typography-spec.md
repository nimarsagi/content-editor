# Reel typography and safe-zone spec

Reference spec for the Remotion pipeline. Covers canvas, safe zones, fonts, sizing, and placement for hook and caption text on IG Reels / TikTok exports.

## Canvas

- **Dimensions:** 1080 x 1920 px
- **Aspect ratio:** 9:16
- **Format:** single export works for both TikTok and Instagram Reels

## Safe zone (conservative, works on both platforms)

Platform UI specs aren't officially published — these margins are set conservatively so one export clears both TikTok's and Instagram's overlay elements (profile bar, caption bar, engagement icons, audio ticker) without per-platform re-cuts.

| Edge | Clear this much |
|---|---|
| Top | 250 px |
| Bottom | 480 px |
| Left | 120 px |
| Right | 250 px |

Resulting safe content area: **710 x 1190 px**, centered.

## Text placement

| Element | Vertical position (from top) |
|---|---|
| Hook text | 300–700 px |
| Subtitle / supporting line | ~700–780 px |
| Burned-in captions | 1150–1350 px |

All text horizontally centered within the safe content area.

## Fonts

**Primary: Inter** — used for both hook and captions by default. Chosen because it reads as "native caption," not "designed graphic" — fits a diagnostic/analytical brand voice better than warmer geometric sans fonts.

| Role | Font | Weight | Size (at 1080 px width) | % of width |
|---|---|---|---|---|
| Hook | Inter | 800 (ExtraBold) | 85–110 px | ~8–10% |
| Subtitle | Inter | 500 (Medium) | 48–58 px | ~4.5–5% |
| Burned-in captions | Inter | 600 (SemiBold) | 55–70 px | ~5–6.5% |
| Absolute legibility floor | — | — | 40 px | — |

**Optional variant: Poppins for hook only** — swap hook font to Poppins Bold (700) when a video's tone is instructional/friendly rather than diagnostic. Keep subtitle and captions in Inter regardless. Do not use Poppins below ~19px effective size or pair it with Inter at similar sizes — the two need at least ~1.8x size contrast or they read as inconsistent rather than intentional.

Avoid: Times New Roman or other traditional serifs for hook/caption text — breaks down under video compression and reads as an unstyled document font rather than a designed caption.

## Text formatting rules

- Hook: max 2 lines, 20–28 characters per line
- One font family per video (Inter, or Inter + Poppins-hook variant) — never introduce a third
- Vary weight and size for hierarchy, not additional font families

## Implementation note for Remotion

Define as constants and drive all compositions from them, so platform UI shifts only require updating these values:

```
SAFE_TOP = 250
SAFE_BOTTOM = 480
SAFE_LEFT = 120
SAFE_RIGHT = 250
HOOK_SIZE = 96
SUBTITLE_SIZE = 52
CAPTION_SIZE = 62
FONT_PRIMARY = "Inter"
FONT_HOOK_ALT = "Poppins"
```

## Confidence notes

- Canvas dimensions (1080x1920): high confidence, consistent across all sources.
- Safe zone margins: no official platform spec exists; figures above are a conservative envelope built from multiple third-party measurement guides (which vary 150–480px on some edges) and platform UI has shifted before without notice. Validate periodically by exporting a test video with a safe-zone overlay burned in and checking on-device.
- Font size guidance: craft convention based on legibility norms, not a published platform spec.
