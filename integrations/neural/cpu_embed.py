#!/usr/bin/env python3
"""Local CPU embedding endpoint for the unmodified upstream premise server.

Uses the pinned SentenceTransformer (including its pooling and Normalize modules).
This replaces TEI execution only; corpus filtering and ranking stay upstream.
Validate against the pinned precomputed vectors before comparative benchmarks.
Run only as a child of the shared memory-limited benchmark process tree.
"""
import asyncio
import json
import os
from pathlib import Path

import torch
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import uvicorn

root = Path(__file__).resolve().parent
artifact = json.loads((root / "provenance.example.json").read_text())["model"]
torch.set_num_threads(2)
torch.set_num_interop_threads(1)
model = SentenceTransformer(artifact["id"], revision=artifact["revision"],
                            device="cpu", trust_remote_code=False)
model.float().eval()
app = FastAPI()
lock = asyncio.Lock()


class Inputs(BaseModel):
    inputs: list[str]
    truncate: bool = True


@app.get("/health")
def health():
    return {"model": artifact, "device": "cpu", "dtype": "float32",
            "maxSequenceLength": model.max_seq_length}


@app.post("/embed")
async def embed(request: Inputs):
    if not request.inputs or len(request.inputs) > 32:
        raise HTTPException(400, "Expected 1–32 input texts")
    if not request.truncate:
        raise HTTPException(400, "Only the upstream truncate=true protocol is supported")
    async with lock:
        with torch.inference_mode():
            vectors = model.encode(request.inputs, batch_size=8, show_progress_bar=False,
                                   convert_to_numpy=True, normalize_embeddings=True)
    return vectors.tolist()


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=int(os.environ.get("EMBED_PORT", "18081")), workers=1)
