from dataclasses import dataclass


@dataclass(frozen=True)
class Source:
    organization: str
    url: str


CATEGORIES = {
    "academic": "Centros académicos",
    "big_tech": "Laboratorios de big tech",
    "papers": "Papers",
    "media": "Medios y newsletters",
}


SOURCES: dict[str, list[Source]] = {
    "academic": [
        Source("Stanford HAI", "https://hai.stanford.edu/news"),
        Source("MIT News (AI)", "https://news.mit.edu/topic/artificial-intelligence2"),
        Source("Berkeley BAIR", "https://bair.berkeley.edu/blog/"),
        Source("CMU Machine Learning", "https://blog.ml.cmu.edu/"),
        Source("Oxford Internet Institute", "https://www.oii.ox.ac.uk/news-events/"),
        Source("ETH Zürich AI Center", "https://ai.ethz.ch/news.html"),
    ],
    "big_tech": [
        Source("OpenAI", "https://openai.com/news/"),
        Source("Anthropic", "https://www.anthropic.com/news"),
        Source("Google DeepMind", "https://deepmind.google/discover/blog/"),
        Source("Meta AI", "https://ai.meta.com/blog/"),
        Source("Microsoft Research", "https://www.microsoft.com/en-us/research/blog/"),
        Source("NVIDIA Research", "https://blogs.nvidia.com/blog/category/deep-learning/"),
    ],
    "papers": [
        Source("arXiv cs.AI", "https://arxiv.org/list/cs.AI/recent"),
        Source("arXiv cs.LG", "https://arxiv.org/list/cs.LG/recent"),
        Source("Hugging Face Daily Papers", "https://huggingface.co/papers"),
    ],
    "media": [
        Source("The Batch (DeepLearning.AI)", "https://www.deeplearning.ai/the-batch/"),
        Source("Import AI", "https://jack-clark.net/"),
        Source("MIT Technology Review — AI", "https://www.technologyreview.com/topic/artificial-intelligence/"),
        Source("The Verge — AI", "https://www.theverge.com/ai-artificial-intelligence"),
    ],
}


def render_sources_for_prompt() -> str:
    lines = []
    for key, sources in SOURCES.items():
        lines.append(f"### {CATEGORIES[key]} (category id: `{key}`)")
        for s in sources:
            lines.append(f"- {s.organization}: {s.url}")
        lines.append("")
    return "\n".join(lines).rstrip()
