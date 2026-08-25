import { Config } from "@remotion/cli/config";

/**
 * Render settings. Deliberately conservative:
 *
 *   H.264 in an MP4, which is what TikTok and Instagram both accept without
 *   re-processing more than they already do.
 *
 *   CRF 18 — visually lossless for this kind of material. This is the THIRD
 *   encode the footage has been through (phone, then CapCut, then here), so
 *   this stage should not be where visible loss is introduced.
 */
Config.setVideoImageFormat("jpeg");
Config.setCodec("h264");
Config.setCrf(18);
Config.setOverwriteOutput(true);

// At startup every worker page competes for the static server, and the
// 28-second default is not enough for the first video frames to arrive.
//
// This is a ceiling on how long any ONE wait may take, never on the length of a
// render. Nothing here may open a delayRender() handle that stays open across
// frames — a handle at module scope turned this number into a hard limit on
// video length, and a two-minute take died at frame 1207 because of it. See the
// note in Root.tsx.
Config.setDelayRenderTimeoutInMilliseconds(120_000);
