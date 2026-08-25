/**
 * The shape of what Python hands over.
 *
 * NOTHING IN THIS PROJECT DECIDES A VISUAL CONSTANT. Font size, colour, the
 * anchor, the safe margins, the line cap — all of them live in
 * _config/edit-defaults.yaml and arrive here as props. That is the same rule the
 * Python side works under: no threshold in a script. It matters more here than
 * anywhere else, because a caption style that drifts from the config is a
 * difference nobody sees until they compare two videos side by side.
 */

export type CaptionCard = {
  index: number;
  start: number;      // seconds, on the finished video's timeline
  end: number;
  duration: number;
  text: string;
  /** Pre-wrapped by chunk_captions.py against the width budget. Never re-wrap. */
  lines: string[];
};

export type CaptionStyle = {
  fontFamily: string;
  fontWeight: number;
  fontSizePx: number;
  colour: string;
  /** Block centre, as a fraction of frame height. */
  anchorFraction: number;
  centreXPx: number;
  maxLineWidthPx: number;
  lineHeightEm: number;
  /** "soft_dark" draws a shadow; "none" draws nothing. No stroke, ever. */
  shadow: string;
  /** Sentence case is applied upstream; this is only a guard against re-casing. */
  uppercase: boolean;
};

export type VideoMeta = {
  /** From _config geometry.canvas, so the frame matches what captions were measured against. */
  width: number;
  height: number;
  /** Read off the actual input file with ffprobe — never assumed. */
  fps: number;
  durationInFrames: number;
};

export type CaptionedVideoProps = {
  /** Path relative to remotion/public/, written there by render_captions.py. */
  videoSrc: string;
  cards: CaptionCard[];
  style: CaptionStyle;
  meta: VideoMeta;
};
