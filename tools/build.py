#!/usr/bin/env python3
"""Generate the showcase index.html from local clones of the zero-to-* repos.

Usage: python3 tools/build.py <dir-containing-zero-to-*-clones>
"""
import sys
from html import escape
from pathlib import Path

if len(sys.argv) != 2:
    sys.exit(__doc__)
ROOT = Path(sys.argv[1]).resolve()
TOOLS = Path(__file__).resolve().parent
OUT = TOOLS.parent
GH = "https://github.com/chenziyaos"
COLAB = "https://colab.research.google.com/github/chenziyaos"

SERIES = [
    {
        "repo": "zero-to-vllm",
        "name": "从 0 开始 vLLM",
        "desc": "按章拆 vLLM：显存账本、调度与抢占、Paged KV、前缀缓存、PD 分离、LoRA，再到 DeepSeek / Qwen 部署实战和 Embedding / Rerank 服务。",
        "baseline": "vLLM v0.32.0，主干提交 <code>0d6f92a</code>（2026-10-29）",
        "runtime": "<code>sim_*.py</code> 在 CPU 上跑（Python ≥ 3.11）；<code>gpu_*.py</code> 和起服脚本要 GPU",
    },
    {
        "repo": "zero-to-sglang",
        "name": "从 0 开始 SGLang",
        "desc": "按章拆 SGLang：内存池与页表、RadixAttention、overlap 调度与 CUDA Graph、HiCache 三层 KV 缓存、PD 分离、Embedding / Rerank 服务。",
        "baseline": "SGLang v0.5.22，主干提交 <code>8fabf5e</code>（2026-10-28）",
        "runtime": "CPU 练习需要 Python ≥ 3.10 + numpy",
    },
    {
        "repo": "zero-to-llama",
        "name": "从 0 开始 llama.cpp",
        "desc": "按章拆 llama.cpp：GGUF / GGML 结构、内存与带宽预测器、量化对照、CPU 调优、投机解码。实测数字来自一台 4 vCPU / 8 GB、没有 GPU 的机器。",
        "baseline": "llama.cpp v0.8.0，主干提交 <code>0ec4027</code>（2026-10-30），ggml 0.28.0",
        "runtime": "Python ≥ 3.9 标准库，不装 <code>gguf</code> 包也能读 GGUF",
    },
    {
        "repo": "zero-to-gpu",
        "name": "从 0 开始 GPU 优化",
        "desc": "从硬件到集群：性能账本、访存与 GEMM、Tensor Core、PCIe / NVLink / RDMA、NCCL、K8s 调度、可靠性、MoE 专家并行和推理系统。",
        "baseline": "CUDA 13.4 Update 2，PyTorch 2.15.0，NCCL 2.32.3",
        "runtime": "<code>sim_*.py</code> 在 CPU 上跑（Python ≥ 3.10 + numpy）；<code>*.cu</code> 和 <code>gpu_*.py</code> 要 GPU",
    },
]


def chapters(repo):
    """Return [(stem, number, stage, title)] parsed from book/NN-*.md headings."""
    rows = []
    for md in sorted((ROOT / repo / "book").glob("[0-9]*.md")):
        head = md.read_text(encoding="utf-8").splitlines()[0].lstrip("# ").strip()
        parts = head.split("｜")
        if len(parts) != 3:
            raise ValueError(f"unexpected heading in {md}: {head!r}")
        rows.append((md.stem, md.stem.split("-")[0], parts[1], parts[2]))
    return rows


def stages(rows):
    seen = []
    for _, _, stage, _ in rows:
        if stage not in seen:
            seen.append(stage)
    return seen


def series_card(s):
    repo = s["repo"]
    rows = chapters(repo)
    notebooks = {p.stem for p in (ROOT / repo / "colab").glob("*.ipynb")}
    code_dirs = [p for p in (ROOT / repo).glob("[0-9]*") if p.is_dir()]
    items = []
    for stem, no, stage, title in rows:
        link = f'<a href="{GH}/{repo}/blob/main/book/{stem}.md">{escape(title)}</a>'
        colab = (
            f'<a class="colab" href="{COLAB}/{repo}/blob/main/colab/{stem}.ipynb">Colab</a>'
            if stem in notebooks
            else ""
        )
        items.append(
            f'<li><span class="no">{no}</span><span class="stage">{escape(stage)}</span>'
            f'<span class="t">{link}</span>{colab}</li>'
        )
    tags = "".join(f"<li>{escape(t)}</li>" for t in stages(rows))
    return f"""
      <article class="card series">
        <h3><a href="{GH}/{repo}">{repo}</a></h3>
        <p class="desc">{s["desc"]}</p>
        <ul class="tags">{tags}</ul>
        <ul class="meta">
          <li><span>书稿</span><span>{len(rows)} 章</span></li>
          <li><span>配套代码</span><span>{len(code_dirs)} 个章节目录，{len(notebooks)} 个 Colab notebook</span></li>
          <li><span>版本基线</span><span>{s["baseline"]}</span></li>
          <li><span>运行环境</span><span>{s["runtime"]}</span></li>
        </ul>
        <div class="btns">
          <a class="btn primary" href="{GH}/{repo}/blob/main/book/README.md">读书稿</a>
          <a class="btn" href="{GH}/{repo}">配套代码</a>
          <a class="btn" href="{COLAB}/{repo}/blob/main/colab/02-ledger.ipynb">在 Colab 打开第 2 章</a>
        </div>
        <details>
          <summary>章节目录（{len(rows)} 章）</summary>
          <ol class="chapters">
            {"".join(items)}
          </ol>
        </details>
      </article>"""


def totals():
    book = sum(len(chapters(s["repo"])) for s in SERIES)
    nb = sum(len(list((ROOT / s["repo"] / "colab").glob("*.ipynb"))) for s in SERIES)
    return book, nb


def main():
    book, nb = totals()
    cards = "".join(series_card(s) for s in SERIES)
    tpl = (TOOLS / "index.tpl.html").read_text(encoding="utf-8")
    html = (
        tpl.replace("{{SERIES_CARDS}}", cards)
        .replace("{{BOOK_TOTAL}}", str(book))
        .replace("{{NB_TOTAL}}", str(nb))
    )
    (OUT / "index.html").write_text(html, encoding="utf-8")
    print(f"index.html written: {book} chapters, {nb} notebooks")


if __name__ == "__main__":
    main()
