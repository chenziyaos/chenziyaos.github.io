#!/usr/bin/env python3
"""Generate the showcase index.html from local clones of the series repos.

Usage: python3 tools/build.py <dir-containing-zero-to-*-and-nginx-devops-clones>

Chapter links point to each repo's online edition (MkDocs on GitHub Pages,
https://zyaochen.github.io/<repo>/<chapter>/), not to the Markdown on GitHub.
"""

import sys
from html import escape
from pathlib import Path

if len(sys.argv) != 2:
    sys.exit(__doc__)
ROOT = Path(sys.argv[1]).resolve()
TOOLS = Path(__file__).resolve().parent
OUT = TOOLS.parent
GH = "https://github.com/zyaochen"
COLAB = "https://colab.research.google.com/github/zyaochen"
SITE = "https://zyaochen.github.io"

SERIES = [
    {
        "repo": "zero-to-llm",
        "name": "从零掌握大模型",
        "wide": True,
        "desc": "从矩阵乘法一路讲到推理服务、RAG、Agent 和工程交付，七层由浅入深。每个技术决策都落到效果、显存、时延、成本四笔账上算清楚；正文里的表格和结论都来自代码的真实输出。",
        "book": "{n} 篇正文 + 1 篇总览（ZTL-00）",
        "code": "{ex} 段可运行代码，<code>tools/verify.py</code> 逐段运行并和正文贴出的输出逐字核对",
        "meta": [
            (
                "运行环境",
                "只要 CPU；Python ≥ 3.10，部分篇要 PyTorch CPU 版，其余只要 NumPy 或标准库",
            ),
            ("注意", "后半部分案例里的准确率、时延、成本读数是示意，不是实测，正文已标明"),
        ],
        "btn3": (
            "看核对脚本",
            "https://github.com/zyaochen/zero-to-llm/blob/main/tools/verify.py",
        ),
    },
    {
        "repo": "zero-to-vllm",
        "name": "从 0 开始 vLLM",
        "desc": "按章拆 vLLM：显存账本、调度与抢占、Paged KV、前缀缓存、PD 分离、LoRA，再到 DeepSeek / Qwen 部署实战和 Embedding / Rerank 服务。",
        "meta": [
            ("版本基线", "vLLM v0.32.0，主干提交 <code>0d6f92a</code>（2026-10-29）"),
            (
                "运行环境",
                "<code>sim_*.py</code> 在 CPU 上跑（Python ≥ 3.11）；<code>gpu_*.py</code> 和起服脚本要 GPU",
            ),
        ],
    },
    {
        "repo": "zero-to-sglang",
        "name": "从 0 开始 SGLang",
        "desc": "按章拆 SGLang：内存池与页表、RadixAttention、overlap 调度与 CUDA Graph、HiCache 三层 KV 缓存、PD 分离、Embedding / Rerank 服务。",
        "meta": [
            ("版本基线", "SGLang v0.5.22，主干提交 <code>8fabf5e</code>（2026-10-28）"),
            ("运行环境", "CPU 练习需要 Python ≥ 3.10 + numpy"),
        ],
    },
    {
        "repo": "zero-to-llama",
        "name": "从 0 开始 llama.cpp",
        "desc": "按章拆 llama.cpp：GGUF / GGML 结构、内存与带宽预测器、量化对照、CPU 调优、投机解码。实测数字来自一台 4 vCPU / 8 GB、没有 GPU 的机器。",
        "meta": [
            (
                "版本基线",
                "llama.cpp v0.8.0，主干提交 <code>0ec4027</code>（2026-10-30），ggml 0.28.0",
            ),
            ("运行环境", "Python ≥ 3.9 标准库，不装 <code>gguf</code> 包也能读 GGUF"),
        ],
    },
    {
        "repo": "zero-to-gpu",
        "name": "从 0 开始 GPU 优化",
        "desc": "从硬件到集群：性能账本、访存与 GEMM、Tensor Core、PCIe / NVLink / RDMA、NCCL、K8s 调度、可靠性、MoE 专家并行和推理系统。",
        "meta": [
            ("版本基线", "CUDA 13.4 Update 2，PyTorch 2.15.0，NCCL 2.32.3"),
            (
                "运行环境",
                "<code>sim_*.py</code> 在 CPU 上跑（Python ≥ 3.10 + numpy）；<code>*.cu</code> 和 <code>gpu_*.py</code> 要 GPU",
            ),
        ],
    },
]

