import React, { useEffect, useState } from "react";
import {
  cancelRender,
  Composition,
  continueRender,
  delayRender,
} from "remotion";
import { CaptionedVideo } from "./CaptionedVideo";
import { INTER_SEMIBOLD } from "./font-data";
import type { CaptionedVideoProps } from "./types";

/**
 * INTER IS LOADED FROM DISK, NOT FROM GOOGLE.
 *
 * The 17-character line cap in _config/edit-defaults.yaml is derived from this
 * exact font: 580px / (62px x 0.52 em advance) = 17.99, floored. A substituted
 * fallback has different metrics, so the lines that overflow the safe zone
 * would be the longest ones — the least likely to be noticed in a spot check
 * and the most likely to be cropped by a platform's interface.
 *
 * Loading it from public/ rather than a CDN also means a render works with no
 * network, and cannot change under you when a font gets revised upstream.
 */
/**
 * THE FONT IS EMBEDDED, NOT FETCHED, AND THE WAIT FOR IT IS SCOPED TO A FRAME.
 *
 * Two separate faults broke every render longer than about two minutes, and
 * each hid the other:
 *
 *   1. The font came over HTTP from Remotion's static server. Under render
 *      concurrency that request could hang indefinitely.
 *   2. The handle that waited for it was opened at module scope, so its clock
 *      ran from page load across the whole render rather than across one wait.
 *
 * Together they meant a render died at whatever frame it reached when the timer
 * expired — 905, then 1207, then 49 — always blaming a font that was fine. Only
 * short videos passed, because they finished before the clock ran out.
 *
 * INTER_SEMIBOLD is a data URI generated from public/fonts/Inter-SemiBold.ttf by
 * render_captions.py. There is no request to queue and nothing to time out.
 */
const fontReady: Promise<unknown> =
  typeof FontFace === "undefined"
    ? Promise.resolve()
    : new FontFace("Inter", `url(${INTER_SEMIBOLD})`, {
        weight: "600",
        style: "normal",
      })
        .load()
        .then((face) => {
          document.fonts.add(face);
        });

// Once it is in, later frames open no handle at all.
let fontLoaded = false;
fontReady
  .then(() => {
    fontLoaded = true;
  })
  .catch(() => undefined);

const WithInter: React.FC<CaptionedVideoProps> = (props) => {
  const [handle] = useState<number | null>(() =>
    fontLoaded ? null : delayRender("loading Inter SemiBold"),
  );

  useEffect(() => {
    if (handle === null) {
      return;
    }
    fontReady
      .then(() => continueRender(handle))
      .catch((err) => {
        // Cleared before reporting, or the real cause is buried under a
        // delayRender timeout later — which is what the raw FontFace API did
        // here, and it cost a render to work out.
        continueRender(handle);
        cancelRender(new Error(`Inter SemiBold failed to load: ${err}`));
      });
  }, [handle]);

  return <CaptionedVideo {...props} />;
};

/**
 * Placeholder props. A real render always passes --props, and render_captions.py
 * builds them from _config/edit-defaults.yaml. These exist so `npm run preview`
 * opens without arguments.
 */
const placeholder: CaptionedVideoProps = {
  videoSrc: "input.mp4",
  cards: [],
  style: {
    fontFamily: "Inter",
    fontWeight: 600,
    fontSizePx: 62,
    colour: "#FFFFFF",
    anchorFraction: 0.65,
    centreXPx: 540,
    maxLineWidthPx: 580,
    lineHeightEm: 1.3,
    shadow: "soft_dark",
    uppercase: false,
  },
  meta: { width: 1080, height: 1920, fps: 30, durationInFrames: 300 },
};

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="CaptionedVideo"
      component={WithInter}
      defaultProps={placeholder}
      // Frame size, rate and length all come from the props rather than being
      // fixed here, so the composition cannot disagree with the input file.
      calculateMetadata={({ props }) => ({
        width: props.meta.width,
        height: props.meta.height,
        fps: props.meta.fps,
        durationInFrames: props.meta.durationInFrames,
      })}
      // Required by the type, immediately overridden by calculateMetadata.
      width={1080}
      height={1920}
      fps={30}
      durationInFrames={300}
    />
  );
};
