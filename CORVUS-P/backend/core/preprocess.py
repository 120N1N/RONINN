import os
import uuid
import math
import re
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from backend.db.database import SessionLocal
from backend.db import models

class DatasetPreprocessor:
    @staticmethod
    def calculate_entropy(data_str: str) -> float:
        """Menghitung Shannon Entropy dari payload (Fase 1)."""
        if pd.isna(data_str) or not data_str:
            return 0.0
        data_str = str(data_str)
        prob = [float(data_str.count(c)) / len(data_str) for c in dict.fromkeys(list(data_str))]
        return -sum(p * math.log(p, 2) for p in prob)

    @staticmethod
    def map_labels(df: pd.DataFrame, label_col: str) -> pd.DataFrame:
        if label_col not in df.columns:
            df['label'] = 0
            return df
        def mapper(val):
            if pd.isna(val): return 0
            if str(val).lower().strip() in ['1', '1.0', 'true', 'malicious', 'attack', 'vuln', 'yes', 'danger']: return 1
            return 0
        df['label'] = df[label_col].apply(mapper)
        return df

    @staticmethod
    def extract_features(df: pd.DataFrame) -> pd.DataFrame:
        """
        Fase 1: Implementasi 7 Fitur Heuristik Kunci sesuai Laporan Bab 4.
        """
        processed = pd.DataFrame(index=df.index)
        processed['label'] = df['label'] if 'label' in df.columns else 0

        # Identifikasi kolom yang relevan
        payload_col = next((c for c in df.columns if c.lower() in ['payload', 'evidence', 'request', 'query', 'params']), None)
        resp_col = next((c for c in df.columns if c.lower() in ['response', 'body', 'html', 'match']), None)
        status_col = next((c for c in df.columns if c.lower() in ['status', 'status_code', 'code']), None)
        time_col = next((c for c in df.columns if c.lower() in ['time', 'duration', 'response_time']), None)
        tool_col = next((c for c in df.columns if c.lower() in ['tool', 'source', 'scanner']), None)

        # 1. Entropy Payload
        processed['entropy_payload'] = df[payload_col].apply(DatasetPreprocessor.calculate_entropy) if payload_col else 0.0

        # 2. Length Ratio
        def get_len_ratio(val):
            if pd.isna(val): return 1.0
            return len(str(val)) / 1000.0 # Diasumsikan baseline 1000 karakter
        processed['length_ratio'] = df[resp_col].apply(get_len_ratio) if resp_col else 1.0

        # 3. Status Code Shift
        def check_status_shift(val):
            if pd.isna(val): return 0
            # 1 jika ada indikasi WAF / Error (403, 500, dll)
            return 1 if str(val) in ['500', '403', '401', '406', '502'] else 0
        processed['status_code_shift'] = df[status_col].apply(check_status_shift) if status_col else 0

        # 4. DOM Reflection Flag
        def check_reflection(row):
            if pd.isna(row.get(payload_col)) or pd.isna(row.get(resp_col)): return 0
            payload_str = str(row[payload_col])
            # Cek jika payload ada di response dan panjangnya valid
            if len(payload_str) > 2 and payload_str in str(row[resp_col]):
                return 1
            return 0
            
        if payload_col and resp_col:
            processed['dom_reflection_flag'] = df.apply(check_reflection, axis=1)
        else:
            processed['dom_reflection_flag'] = 0

        # 5. Response Time Delta
        def get_time_delta(val):
            if pd.isna(val): return 0.0
            try: return max(0.0, float(val) - 200.0) # Baseline asumsi 200ms
            except: return 0.0
        processed['response_time_delta'] = df[time_col].apply(get_time_delta) if time_col else 0.0

        # 6. Pattern Regex Severity Match
        dbms_patterns = re.compile(r"(sql syntax|mysql_fetch|ora-[0-9]{5}|postgresql query failed|sqlite3.exception|warning: mysql|unclosed quotation mark|syntax error)", re.IGNORECASE)
        def check_regex(val):
            if pd.isna(val): return 0
            return len(dbms_patterns.findall(str(val)))
        processed['pattern_regex_severity'] = df[resp_col].apply(check_regex) if resp_col else 0

        # 7. Multi-Tool Consensus Score
        def get_tool_consensus(val):
            if pd.isna(val): return 1
            val_str = str(val)
            if ',' in val_str: return len(val_str.split(','))
            return 1
        processed['multi_tool_consensus'] = df[tool_col].apply(get_tool_consensus) if tool_col else 1

        # Tambahan: severity_score (wajib ada untuk model bawaan jika dibutuhkan)
        severity_col = next((c for c in df.columns if c.lower() in ['severity', 'cvss', 'severity_score']), None)
        def map_severity(val):
            if pd.isna(val): return 1.0
            try: return float(val)
            except:
                v = str(val).upper()
                if "CRITICAL" in v: return 9.0
                if "HIGH" in v: return 7.5
                if "MEDIUM" in v: return 5.5
                return 3.0
        processed['severity_score'] = df[severity_col].apply(map_severity) if severity_col else 1.0

        return processed

    @staticmethod
    def handle_missing(df: pd.DataFrame) -> pd.DataFrame:
        for col in df.columns:
            if df[col].isnull().any():
                if pd.api.types.is_numeric_dtype(df[col]):
                    median_val = df[col].median()
                    df[col] = df[col].fillna(median_val if not pd.isna(median_val) else 0.0)
                else:
                    mode_s = df[col].mode()
                    df[col] = df[col].fillna(mode_s.iloc[0] if not mode_s.empty else "unknown")
        return df

    @staticmethod
    def process_end_to_end(file_path: str, label_col: str, dataset_name: str, user_id: str) -> int:
        """
        Fase 3: Pemrosesan Dataset Skala Besar via Chunking.
        Menghindari Out-Of-Memory (OOM) pada RAM saat memproses jutaan baris.
        """
        print(f"[PREPROCESS] Memulai Chunked Processing End-to-End untuk {file_path}...")
        ext = os.path.splitext(file_path)[1].lower()
        chunksize = 50000
        processed_chunks = []
        
        def process_chunk(chunk_df):
            # 1. Map Label
            chunk_df = DatasetPreprocessor.map_labels(chunk_df, label_col)
            # 2. Extract Features (Merampingkan RAM karena membuang raw HTML text)
            featured = DatasetPreprocessor.extract_features(chunk_df)
            return featured

        # Baca data secara bertahap (Chunking)
        if ext == '.csv':
            for chunk in pd.read_csv(file_path, chunksize=chunksize, low_memory=False):
                processed_chunks.append(process_chunk(chunk))
        elif ext == '.json':
            try:
                for chunk in pd.read_json(file_path, lines=True, chunksize=chunksize):
                    processed_chunks.append(process_chunk(chunk))
            except ValueError:
                # Fallback untuk JSON biasa (non-lines)
                df = pd.read_json(file_path)
                processed_chunks.append(process_chunk(df))
        elif ext in ['.parquet', '.pq']:
            # Parquet via pyarrow/fastparquet
            df = pd.read_parquet(file_path)
            processed_chunks.append(process_chunk(df))
        else:
            raise ValueError("Unsupported format.")
            
        # Gabungkan semua chunk yang sudah direduksi menjadi angka numerik (sangat hemat RAM)
        final_df = pd.concat(processed_chunks, ignore_index=True)
        final_df = DatasetPreprocessor.handle_missing(final_df)
        
        print(f"[PREPROCESS] Chunking selesai. Total {len(final_df)} baris siap di-split.")
        
        # Split Data (80/20)
        X = final_df.drop(columns=['label'])
        y = final_df['label']
        stratify_y = y if (len(y.unique()) > 1 and y.value_counts().min() > 1) else None
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=stratify_y)
        
        # Simpan & Register Database
        os.makedirs("preprocessed", exist_ok=True)
        unique_id = uuid.uuid4().hex
        
        train_path = f"preprocessed/{unique_id}_train.csv"
        test_path = f"preprocessed/{unique_id}_test.csv"
        
        train_df = X_train.copy()
        train_df['label'] = y_train
        test_df = X_test.copy()
        test_df['label'] = y_test
        
        train_df.to_csv(train_path, index=False)
        test_df.to_csv(test_path, index=False)
        
        db = SessionLocal()
        try:
            dataset = models.PreprocessedDataset(
                user_id=user_id,
                name=dataset_name,
                rows=len(final_df),
                features=len(X_train.columns),
                file_path=train_path
            )
            db.add(dataset)
            db.commit()
            db.refresh(dataset)
            dataset_id = dataset.id
        finally:
            db.close()
            
        return dataset_id

    @staticmethod
    def extract_features_single(finding_dict: dict) -> pd.DataFrame:
        """Helper untuk mengekstrak fitur dari 1 finding saat scanning berjalan."""
        df = pd.DataFrame([finding_dict])
        return DatasetPreprocessor.extract_features(df)
