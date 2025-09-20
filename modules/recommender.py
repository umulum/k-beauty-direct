import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import streamlit as st

# ======================
# (1) 데이터 로딩 - 캐시 적용
# ======================
@st.cache_data
def load_cosmetic_data():
    """엑셀 데이터를 로드하고 캐시합니다."""
    country_dfs = {}
    countries = ['usa', 'uae', 'vietnam', 'brazil', 'france', 'uk', 
                'india', 'japan', 'indonesia', 'turkey', 'thailand', 'china']
    
    for country in countries:
        try:
            df = pd.read_excel('./data/Cosmetic_trends_cleaned.xlsx', sheet_name=country)
            country_dfs[country] = df
        except Exception as e:
            st.warning(f"국가 {country} 데이터 로드 실패: {e}")
            continue
    
    return country_dfs

# ======================
# (2) 전처리 및 TF-IDF 변환 - 캐시 적용
# ======================
@st.cache_data
def prepare_tfidf_data(country_dfs):
    """TF-IDF 행렬과 관련 데이터를 전처리하고 캐시합니다."""
    
    def detect_keyword_and_freq_cols(df):
        freq_col = None
        for c in df.columns:
            if 'freq' in str(c).lower() or 'frequency' in str(c).lower() or 'count' in str(c).lower():
                freq_col = c
                break
        if freq_col is None:
            num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            if len(num_cols) > 0:
                freq_col = num_cols[0]
        
        keyword_col = None
        for c in df.columns:
            if c != freq_col:
                keyword_col = c
                break
        return keyword_col, freq_col

    # 국가별 키워드-빈도 dict 생성
    country_keyword_counts = {}
    for cname, df in country_dfs.items():
        kw_col, f_col = detect_keyword_and_freq_cols(df)
        tmp = {}
        for _, row in df.iterrows():
            kw = row[kw_col]
            freq = row[f_col]
            if pd.isna(kw):
                continue
            kw = str(kw).strip().lower()
            try:
                f = int(round(float(freq)))
            except:
                continue
            if f <= 0:
                continue
            tmp[kw] = tmp.get(kw, 0) + f
        country_keyword_counts[cname] = tmp

    # 국가 × 키워드 행렬 생성
    all_keywords = sorted({kw for d in country_keyword_counts.values() for kw in d.keys()})
    counts_df = pd.DataFrame(0, index=sorted(country_keyword_counts.keys()), 
                           columns=all_keywords, dtype=float)
    
    for cname, kwdict in country_keyword_counts.items():
        for kw, cnt in kwdict.items():
            counts_df.loc[cname, kw] = cnt

    # TF-IDF 변환
    tfidf_transformer = TfidfTransformer(norm='l2', use_idf=True, smooth_idf=True)
    tfidf_matrix = tfidf_transformer.fit_transform(counts_df.values)
    
    return tfidf_transformer, tfidf_matrix, counts_df

# ======================
# (3) 임베딩 모델 로딩 - 캐시 적용
# ======================
@st.cache_resource  # 모델은 cache_resource 사용
def load_embedding_model():
    """임베딩 모델을 로드합니다."""
    return SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

@st.cache_data
def prepare_embeddings(_model, keywords):
    """키워드 임베딩을 생성하고 캐시합니다."""
    return {kw: _model.encode(kw) for kw in keywords}

# ======================
# (4) 다국어 매핑
# ======================
def normalize_keyword(kw):
    """키워드를 정규화합니다."""
    keyword_aliases = {
        "비건": "vegan",
        "ヴィーガン": "vegan",
        "纯素": "vegan",
        "채식": "vegan",
        "ヴィーガンライフ": "vegan",
        "유기농": "organic",
        "オーガニック": "organic",
        "유해성분무첨가": "clean beauty"
    }
    kw = str(kw).strip().lower()
    return keyword_aliases.get(kw, kw)

def map_or_embed(input_kw, model, keyword_embeddings, counts_df, threshold=0.6):
    """키워드를 매핑하거나 임베딩으로 유사도를 계산합니다."""
    norm_kw = normalize_keyword(input_kw)
    if norm_kw in counts_df.columns:
        return norm_kw

    vec = model.encode(norm_kw)
    sims = {kw: cosine_similarity([vec], [emb])[0][0] 
            for kw, emb in keyword_embeddings.items()}
    best_kw, best_score = max(sims.items(), key=lambda x: x[1])
    
    if best_score >= threshold:
        return best_kw
    else:
        return None

# ======================
# (5) 추천 함수
# ======================
def recommend_countries(input_keywords, tfidf_transformer, tfidf_matrix, 
                       counts_df, model, keyword_embeddings, top_n=3, return_scores=False):
    """국가를 추천합니다."""
    mapped_keywords = []
    for kw in input_keywords:
        mapped_kw = map_or_embed(kw, model, keyword_embeddings, counts_df)
        if mapped_kw:
            mapped_keywords.append(mapped_kw)

    if not mapped_keywords:
        return []

    input_vec = np.zeros(len(counts_df.columns), dtype=float)
    for k in mapped_keywords:
        if k in counts_df.columns:
            idx = counts_df.columns.get_loc(k)
            input_vec[idx] += 1.0

    input_tfidf = tfidf_transformer.transform(input_vec.reshape(1, -1))
    sims = cosine_similarity(input_tfidf, tfidf_matrix).flatten()
    ranked = sorted(zip(counts_df.index.tolist(), sims), 
                   key=lambda x: x[1], reverse=True)

    if return_scores:
        return ranked[:top_n]
    else:
        return [r[0] for r in ranked[:top_n]]

# ======================
# (6) 통합 초기화 함수
# ======================
@st.cache_data
def initialize_recommender_system():
    """추천 시스템을 초기화합니다."""
    # 데이터 로딩
    country_dfs = load_cosmetic_data()
    
    # TF-IDF 준비
    tfidf_transformer, tfidf_matrix, counts_df = prepare_tfidf_data(country_dfs)
    
    # 임베딩 모델 및 키워드 임베딩 준비
    model = load_embedding_model()
    keyword_embeddings = prepare_embeddings(model, counts_df.columns.tolist())
    
    return {
        'tfidf_transformer': tfidf_transformer,
        'tfidf_matrix': tfidf_matrix,
        'counts_df': counts_df,
        'model': model,
        'keyword_embeddings': keyword_embeddings
    }