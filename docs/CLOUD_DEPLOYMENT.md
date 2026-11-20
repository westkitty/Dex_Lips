# Compute, hosting, and deployment gates

## Priority order

1. Test deterministic mouth-cue processing and MP4 export in an **already available disposable execution environment** with FFmpeg/Pillow/Rhubarb, not by adding weights or unknown dependencies to constrained Macs. `scripts/proof_smoke.py` establishes only external-cue compositing.
2. For browser delivery, prefer an offline-capable static frontend and a user-controlled export/worker boundary. Static Hugging Face Spaces are free, but **cannot execute Rhubarb/FFmpeg**. Browser-native media encoding/MP4 is not guaranteed; the UI must disclose unavailable exports rather than mislabel a preview.
3. A Gradio ZeroGPU Space is a **conditional** full-app hosting candidate for free personal accounts in good standing. Verify that account's actual eligibility, available slots, runtime quotas and CPU subprocess compatibility. Normal Gradio/Docker compute Space creation **requires a paid plan** despite CPU Basic listing an hourly hardware price of $0. Do not assume a free CPU Basic Gradio Space can be newly created.
4. Neural model adapters are further conditional on the user's actual ZeroGPU entitlement, free quota, model suitability and privacy. Skip without failure when a no-cost run cannot be established.
5. If free compute cannot be proved: keep deterministic offline cue edit/preview, allow explicit download of portable project data for a later eligible worker, and state MP4 export needs a verified no-cost execution environment. Do not automatically run local GPU compute or purchase cloud resources.

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

## Hosting price and eligibility source (reverified 2026-11-19)

Official Hugging Face Spaces overview, https://huggingface.co/docs/hub/spaces-overview : "Static Spaces are free for everyone. Gradio and Docker Spaces run on compute and require a paid plan to create ... Free personal accounts in good standing can still host up to 2 Gradio Spaces running on ZeroGPU." This supersedes older advice that free CPU Basic Gradio Spaces can be created by any free user. No account-specific eligibility test or deployment has occurred; `HOSTED_FREE_UNVERIFIED` remains the default.

## Implementation status 2026-11-19

The working editor runs locally and binds exclusively to `127.0.0.1`. No Space or paid runtime was created. Ordinary new Gradio/Docker Spaces require paid-plan eligibility even on $0/hour CPU Basic hardware; free ZeroGPU Gradio Spaces are conditional, not a universal CPU fallback. A static Space cannot execute the Python Rhubarb/FFmpeg backend. Treat both free hosted deployment and mobile browser access as unverified. See `README.md` and `docs/QQQ_PERFORMANCE_REPAIR_2026-11-19.md`.
