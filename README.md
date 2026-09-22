# MMAudio API — Python client

[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/) [![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE) [![Hosted on Synexa](https://img.shields.io/badge/hosted%20on-Synexa-6366f1.svg)](https://synexa.ai/explore/zsxkib/mmaudio?utm_source=github&utm_medium=ugc&utm_campaign=mmaudio-dev&utm_content=readme-badge&utm_term=tier-a)

MMAudio is the CVPR 2025 video-to-audio model from the University of Illinois and Sony AI that generates a soundtrack matched to what happens on screen, frame-accurately, from the video and a short text prompt. This package is a Python client for the MMAudio API hosted on Synexa: one `pip install` and a `run({"video": url, "prompt": ...})` call return the video with a generated audio track, with no weights or GPU on your side.

The client provides a blocking `run()` that waits for the output, a submit-and-poll mode, webhook delivery on completion and typed errors. Its only dependency is `httpx`. It is intended for video-generation pipelines whose clips come out silent, editing tools that need instant foley, and researchers who want MMAudio as a service rather than a local install.

> **Try it now:** [https://synexa.ai/explore/zsxkib/mmaudio](https://synexa.ai/explore/zsxkib/mmaudio?utm_source=github&utm_medium=ugc&utm_campaign=mmaudio-dev&utm_content=readme-top&utm_term=tier-a) — the hosted model behind this client. New accounts get a free trial credit.

## Contents

- [Why this client](#why-this-client)
- [Installation](#installation)
- [Quickstart](#quickstart)
- [Hosted models](#hosted-models)
- [Parameters](#parameters)
- [Advanced usage](#advanced-usage)
- [About MMAudio](#about-mmaudio)
- [Use cases](#use-cases)
- [FAQ](#faq)
- [License](#license)

## Why this client

- **Four checkpoints, not one.** A local MMAudio run needs the MMAudio weights, the Synchformer visual encoder, the CLIP text encoder and the audio VAE, all downloaded and version-matched. The hosted endpoint has them assembled; you call HTTPS.
- **No CUDA environment.** The reference implementation targets a CUDA GPU. With the hosted model your caller can be a web server, a CI job or a laptop without a discrete GPU.
- **No cold start on every clip.** Loading the encoders and the flow-matching model takes time on a fresh instance; the hosted deployment keeps them resident.
- **$0.01 per clip.** Billing is per prediction with nothing charged while idle; adding sound to a hundred videos costs one dollar.

## Installation

```bash
pip install git+https://github.com/mmaudio-dev/mmaudio-api.git
```

Then set your API key (create one at [synexa.ai](https://synexa.ai?utm_source=github&utm_medium=ugc&utm_campaign=mmaudio-dev&utm_content=readme-apikey&utm_term=tier-a)):

```bash
export SYNEXA_API_KEY="sk-..."
```

## Quickstart

```python
import mmaudio_api

output = mmaudio_api.run({
    "video": "https://example.com/input.png",
    "prompt": "galloping"
})
print(output)   # URL(s) of the generated result
```

Or with an explicit client:

```python
from mmaudio_api import Client

client = Client(api_key="sk-...")
output = client.run({"video": "https://example.com/input.png", "prompt": "galloping"})
```

## Hosted models

| Model | Category | What it does | Price / run |
|---|---|---|---|
| [`zsxkib/mmaudio`](https://synexa.ai/explore/zsxkib/mmaudio?utm_source=github&utm_medium=ugc&utm_campaign=mmaudio-dev&utm_content=readme-models&utm_term=tier-a) | video-to-audio | Add sound to video using the MMAudio V2 model. An advanced AI model that synthesizes high-quality audio from video content, enabling seamless video-to-audio transformation. | $0.01 |

The default model is **`zsxkib/mmaudio`**; pass `model="owner/name"` to `run()` to use another one from the table.

## Parameters

### `zsxkib/mmaudio`

| Field | Type | Required | Default | Range | Description |
|---|---|---|---|---|---|
| `seed` | integer | no | `random` | — | Random seed. Leave blank to randomize the seed |
| `video` | file | yes | `https://files.synexa.ai/models/zsxkib-mm…` | — | video file for video-to-audio generation |
| `prompt` | string | yes | `galloping` | — | Text prompt for generated audio |
| `duration` | number | no | `8` | 1, 10 | Duration of output in seconds |
| `num_steps` | number | no | `25` | 10, 50 | Number of inference steps |
| `cfg_strength` | number | no | `4.5` | 1, 10 | Guidance strength (CFG) |
| `negative_prompt` | string | no | `music` | — | Negative prompt to avoid certain sounds |

## Advanced usage

**Submit without blocking, then poll:**

```python
prediction = client.run(input, wait=False)      # returns immediately
prediction = client.wait(prediction, timeout=300)
print(prediction["output"])
```

**Webhook on completion:**

```python
client.run(input, wait=False, webhook="https://your-app.example/hooks/synexa")
```

**Errors:**

```python
from mmaudio_api import ModelError, PredictionTimeout

try:
    output = client.run(input)
except ModelError as e:
    print("failed:", e, e.prediction and e.prediction.get("id"))
except PredictionTimeout:
    print("still running — poll later")
```

Status values you will see on a prediction: `starting` → `processing` → `succeeded` | `failed`.

## About MMAudio

MMAudio is a video-to-audio synthesis model presented at CVPR 2025 in the paper *Taming Multimodal Joint Training for High-Quality Video-to-Audio Synthesis* by Ho Kei Cheng and colleagues at the University of Illinois Urbana-Champaign and Sony AI. Code and weights are published at [hkchengrex/MMAudio](https://github.com/hkchengrex/MMAudio). The model's contribution is training jointly on video-audio pairs and much larger text-audio datasets, so it learns a broad vocabulary of sounds from text data while learning timing from video.

Architecturally it is a flow-matching transformer over audio latents. Video frames are encoded by a visual encoder, text by CLIP, and a dedicated conditional synchronisation module (built on Synchformer features) aligns generated events such as footsteps, impacts and door slams to the exact frames where they occur. It produces 44.1 kHz audio in a few seconds per clip on a datacenter GPU. Released variants range from a small 16 kHz model to the large 44 kHz models; the hosted endpoint runs MMAudio V2, the updated large 44 kHz checkpoint.

The hosted `zsxkib/mmaudio` endpoint takes a `video` file and a `prompt` describing the desired sound (both required) and returns the video muxed with the generated track; `negative_prompt` suppresses sounds you do not want (music, speech, wind). MMAudio generates environmental sound and effects; it does not synthesise intelligible speech or produce a full musical score, and results are best when the prompt names the sounds concretely ("waves on gravel, distant gulls") rather than describing the scene visually.

The endpoint used by this client is `zsxkib/mmaudio`, which is the same MMAudio model released by its authors, packaged and served on Synexa. The weights and reference inference code are in the official repository if you would rather run it yourself.

**Official project:** https://github.com/hkchengrex/MMAudio

## Use cases

- **Sound for AI-generated video** — take a silent clip from a text-to-video model and call `run({"video": url, "prompt": "rain on a tin roof, thunder"})` to deliver a finished asset.
- **Automatic foley for product demos** — describe the mechanical sound ("keyboard clicks, laptop lid closing") and get effects timed to the on-screen action.
- **Ambience tracks for stock footage** — add matched environmental sound to B-roll shot without audio, using `negative_prompt="music, speech"` to keep the bed clean.
- **Rapid previews in an editing tool** — submit with `wait=False` and poll so the editor stays responsive while several candidate tracks render.
- **Game and animation prototyping** — generate placeholder effects for cutscenes and animatics so reviewers hear timing before a sound designer is involved.
- **Batch processing a media library** — send thousands of short clips with a `webhook` and store the returned URLs; at $0.01 a clip the cost is predictable.

## FAQ

**Is there an MMAudio API?**

The authors release MMAudio as open code and weights with a Gradio demo, not a hosted API. This package is a Python client for the `zsxkib/mmaudio` endpoint on Synexa, which serves the model behind an HTTPS API.

**How much does the MMAudio API cost?**

The hosted endpoint is billed at $0.01 per run. There is no hourly charge and nothing to pay while idle. New Synexa accounts receive a free trial credit.

**Can I run MMAudio without a GPU?**

Yes. With this client generation happens on Synexa's GPUs; your code needs only Python 3.8+ and `httpx`. Self-hosting is designed around a CUDA GPU and requires downloading the MMAudio, Synchformer, CLIP and VAE checkpoints.

**Does this client work with the hkchengrex/MMAudio repo or ComfyUI?**

No. It does not load local checkpoints or ComfyUI nodes; it is an HTTP client for the hosted endpoint. Use the official repository or its ComfyUI wrappers for offline inference or custom model variants.

**What input formats does it accept?**

`video` must be a publicly reachable video file URL (MP4 is the safe choice) and `prompt` a string; both are required. Optional fields are `negative_prompt` (string), `duration` (seconds), `num_steps` (integer), `cfg_strength` (number) and `seed` (integer). Output is a URL to the video with the generated audio track.

**Is this the official MMAudio SDK?**

No. This is an independent, MIT-licensed client and is not affiliated with the MMAudio authors, UIUC or Sony. The official project is at https://github.com/hkchengrex/MMAudio.

## Related

- [hkchengrex/MMAudio](https://github.com/hkchengrex/MMAudio) — official code, weights, paper and demo.
- [Synexa Python client](https://github.com/synexa-ai/synexa-python) — the general-purpose client for every model on the platform.
- [lightricks/ltx-2.5-pro](https://synexa.ai/explore/lightricks/ltx-2.5-pro) — image-to-video with its own synchronised audio, for clips that should be generated with sound from the start.
- [lightricks/ltx-2.5-audio-to-video](https://synexa.ai/explore/lightricks/ltx-2.5-audio-to-video) — the reverse direction: video timed to an existing audio track.
- [bytedance/seedvr2-upscale](https://synexa.ai/explore/bytedance/seedvr2-upscale) — restore frames before or after adding sound.

## License

MIT. This is an independent, community-maintained client and is not affiliated with or endorsed by the authors of MMAudio. Model weights and trademarks belong to their respective owners.


_Last reviewed: 2026-09-22_
