import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import streamlit as st
import pickle
import os
from functools import lru_cache

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
# (2) 캐시 파일 관리
# ======================
def save_data(data, filepath):
    """데이터를 파일로 저장합니다."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'wb') as f:
        pickle.dump(data, f)
    print(f"데이터가 {filepath}에 저장되었습니다.")

def load_data(filepath):
    """저장된 데이터를 로드합니다."""
    if os.path.exists(filepath):
        try:
            with open(filepath, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            print(f"파일 로드 실패: {e}")
            return None
    return None

# ======================
# (3) TF-IDF 전처리
# ======================
@st.cache_data
def prepare_tfidf_data(country_dfs, force_rebuild=False):
    """TF-IDF 행렬과 관련 데이터를 전처리하고 캐시합니다."""
    cache_file = './data/tfidf_data.pkl'
    
    # 캐시된 파일이 있고 강제 재빌드가 아니면 로드
    if not force_rebuild:
        cached_data = load_data(cache_file)
        if cached_data is not None:
            return cached_data['tfidf_transformer'], cached_data['tfidf_matrix'], cached_data['counts_df']
    
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
    
    # 결과 저장
    save_data({
        'tfidf_transformer': tfidf_transformer,
        'tfidf_matrix': tfidf_matrix,
        'counts_df': counts_df
    }, cache_file)
    
    return tfidf_transformer, tfidf_matrix, counts_df

# ======================
# (4) 임베딩 모델 - 지연 로딩
# ======================
@st.cache_resource  # 모델은 cache_resource 사용
def load_embedding_model():
    """임베딩 모델을 로드합니다. (지연 로딩)"""
    try:
        model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
        # print("임베딩 모델 로드 완료")
        return model
    except Exception as e:
        st.error(f"임베딩 모델 로드 실패: {e}")
        return None

@st.cache_data
def prepare_embeddings(_model, keywords):
    """키워드 임베딩을 생성하고 캐시합니다."""
    if _model is None:
        return {}
    
    cache_file = './data/keyword_embeddings.pkl'
    
    # 캐시된 임베딩 로드 시도
    cached_embeddings = load_data(cache_file)
    if cached_embeddings is not None:
        # 새로운 키워드가 있는지 확인
        missing_keywords = [kw for kw in keywords if kw not in cached_embeddings]
        if not missing_keywords:
            # print("캐시된 임베딩 사용")
            return {kw: cached_embeddings[kw] for kw in keywords}
        
        # 새로운 키워드만 임베딩 계산
        print(f"새로운 키워드 {len(missing_keywords)}개 임베딩 계산 중...")
        new_embeddings = {kw: _model.encode(kw) for kw in missing_keywords}
        
        # 기존 임베딩과 합치기
        all_embeddings = {**cached_embeddings, **new_embeddings}
        
        # 업데이트된 임베딩 저장
        save_data(all_embeddings, cache_file)
        
        return {kw: all_embeddings[kw] for kw in keywords}
    
    # 첫 실행: 모든 임베딩 계산
    # print(f"모든 키워드 {len(keywords)}개 임베딩 계산 중...")
    embeddings = {kw: _model.encode(kw) for kw in keywords}
    
    # 임베딩 저장
    save_data(embeddings, cache_file)
    
    return embeddings

# ======================
# (5) 다국어 매핑
# ======================
@lru_cache(maxsize=1000)  # 자주 사용되는 키워드 캐싱
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
    if model is None:  # 임베딩 모델이 없으면 기본 매핑만
        norm_kw = normalize_keyword(input_kw)
        return norm_kw if norm_kw in counts_df.columns else None
    
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
# (6) 최적화된 추천 함수들 (클래스 대신 함수 사용)
# ======================
def create_keyword_mapping(keywords):
    """키워드 인덱스 매핑을 생성합니다."""
    return {kw: idx for idx, kw in enumerate(keywords)}

def create_input_vector(mapped_keywords, keyword_to_idx, total_keywords):
    """입력 키워드들로부터 벡터를 생성합니다."""
    input_vec = np.zeros(total_keywords, dtype=float)
    for kw in mapped_keywords:
        if kw in keyword_to_idx:
            idx = keyword_to_idx[kw]
            input_vec[idx] += 1.0
    return input_vec

def recommend_countries_fast(input_keywords, tfidf_transformer, tfidf_matrix, 
                           counts_df, model, keyword_embeddings, 
                           keyword_to_idx=None, top_n=3, return_scores=False):
    """최적화된 국가 추천 함수"""
    
    # 키워드 매핑이 없으면 생성
    if keyword_to_idx is None:
        keyword_to_idx = create_keyword_mapping(counts_df.columns.tolist())
    
    # 키워드 매핑
    mapped_keywords = []
    for kw in input_keywords:
        mapped_kw = map_or_embed(kw, model, keyword_embeddings, counts_df)
        if mapped_kw:
            mapped_keywords.append(mapped_kw)

    if not mapped_keywords:
        return []

    # 입력 벡터 생성
    input_vec = create_input_vector(mapped_keywords, keyword_to_idx, len(counts_df.columns))
    
    # TF-IDF 변환 (이미 fit된 transformer 사용)
    input_tfidf = tfidf_transformer.transform(input_vec.reshape(1, -1))
    
    # 코사인 유사도 계산 (사전 계산된 tfidf_matrix와 비교)
    sims = cosine_similarity(input_tfidf, tfidf_matrix).flatten()
    
    # 결과 정렬
    countries = counts_df.index.tolist()
    ranked = sorted(zip(countries, sims), key=lambda x: x[1], reverse=True)

    if return_scores:
        return ranked[:top_n]
    else:
        return [r[0] for r in ranked[:top_n]]

# 기존 함수와 호환성을 위한 래퍼 함수
def recommend_countries(input_keywords, tfidf_transformer, tfidf_matrix, 
                       counts_df, model, keyword_embeddings, top_n=3, return_scores=False):
    """기존 API와 호환되는 추천 함수"""
    return recommend_countries_fast(input_keywords, tfidf_transformer, tfidf_matrix, 
                                   counts_df, model, keyword_embeddings, 
                                   None, top_n, return_scores)

# ======================
# (7) 통합 초기화 함수 - pickle 가능하도록 수정
# ======================
def initialize_recommender_system(force_rebuild=False):
    """추천 시스템을 초기화합니다. (pickle 가능한 버전)"""
    # 데이터 로딩
    country_dfs = load_cosmetic_data()
    
    # TF-IDF 준비 (캐시 활용)
    tfidf_transformer, tfidf_matrix, counts_df = prepare_tfidf_data(
        country_dfs, force_rebuild=force_rebuild
    )
    
    # 임베딩 모델 및 키워드 임베딩 준비
    model = load_embedding_model()
    keyword_embeddings = prepare_embeddings(model, counts_df.columns.tolist())
    
    # 키워드 매핑 생성 (성능 향상용)
    keyword_to_idx = create_keyword_mapping(counts_df.columns.tolist())
    
    return {
        'tfidf_transformer': tfidf_transformer,
        'tfidf_matrix': tfidf_matrix,
        'counts_df': counts_df,
        'model': model,
        'keyword_embeddings': keyword_embeddings,
        'keyword_to_idx': keyword_to_idx,  # 클래스 대신 매핑 딕셔너리
        'countries': counts_df.index.tolist(),
        'keywords': counts_df.columns.tolist()
    }

# ======================
# (8) 빠른 추천을 위한 헬퍼 함수
# ======================
def fast_recommend(recommender_data, input_keywords, top_n=3, return_scores=False):
    """빠른 추천을 위한 헬퍼 함수"""
    return recommend_countries_fast(
        input_keywords,
        recommender_data['tfidf_transformer'],
        recommender_data['tfidf_matrix'],
        recommender_data['counts_df'],
        recommender_data['model'],
        recommender_data['keyword_embeddings'],
        recommender_data['keyword_to_idx'],  # 미리 생성된 매핑 사용
        top_n,
        return_scores
    )

# ======================
# (9) 사용 예시
# ======================
def example_usage():
    """사용 예시"""
    # 시스템 초기화
    system = initialize_recommender_system()
    
    # 빠른 추천 실행
    input_keywords = ['vegan', 'organic', 'natural']
    recommendations = fast_recommend(system, input_keywords, top_n=5, return_scores=True)
    
    print("추천 결과:")
    for country, score in recommendations:
        print(f"{country}: {score:.4f}")

# TF-IDF 데이터 강제 재빌드가 필요한 경우
def rebuild_tfidf_cache():
    """TF-IDF 캐시를 강제로 재빌드합니다."""
    system = initialize_recommender_system(force_rebuild=True)
    return system