"""文本解析：把隐私政策切成可检索的段落/句子。

纯标准库实现，不调用任何外部服务，离线可用。
"""


def split_paragraphs(text):
    """按空行切分段落，过滤空段。"""
    paras = []
    for raw in text.split("\n"):
        p = raw.strip()
        if p:
            paras.append(p)
    return paras


def normalize(text):
    """统一小写用于子串匹配（中文不受大小写影响，英文匹配更稳健）。"""
    return text.lower()


def read_file(path):
    """读取隐私政策文本文件，返回 (text, error)。"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read(), None
    except OSError as e:
        return None, str(e)