NGINX = {
    "repo": "nginx-devops",
    "name": "nginx 运维篇与开发篇",
    "wide": True,
    "branch": "master",
    "folders": [("ops", "运维篇"), ("dev", "开发篇")],
    "desc": "按 nginx 1.31.9 源码讲清配置在源码里实际怎么生效：运维篇从安装、路由、反向代理、负载均衡、缓存、限流讲到四层代理和排障，开发篇从源码地图、内存池、事件循环、HTTP 阶段讲到自己写一个模块。",
    "book": "{n} 章：运维篇 13 章、开发篇 10 章",
    "code": "{labs} 个实验目录，每章一个；<code>tools/verify_labs.sh</code> 运行实验并和正文引用的输出逐行比对",
    "meta": [
        ("版本基线", "nginx 1.31.9（mainline，2026-11-18），引用的源码片段逐行核对过"),
        (
            "运行环境",
            "C 编译器、make、OpenSSL 3 和 PCRE2；实验只在 macOS arm64 上跑过，不支持 Windows",
        ),
    ],
    "btn3": ("看实验", "https://github.com/zyaochen/nginx-devops/tree/master/labs"),
}


def chapters(s):
    """Return [(path, number, stage, title)] parsed from the chapter headings.

    zero-to-*: book/NN-*.md with "PREFIX-NN｜stage｜title" (path is relative to book/).
    folders:   <folder>/NN-*.md with "part NN｜title" (stage is the folder's name).
    """
    rows = []
    if "folders" in s:
        for folder, stage in s["folders"]:
            for md in sorted((ROOT / s["repo"] / folder).glob("[0-9]*.md")):
                head = md.read_text(encoding="utf-8").splitlines()[0].lstrip("# ").strip()
                title = head.split("｜", 1)[1].split("：")[0]
                rows.append((f"{folder}/{md.stem}", md.stem.split("-")[0], stage, title))
        return rows
    for md in sorted((ROOT / s["repo"] / "book").glob("[0-9]*.md")):
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
    site = f"{SITE}/{repo}/"
    rows = chapters(s)
    notebooks = {p.stem for p in (ROOT / repo / "colab").glob("*.ipynb")}
    code_dirs = [p for p in (ROOT / repo).glob("[0-9]*") if p.is_dir()]
    if "code" in s:
        code = s["code"].format(
            ex=len(list((ROOT / repo).glob("[0-9]*/ex*.py"))),
            labs=len([p for p in (ROOT / repo / "labs").glob("*-*") if p.is_dir()]),
        )
    else:
        code = f"{len(code_dirs)} 个章节目录，{len(notebooks)} 个 Colab notebook"
    book = s.get("book", "{n} 章").format(n=len(rows))
    meta = [("书稿", book), ("配套代码", code), *s["meta"]]
    meta_html = "".join(f"<li><span>{k}</span><span>{v}</span></li>" for k, v in meta)
    btn3_label, btn3_href = s.get(
        "btn3", ("在 Colab 打开第 2 章", f"{COLAB}/{repo}/blob/main/colab/02-ledger.ipynb")
    )
    wide = " wide" if s.get("wide") else ""
    items = []
    for stem, no, stage, title in rows:
        link = f'<a href="{site}{stem}/">{escape(title)}</a>'
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
      <article class="card series{wide}">
        <h3><a href="{GH}/{repo}">{repo}</a> <small>{s["name"]}</small></h3>
        <p class="desc">{s["desc"]}</p>
        <ul class="tags">{tags}</ul>
        <ul class="meta">{meta_html}</ul>
        <div class="btns">
          <a class="btn primary" href="{site}">在线阅读</a>
          <a class="btn" href="{GH}/{repo}">配套代码</a>
          <a class="btn" href="{btn3_href}">{btn3_label}</a>
        </div>
        <details>
          <summary>章节目录（{len(rows)} 章）</summary>
          <ol class="chapters">
            {"".join(items)}
          </ol>
        </details>
      </article>"""


def totals():
    book = sum(len(chapters(s)) for s in [*SERIES, NGINX])
    nb = sum(len(list((ROOT / s["repo"] / "colab").glob("*.ipynb"))) for s in SERIES)
    return len(SERIES), book, nb


def main():
    n, book, nb = totals()
    cards = "".join(series_card(s) for s in SERIES)
    tpl = (TOOLS / "index.tpl.html").read_text(encoding="utf-8")
    html = (
        tpl.replace("{{SERIES_CARDS}}", cards)
        .replace("{{NGINX_CARD}}", series_card(NGINX))
        .replace("{{BOOK_TOTAL}}", str(book))
        .replace("{{NB_TOTAL}}", str(nb))
        .replace("{{SERIES_TOTAL}}", str(n))
    )
    (OUT / "index.html").write_text(html, encoding="utf-8")
    print(f"index.html written: {book} chapters, {nb} notebooks")


if __name__ == "__main__":
    main()
