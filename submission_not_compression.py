import torch
import numpy as np
import lzma
import struct


class SubmissionOrientedCompressor:
    """
    Public-safe version.
    Core idea: deterministic bit-plane packing + LZMA optimization.
    """

    def __init__(self, budget_bytes=16_000_000):
        self.BUDGET = budget_bytes

    @torch.no_grad()
    def build_artifact(self, weights: torch.Tensor):
        """
        Entry point.
        weights: flattened tensor (pre-selected / pre-processed externally)
        """

        # --- Placeholder quantization (intentionally simplified) ---
        # NOTE: real implementation uses more advanced scaling strategy
        scale = weights.abs().mean().clamp(min=1e-6)
        q = torch.round(weights / scale).clamp(-4, 3).to(torch.int8) + 4
        q = q.to(torch.uint8)

        # --- Alignment (deterministic) ---
        pad_len = (64 - (q.numel() % 64)) % 64
        if pad_len > 0:
            q = torch.cat([q, torch.zeros(pad_len, dtype=q.dtype)])

        q_blocks = q.view(-1, 64)

        # --- Bit-plane decomposition ---
        p0 = q_blocks & 1
        p1 = (q_blocks >> 1) & 1
        p2 = (q_blocks >> 2) & 1

        # --- Packing ---
        b0 = self._pack_8bit(p0)
        b1 = self._pack_8bit(p1)
        b2 = self._pack_8bit(p2)

        # --- Stream layout (important for compression efficiency) ---
        stream = torch.cat([
            b2.reshape(-1),
            b1.reshape(-1),
            b0.reshape(-1)
        ])

        payload = stream.cpu().numpy().tobytes()

        # --- Minimal header (self-describing) ---
        header = struct.pack("<Q", len(payload))

        compressed = lzma.compress(header + payload, preset=9)

        if len(compressed) > self.BUDGET:
            raise RuntimeError("Budget exceeded")

        return compressed

    def _pack_8bit(self, p: torch.Tensor):
        """
        Safe deterministic bit packing.
        [N, 64] -> [N, 8]
        """
        res = torch.zeros((p.shape[0], 8), dtype=torch.uint8, device=p.device)
        for i in range(8):
            res |= (p[:, i::8].to(torch.uint8) << i)
        return res
