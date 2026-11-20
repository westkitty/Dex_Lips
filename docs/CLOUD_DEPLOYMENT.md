# Compute, hosting, and deployment gates

## Priority order

1. Browser deterministic renderer / 2D speech-cue preview where supported.
2. Hugging Face free-tier Gradio Space CPU execution for Rhubarb + FFmpeg, **only after verifying free entitlement and no billing**.
3. Hugging Face ZeroGPU inference for optional face-model adapters, **only after checking current account eligibility, queue, quota, model RAM, and zero-spend guarantee**.
4. No free quota or unsafe conditions -> WAIT/STOP, or manual rig-only fallback; never paid upgrade.

## Hard constraints

- No model-weight, dataset, or dependency-download staging on MacBook or Big Mac beyond tiny source files.
- No automatic public Space deployment of user-supplied artwork or private audio. Require explicit target/visibility and user approval for upload.
- If a public Space is unavoidable, use synthetic sample data only and do not persist or display user media; access to private source images needs a verified privacy-safe mechanism.
- No `gradio app` claim or ZeroGPU compatibility without actual runtime proof.
- No Google Colab neural deepfake compute (prohibited by provider policy).
- No surprise cloud credits; no pay-as-you-go billing; fail closed before any request requiring payment.
- Treat remote workspaces as ephemeral, clean temporary uploads, and never delete original source media before verified output/Drive receipt.

## Manual first proof

- Check account and Space creation eligibility without mutation.
- Check CPU Rhubarb/FFmpeg installation in a disposable environment with non-sensitive synthetic voice sample.
- Check model adapter supported input, run duration, GPU runtime, and disk/temp requirements if available for $0.
- Retrieve a short exported MP4, inspect codecs, duration, time alignment, and cleanup.
- Record limits and errors before automating deployment or scheduled work.
