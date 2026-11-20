# Security, privacy, and rights boundary

- Inputs may include faces, voices, private footage, fictional artwork, or proprietary material. Never publish or expose them to public demos/repositories by default.
- Current remote GitHub repository intended PRIVATE. Keep user-provided reference media private, even if source code is eventually published.
- Store only small, nonsensitive fixtures in Git. `media/`, `outputs/`, `.env`, cache and model-weight filenames are ignored; inspect staged file list for surprises before commit.
- Require affirmative user opt-in before transmitting an image/voice/video to a new processing provider, and verify provider retention/public sharing.
- For real people's voices and likenesses, restrict workflows to permitted source media and honest attribution; offer disclosure labeling for synthetic/synced footage.
- Secret tokens belong in runtime environment/config, never logs, docs, CLI arguments persisted in Git, or Drive manifests.
- Avoid arbitrary subprocess strings from user input, limit file paths and upload size, validate media headers and extension/MIME, guard against decompression bombs, SSRF, and malformed uploads.
- Use job-specific temp directories with explicit time/size ceilings and scoped cleanup. A successful cloud upload is not itself proof of recoverable media; read back metadata/hash when API supports it.
- External dependencies: inspect license and download origin before integration; don't vendor weights or paid SDKs by convenience.
