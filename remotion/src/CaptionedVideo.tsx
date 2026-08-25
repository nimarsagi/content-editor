import React from "react";
import {
  AbsoluteFill,
  OffthreadVideo,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import type { CaptionCard, CaptionedVideoProps } from "./types";

/**
 * The video, with caption cards burned on top.
 *
 * THREE RULES FROM THE SPEC ARE TRUE BY CONSTRUCTION HERE, not by discipline:
 *
 *   1. NO ANIMATION. A card is either on screen or it is not. There is no
 *      interpolate() anywhere in this file, so no fade, no pop, no scale, and
 *      no per-word highlight can creep in later without someone adding one on
 *      purpose. The word-by-word look was tried and explicitly reversed.
 *   2. NO RE-WRAPPING. `lines` was computed against the pixel budget by
 *      chunk_captions.py. Letting CSS wrap instead would silently produce lines
 *      wider than the safe zone allows, on exactly the phrases that are longest.
 *   3. CAPTIONS ARE TOPMOST. They are the last child of the AbsoluteFill.
 */

const findCard = (cards: CaptionCard[], seconds: number): CaptionCard | null => {
  // Cards are contiguous and gapless by construction, so the first match is the
  // only match. `end` is exclusive: card N ends on the frame N+1 begins, which
  // is what "no gap between cards" means in frames rather than in seconds.
  for (const card of cards) {
    if (seconds >= card.start && seconds < card.end) {
      return card;
    }
  }
  return null;
};

export const CaptionedVideo: React.FC<CaptionedVideoProps> = ({
  videoSrc,
  cards,
  style,
}) => {
  const frame = useCurrentFrame();
  const { fps, height } = useVideoConfig();
  const card = findCard(cards, frame / fps);

  // The anchor is the block's CENTRE, expressed as a fraction of frame height,
  // so it survives a canvas change. translateY(-50%) is what makes it the
  // centre rather than the top — without it the block hangs below the anchor
  // and a two-line card breaches the bottom safe margin.
  const anchorPx = style.anchorFraction * height;

  return (
    <AbsoluteFill style={{ backgroundColor: "black" }}>
      <OffthreadVideo src={staticFile(videoSrc)} />

      {card === null ? null : (
        <AbsoluteFill>
          <div
            style={{
              position: "absolute",
              top: anchorPx,
              left: style.centreXPx,
              transform: "translate(-50%, -50%)",
              width: style.maxLineWidthPx,
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              textAlign: "center",
              fontFamily: `"${style.fontFamily}", sans-serif`,
              fontWeight: style.fontWeight,
              fontSize: style.fontSizePx,
              lineHeight: style.lineHeightEm,
              color: style.colour,
              textTransform: style.uppercase ? "uppercase" : "none",
              // A soft dark shadow rather than a hard stroke: the spec's choice,
              // on the grounds that a stroke breaks down under compression.
              textShadow:
                style.shadow === "soft_dark"
                  ? "0px 4px 16px rgba(0,0,0,0.75), 0px 2px 4px rgba(0,0,0,0.55)"
                  : "none",
              // No background box, no pill.
              background: "none",
            }}
          >
            {card.lines.map((line, index) => (
              // whiteSpace: pre keeps the pre-computed break. See rule 2.
              <div key={index} style={{ whiteSpace: "pre" }}>
                {line}
              </div>
            ))}
          </div>
        </AbsoluteFill>
      )}
    </AbsoluteFill>
  );
};
