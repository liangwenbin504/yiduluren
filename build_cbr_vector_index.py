# -*- coding: utf-8 -*-
"""CBR 向量索引构建器
================================================================
从 data/longmarch_feature_vectors.json (218案) + data/rzhy_feature_vectors.json (529案)
提取每案的 duanyu(断语) + keti(课体) + sanchuan(三传) 文本，
用 NgramVectorizer 构建 n-gram TF-IDF 向量索引，
输出到 data/vector_store/cbr_vector_index.json，供 CaseLibrary 文本检索通道使用。
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine.vector_knowledge_base import VectorKnowledgeBase

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, 'data')
LONGMARCH_FILE = os.path.join(DATA, 'longmarch_feature_vectors.json')
RZHY_FILE = os.path.join(DATA, 'rzhy_feature_vectors.json')
OUT_DIR = os.path.join(DATA, 'vector_store')
OUT_FILE = os.path.join(OUT_DIR, 'cbr_vector_index.json')


def _build_text(case: dict) -> str:
    """从案例构建检索文本：断语 + 课体 + 三传 + 占类"""
    parts = []
    duanyu = case.get('duanyu', '') or case.get('interpretation', '') or ''
    if duanyu:
        parts.append(duanyu[:500])  # 截断长文本
    keti = case.get('features', {}).get('keti', [])
    if keti:
        parts.append(''.join(keti))
    sc = case.get('sanchuan', [])
    if sc:
        parts.append(''.join(str(x) for x in sc))
    zhanlei = case.get('zhanlei', '') or case.get('question', '')
    if zhanlei:
        parts.append(zhanlei)
    return ' '.join(parts)


def main():
    # 1. 加载 747 案
    docs = []
    for fpath in [LONGMARCH_FILE, RZHY_FILE]:
        if os.path.exists(fpath):
            with open(fpath, 'r', encoding='utf-8') as f:
                d = json.load(f)
            for c in d.get('cases', []):
                text = _build_text(c)
                if text.strip():
                    docs.append({
                        'id': c.get('case_id', ''),
                        'source': c.get('source', ''),
                        'text': text,
                        'zhanlei': c.get('zhanlei', ''),
                        'duanyu': (c.get('duanyu', '') or '')[:500],
                        'sanchuan': c.get('sanchuan', []),
                        'keti': c.get('features', {}).get('keti', []),
                    })
    print(f"Loaded {len(docs)} cases for vector index")

    # 2. 构建向量索引
    os.makedirs(OUT_DIR, exist_ok=True)
    vkb = VectorKnowledgeBase(persist_dir=OUT_DIR)

    # 直接用 add_documents，传入自定义 text_fields
    # VectorKnowledgeBase.add_documents 期望字段名 "原文"/"预测事情"/"实际事情"
    # 我们改用直接构建的方式
    vkb.documents = docs
    vkb.metadata = [{'id': d['id'], 'text': d['text'], 'zhanshi': d['zhanlei']} for d in docs]
    texts = [m['text'] for m in vkb.metadata]
    vkb.embeddings = vkb.vectorizer.fit_transform(texts)
    print(f"Vector index built: {vkb.embeddings.shape}")

    # 3. 保存
    vkb.save(OUT_FILE)
    sz = os.path.getsize(OUT_FILE)
    print(f"Saved to {OUT_FILE} ({sz/1024:.1f} KB)")

    # 4. 测试查询
    test_q = "求财见财得财"
    results = vkb.query(test_q, top_k=3)
    print(f"\nTest query '{test_q}':")
    for r in results:
        c = r['case']
        sim = r['similarity']
        print(f"  {sim:.3f}  {c['id']}  [{c['zhanlei']}]  {c['duanyu'][:60]}...")


if __name__ == '__main__':
    main()
