# submission-not-compression
## Note  “Compression that wins” and “Submission that wins” are not the same.  Stopped at the point where the latter was achievable.

## Dev Log — 2026-04-03

Parameter Golf (16MB track) に対して独自アプローチを試行。

* 3-bit centered quantization
* bit-plane decomposition (p2 → p1 → p0)
* LZMA dictionary optimization via stream structuring
* strict alignment & deterministic packing

ローカル検証では再現性・整合性ともに確認済み。

ただし、外部計算リソース（H100 × n）の確保が間に合わず、
最終評価パイプラインを実行できないため、ここで一旦停止。

設計自体は「提出可能な状態」まで到達。

今後再開するかは未定。
