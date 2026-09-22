#!/usr/bin/env python3
"""Compare local inference with 32 outcome-independent corpus vectors.

Use the same environment as the upstream server. Success requires close numerical
agreement; save the JSON report before enabling the local selector comparator.
"""
import hashlib
import json
import os
from pathlib import Path
import sys

import numpy as np
import torch
from sentence_transformers import SentenceTransformer

root = Path(__file__).resolve().parent
upstream = Path(os.environ["JEVBENCH_PREMISE_SERVER"]) / "app"
sys.path.insert(0, str(upstream))
# Import initializes the pinned corpus and its exact upstream filtering/order.
from retrieve import corpus, PRECOMPUTED_EMBEDDINGS_PATH

artifact = json.loads((root / "provenance.example.json").read_text())["model"]
torch.set_num_threads(2)
torch.set_num_interop_threads(1)
model = SentenceTransformer(artifact["id"], revision=artifact["revision"],
                            device="cpu", trust_remote_code=False)
model.float().eval()
indices = np.linspace(0, len(corpus.premises) - 1, 32, dtype=int)
texts = [corpus.premises[int(i)].to_string() for i in indices]
with torch.inference_mode():
    actual = model.encode(texts, batch_size=8, show_progress_bar=False,
                          convert_to_numpy=True, normalize_embeddings=True)
expected = np.load(PRECOMPUTED_EMBEDDINGS_PATH, mmap_mode="r")[indices]
cosines = np.sum(actual * expected, axis=1) / (
    np.linalg.norm(actual, axis=1) * np.linalg.norm(expected, axis=1))
max_error = float(np.max(np.abs(actual - expected)))
minimum_cosine = float(np.min(cosines))
report = {"model": artifact, "indices": indices.tolist(),
          "maxAbsoluteError": max_error, "minimumCosine": minimum_cosine,
          "corpusSize": len(corpus.premises), "device": "cpu", "dtype": "float32",
          "corpus": json.loads((root / "provenance.example.json").read_text())["corpus"],
          "cpuEmbedSha256": hashlib.sha256((root / "cpu_embed.py").read_bytes()).hexdigest(),
          "passed": minimum_cosine >= 0.99999 and max_error <= 0.0001}
Path(os.environ["JEVBENCH_EMBED_VALIDATION"]).write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
sys.exit(0 if report["passed"] else 1)
