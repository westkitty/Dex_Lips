# Product contract

## User goal

Upload one image or existing video and an audio track. Generate speech-synchronized mouth motion as an MP4, including characters whose anatomy does not resemble a human. Preserve identity, original background/motion, audio timing, user edits, and free-compute boundary. Keep the app easy to use on desktop and Android tablet browsers.

## Supported input classes

1. Still human/human-like portrait + dialogue audio.
2. Existing human-like video + replacement dialogue audio.
3. Still stylized/nonhuman character + user-authored/approved mouth rig.
4. Existing stylized/nonhuman video + user-authored rig with placement/tracking/keyframes.

## Five application screens / states

- Import: media drop zone, preview, duration, aspect ratio, language, private-content warning.
- Route: source classification suggested with user override; neural eligible/ineligible with real cost/availability status; no hidden paid fallback.
- Rig/anchors: X/A-F (+ G/H optional) mouth-shape editor/import; anchor, affine transform, optional mask; frame keyframes for video; neutral/closed mouth baseline.
- Timeline/preview: audio waveform and timed mouth cues, seek/step/play, inspect timing and occlusions, manual correction, 2-sec preview render.
- Export/receipt: result preview, MP4/H.264/AAC, checksum, detailed job receipt, optional Drive handoff; no auto deletion before verification.

## Nonfunctional requirements

- Responsive touch controls (Samsung/Android tablet), keyboard, understandable labels and focus; reduced-motion mode.
- Input size/duration ceilings configurable and enforced before upload; no indefinite web tasks.
- Confidentiality: transient scratch outputs, explicit external transfer, no logging original media content; no public galleries by default.
- Server-side FFmpeg optional; browser preview always informative even if codec/worker export unavailable.
- Zero spend HARD STOP. Do not infer free access from product marketing or prior plan entitlement; inspect current account quotas and billing before any paid-capable call.
- All source examples must be fully synthetic or explicitly user-licensed; don't publish uploaded personal footage.
- User-approved mouth shapes remain separate from canonical reference source bytes.
