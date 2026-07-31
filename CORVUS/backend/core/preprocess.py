import os
import uuid
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from backend.db.database import SessionLocal
from backend.db import models

class DatasetPreprocessor:
    @staticmethod
    def load_data(file_path: str) -> pd.DataFrame:
        """
        Reads CSV, JSON, or Parquet file and returns a pandas DataFrame.
        """
        print(f"[PREPROCESS] Memuat file {file_path} ke dalam memori Pandas...")
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.csv':
            return pd.read_csv(file_path)
        elif ext == '.json':
            try:
                return pd.read_json(file_path)
            except ValueError:
                print("[PREPROCESS] Mem-bypass limit angka raksasa Pandas (Manual JSON Lines)...")
                import json
                data = []
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            data.append(json.loads(line))
                return pd.DataFrame(data)
        elif ext in ['.parquet', '.pq']:
            return pd.read_parquet(file_path)
        else:
            raise ValueError("Unsupported file format. Only CSV, JSON, and Parquet are supported.")

    @staticmethod
    def map_labels(df: pd.DataFrame, label_col: str) -> pd.DataFrame:
        """
        Standardizes labels by mapping malicious/attack/True/1 to 1, and benign/normal/False/0 to 0.
        """
        print(f"[PREPROCESS] Memetakan kolom label '{label_col}' (1=Bahaya, 0=Aman)...")
        if label_col not in df.columns:
            raise ValueError(f"Label column '{label_col}' not found in dataset.")
        
        def mapper(val):
            if pd.isna(val):
                return 0
            val_str = str(val).lower().strip()
            if val_str in ['1', '1.0', 'true', 'malicious', 'attack', 'vuln', 'vulnerable', 'yes', 'danger', 'alert']:
                return 1
            return 0
            
        df['label'] = df[label_col].apply(mapper)
        return df

    @staticmethod
    def extract_features(df: pd.DataFrame) -> pd.DataFrame:
        """
        Extracts specific features: severity_score, tool_source, owasp_category, endpoint_depth, has_payload, response_length.
        Also parses traffic metadata from Caido CLI passive capture when present.
        
        SOP Labeling standard:
        - Malicious / verified exploit / attack Indicator -> 1 (True Positive)
        - Benign request / standard error / normal response -> 0 (False Positive)
        """
        print(f"[PREPROCESS] Mengekstrak fitur dari {len(df)} baris. Ini mungkin butuh waktu bermenit-menit...")
        processed = pd.DataFrame(index=df.index)
        
        # 1. Preserve or set binary Label
        if 'label' in df.columns:
            processed['label'] = df['label']
        else:
            processed['label'] = 0

        # 2. severity_score: CVSS score float or severity string mapping
        severity_col = None
        for col in df.columns:
            if col.lower() in ['severity', 'cvss', 'severity_score', 'cvss_score', 'risk_score']:
                severity_col = col
                break
                
        if severity_col:
            def map_severity(val):
                if pd.isna(val):
                    return 1.0
                try:
                    return float(val)
                except ValueError:
                    val_str = str(val).upper().strip()
                    if "CRITICAL" in val_str: return 9.0
                    elif "HIGH" in val_str: return 7.5
                    elif "MEDIUM" in val_str: return 5.5
                    elif "LOW" in val_str: return 3.0
                    return 1.0
            processed['severity_score'] = df[severity_col].apply(map_severity)
        else:
            processed['severity_score'] = 1.0

        # 3. tool_source: Label encoded source/scanner name
        source_col = None
        for col in df.columns:
            if col.lower() in ['source', 'tool', 'tool_source', 'scanner', 'origin']:
                source_col = col
                break
                
        if source_col:
            processed['tool_source'] = df[source_col].astype(str).astype('category').cat.codes + 1
        else:
            processed['tool_source'] = 1

        # 4. owasp_category: Label encoded category/cwe
        cat_col = None
        for col in df.columns:
            if col.lower() in ['category', 'cwe', 'owasp', 'owasp_category', 'vuln_type']:
                cat_col = col
                break
                
        if cat_col:
            processed['owasp_category'] = df[cat_col].astype(str).astype('category').cat.codes + 1
        else:
            processed['owasp_category'] = 1

        # 5. endpoint_depth: Count '/' occurrences in URLs or endpoints
        endpoint_col = None
        for col in df.columns:
            if col.lower() in ['endpoint', 'url', 'path', 'location', 'request_url']:
                endpoint_col = col
                break
                
        if endpoint_col:
            def get_depth(val):
                if pd.isna(val):
                    return 0
                val_str = str(val)
                val_str = val_str.replace("https://", "").replace("http://", "")
                return val_str.count('/')
            processed['endpoint_depth'] = df[endpoint_col].apply(get_depth)
        else:
            processed['endpoint_depth'] = 0

        # 6. has_payload: detect script/injection characters inside requests
        evidence_col = None
        for col in df.columns:
            if col.lower() in ['evidence', 'payload', 'request', 'params', 'match', 'query']:
                evidence_col = col
                break
                
        if evidence_col:
            def check_payload(val):
                if pd.isna(val):
                    return 0
                val_str = str(val).lower()
                indicators = ["'", "\"", "<script>", "union", "select", "alert(", "<", ">", "sys.user_objects", "passwd", "../"]
                for ind in indicators:
                    if ind in val_str:
                        return 1
                return 0
            processed['has_payload'] = df[evidence_col].apply(check_payload)
        else:
            processed['has_payload'] = 0

        # 7. response_length: Length of evidence/payload
        if evidence_col:
            processed['response_length'] = df[evidence_col].apply(lambda x: len(str(x)) if not pd.isna(x) else 0)
        else:
            processed['response_length'] = 0

        # 8. Caido CLI features integration (Traffic Context)
        # Parse caido request verb (GET/POST/PUT/DELETE)
        verb_col = next((c for c in df.columns if c.lower() in ['caido_request_verb', 'request_verb', 'method']), None)
        if verb_col:
            processed['caido_request_verb'] = df[verb_col].astype(str).astype('category').cat.codes + 1
        else:
            processed['caido_request_verb'] = 1

        # Parse caido param count
        param_col = next((c for c in df.columns if c.lower() in ['caido_param_count', 'param_count']), None)
        processed['caido_param_count'] = df[param_col].fillna(0).astype(int) if param_col else 0

        # Parse auth headers
        auth_col = next((c for c in df.columns if c.lower() in ['caido_auth_headers_present', 'auth_headers_present']), None)
        processed['caido_auth_headers_present'] = df[auth_col].fillna(0).astype(int) if auth_col else 0

        # Parse content type
        ct_col = next((c for c in df.columns if c.lower() in ['caido_content_type', 'content_type']), None)
        if ct_col:
            processed['caido_content_type'] = df[ct_col].astype(str).astype('category').cat.codes + 1
        else:
            processed['caido_content_type'] = 1

        # Parse response size mean & std
        size_mean_col = next((c for c in df.columns if c.lower() in ['caido_response_size_mean', 'response_size_mean']), None)
        processed['caido_response_size_mean'] = df[size_mean_col].fillna(1000.0).astype(float) if size_mean_col else 1000.0

        size_std_col = next((c for c in df.columns if c.lower() in ['caido_response_size_std', 'response_size_std']), None)
        processed['caido_response_size_std'] = df[size_std_col].fillna(100.0).astype(float) if size_std_col else 100.0

        # Parse status codes seen count
        sc_col = next((c for c in df.columns if c.lower() in ['caido_status_codes_seen', 'status_codes_seen']), None)
        if sc_col:
            processed['caido_status_codes_seen'] = df[sc_col].apply(lambda x: len(x) if isinstance(x, list) else (len(str(x).split(',')) if x else 1))
        else:
            processed['caido_status_codes_seen'] = 1

        # Parse depth
        depth_col = next((c for c in df.columns if c.lower() in ['caido_endpoint_depth', 'endpoint_depth']), None)
        processed['caido_endpoint_depth'] = df[depth_col].fillna(1).astype(int) if depth_col else 1

        return processed

    @staticmethod
    def handle_missing(df: pd.DataFrame) -> pd.DataFrame:
        """
        Fills missing values: numeric columns with median, categorical columns with mode.
        """
        print("[PREPROCESS] Mengisi data kosong (NaN) dengan Nilai Median/Mode...")
        for col in df.columns:
            if df[col].isnull().any():
                if pd.api.types.is_numeric_dtype(df[col]):
                    median_val = df[col].median()
                    df[col] = df[col].fillna(median_val if not pd.isna(median_val) else 0.0)
                else:
                    mode_series = df[col].mode()
                    df[col] = df[col].fillna(mode_series.iloc[0] if not mode_series.empty else "unknown")
        return df

    @staticmethod
    def split_data(df: pd.DataFrame):
        """
        Splits data 80/20 into train/test datasets.
        """
        print("[PREPROCESS] Memecah data menjadi 80% Latih (Train) dan 20% Uji (Test)...")
        X = df.drop(columns=['label'])
        y = df['label']
        # Try to stratify split if both classes are present, otherwise split without stratification
        stratify_y = y if (len(y.unique()) > 1 and y.value_counts().min() > 1) else None
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=stratify_y)
        return X_train, X_test, y_train, y_test

    @staticmethod
    def save_preprocessed(X_train, X_test, y_train, y_test, dataset_name: str, user_id: str) -> int:
        """
        Saves preprocessed train and test CSVs and registers the dataset metadata in the database.
        Returns the created dataset ID.
        """
        print(f"[PREPROCESS] Menyimpan dataset yang sudah diproses ke disk dan database...")
        os.makedirs("preprocessed", exist_ok=True)
        unique_id = uuid.uuid4().hex
        
        train_path = f"preprocessed/{unique_id}_train.csv"
        test_path = f"preprocessed/{unique_id}_test.csv"
        
        # Merge X and y before saving
        train_df = X_train.copy()
        train_df['label'] = y_train
        
        test_df = X_test.copy()
        test_df['label'] = y_test
        
        train_df.to_csv(train_path, index=False)
        test_df.to_csv(test_path, index=False)
        
        rows = len(train_df) + len(test_df)
        features = len(X_train.columns)
        
        # DB Persistence
        db = SessionLocal()
        try:
            dataset = models.PreprocessedDataset(
                user_id=user_id,
                name=dataset_name,
                rows=rows,
                features=features,
                file_path=train_path
            )
            db.add(dataset)
            db.commit()
            db.refresh(dataset)
            dataset_id = dataset.id
        finally:
            db.close()
            
        return dataset_id
