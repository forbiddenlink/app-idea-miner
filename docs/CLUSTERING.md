# Clustering Algorithm Deep Dive

## Overview

App-Idea Miner uses **HDBSCAN (Hierarchical Density-Based Spatial Clustering)** combined with **TF-IDF vectorization** to automatically discover and group similar app ideas from raw text.

### Why Clustering Matters

Traditional keyword search or manual categorization doesn't scale. Clustering allows us to:
- **Discover patterns** we didn't know existed
- **Group similar needs** even with different wording
- **Surface opportunities** by aggregating demand signals
- **Reduce noise** by identifying outliers

---

## Algorithm Pipeline

```
Raw Ideas
    │
    ▼
┌───────────────────┐
│ Text Preprocessing│
│ - Lowercase       │
│ - Remove stopwords│
│ - Lemmatization   │
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ TF-IDF            │
│ Vectorization     │
│ (500 features)    │
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ Dimensionality    │
│ Reduction (UMAP)  │
│ Optional for viz  │
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ HDBSCAN Clustering│
│ min_cluster_size=3│
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ Post-Processing   │
│ - Extract keywords│
│ - Generate labels │
│ - Score clusters  │
└───────────────────┘
```

---

## Step-by-Step Implementation

### 1. Text Preprocessing

**Goal:** Normalize text for better vectorization

```python
import re
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

class TextPreprocessor:
    def __init__(self):
        self.stopwords = set(stopwords.words('english'))
        self.lemmatizer = WordNetLemmatizer()
        
        # Add domain-specific stopwords
        self.stopwords.update(['app', 'application', 'wish', 'need', 'want'])
    
    def preprocess(self, text: str) -> str:
        # Lowercase
        text = text.lower()
        
        # Remove URLs
        text = re.sub(r'http\S+', '', text)
        
        # Remove punctuation except hyphens (for "e-commerce")
        text = re.sub(r'[^\w\s-]', ' ', text)
        
        # Tokenize
        tokens = text.split()
        
        # Remove stopwords and lemmatize
        tokens = [
            self.lemmatizer.lemmatize(token)
            for token in tokens
            if token not in self.stopwords and len(token) > 2
        ]
        
        return ' '.join(tokens)
```

**Example:**
```python
input = "I wish there was an app for tracking my daily water intake"
output = "track daily water intake"
```

---

### 2. TF-IDF Vectorization

**Goal:** Convert text to numerical vectors while capturing term importance

**Configuration:**
```python
from sklearn.feature_extraction.text import TfidfVectorizer

vectorizer = TfidfVectorizer(
    max_features=500,         # Top 500 terms
    ngram_range=(1, 3),       # Unigrams, bigrams, trigrams
    stop_words='english',     # Built-in stopword removal
    min_df=2,                 # Term must appear in ≥2 documents
    max_df=0.85,              # Ignore terms in >85% of docs
    sublinear_tf=True,        # Use log scaling for term frequency
    norm='l2'                 # L2 normalization
)

# Fit and transform
tfidf_matrix = vectorizer.fit_transform(preprocessed_texts)
# Result: (n_documents, 500) sparse matrix
```

**Why These Parameters?**

- **max_features=500:** Balance between detail and computational cost
- **ngram_range=(1,3):** Capture phrases like "budget tracking app"
- **min_df=2:** Remove typos and extremely rare terms
- **max_df=0.85:** Remove generic terms that appear everywhere
- **sublinear_tf:** Prevent common words from dominating

**Example TF-IDF Scores:**
```python
# For text: "expense tracking budget management"
{
    "expense": 0.52,
    "tracking": 0.48,
    "budget": 0.51,
    "management": 0.49,
    "expense tracking": 0.65,  # Bigram gets higher weight
    "budget management": 0.62
}
```

---

### 3. Dimensionality Reduction (Optional)

**Goal:** Reduce 500D to 2D/3D for visualization

```python
import umap

reducer = umap.UMAP(
    n_components=2,           # 2D for plotting
    n_neighbors=15,           # Local structure preservation
    min_dist=0.1,             # Minimum spacing between points
    metric='cosine',          # Good for text data
    random_state=42
)

# Reduce dimensionality
embedding_2d = reducer.fit_transform(tfidf_matrix.toarray())
```

**Use Cases:**
- Visualization in web UI
- Exploratory data analysis
- Sanity checking clusters

**Note:** HDBSCAN runs on original 500D space, not reduced dimensions!

---

### 4. HDBSCAN Clustering

**Goal:** Find dense regions of similar ideas, identify noise

```python
import hdbscan

clusterer = hdbscan.HDBSCAN(
    min_cluster_size=3,              # Minimum ideas per cluster
    min_samples=2,                   # Core point threshold
    metric='cosine',                 # Distance metric for text
    cluster_selection_method='eom',  # Excess of Mass (stable)
    prediction_data=True             # Enable soft clustering
)

# Fit clustering
labels = clusterer.fit_predict(tfidf_matrix)

# Results:
# labels = [0, 0, 1, 1, 1, -1, 2, 2, 0]
#          ↑           ↑           ↑
#       Cluster 0   Noise      Cluster 2
```

**Key Parameters Explained:**

**min_cluster_size=3:**
- Minimum number of points to form a cluster
- Lower value = more granular clusters
- Higher value = only large, stable clusters
- **Recommended:** 3-5 for MVP

**min_samples=2:**
- How many neighbors a point needs to be a "core" point
- Lower = more points included in clusters
- Higher = stricter cluster membership
- **Recommended:** Equal to or less than min_cluster_size

**metric='cosine':**
- Measures angle between vectors (direction, not magnitude)
- Perfect for TF-IDF (normalized vectors)
- Range: 0 (identical) to 1 (opposite)

**cluster_selection_method='eom':**
- **EOM (Excess of Mass):** Prefers stable, persistent clusters
- **Leaf:** More granular, sometimes unstable
- **Recommended:** EOM for production

---

### 5. Understanding Cluster Labels

```python
# Example output:
labels = [-1, 0, 0, 1, -1, 2, 2, 2, 0]

# -1 = Noise/Outlier (doesn't fit any cluster)
# 0, 1, 2, ... = Cluster IDs
```

**Noise Handling:**
- Ideas labeled `-1` are outliers
- Could be: unique needs, spam, vague statements
- **Strategy:** Store separately, periodically re-cluster as more data arrives

---

### 6. Keyword Extraction

**Goal:** Identify top terms that characterize each cluster

```python
def extract_cluster_keywords(
    tfidf_matrix,
    vectorizer,
    labels,
    top_n=10
):
    cluster_keywords = {}
    
    for cluster_id in set(labels):
        if cluster_id == -1:  # Skip noise
            continue
        
        # Get all documents in this cluster
        cluster_mask = labels == cluster_id
        cluster_vectors = tfidf_matrix[cluster_mask]
        
        # Average TF-IDF scores across cluster
        avg_scores = cluster_vectors.mean(axis=0).A1
        
        # Get top N terms
        top_indices = avg_scores.argsort()[-top_n:][::-1]
        terms = vectorizer.get_feature_names_out()
        
        cluster_keywords[cluster_id] = [
            (terms[i], avg_scores[i])
            for i in top_indices
        ]
    
    return cluster_keywords
```

**Example Output:**
```python
{
    0: [
        ('reading', 0.82),
        ('books', 0.78),
        ('progress tracking', 0.75),
        ('habits', 0.71),
        ('analytics', 0.68),
        ...
    ],
    1: [
        ('expense', 0.85),
        ('budget', 0.83),
        ('tracking', 0.79),
        ('finance', 0.74),
        ...
    ]
}
```

---

### 7. Cluster Label Generation

**Goal:** Create human-readable cluster names

**Strategy 1: Top Keywords (Simple)**
```python
def generate_label_from_keywords(keywords: List[Tuple[str, float]]) -> str:
    # Take top 3 keywords
    top_terms = [kw[0] for kw in keywords[:3]]
    
    # Capitalize and join
    label = ' + '.join(word.title() for word in top_terms)
    
    return label

# Example: "Reading + Books + Progress Tracking"
```

**Strategy 2: Most Representative Idea (Better)**
```python
def generate_label_from_centroid(
    cluster_id: int,
    tfidf_matrix,
    labels,
    ideas: List[str]
) -> str:
    # Get cluster documents
    cluster_mask = labels == cluster_id
    cluster_vectors = tfidf_matrix[cluster_mask]
    
    # Calculate centroid
    centroid = cluster_vectors.mean(axis=0)
    
    # Find closest idea to centroid
    similarities = cosine_similarity(cluster_vectors, centroid)
    most_central_idx = similarities.argmax()
    
    # Get the idea text
    cluster_ideas = [idea for i, idea in enumerate(ideas) if cluster_mask[i]]
    representative_idea = cluster_ideas[most_central_idx]
    
    # Extract key phrases (simple heuristic)
    label = extract_key_phrase(representative_idea)
    
    return label

# Example: "Book Reading & Progress Tracking"
```

**Strategy 3: GPT-4 Generation (Future)**
```python
def generate_label_with_gpt(
    keywords: List[str],
    example_ideas: List[str]
) -> str:
    prompt = f"""
    Based on these keywords and examples, create a 2-5 word label:
    
    Keywords: {', '.join(keywords[:10])}
    
    Examples:
    {chr(10).join(f'- {idea}' for idea in example_ideas[:5])}
    
    Label:
    """
    
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=20
    )
    
    return response.choices[0].message.content.strip()
```

---

### 8. Cluster Scoring

**Goal:** Rank clusters by opportunity quality

```python
def score_cluster(cluster_data: dict) -> float:
    """
    Composite score combining multiple factors
    """
    # Normalize inputs (0-1 range)
    size_score = min(cluster_data['idea_count'] / 50, 1.0)  # Cap at 50
    sentiment_score = (cluster_data['avg_sentiment'] + 1) / 2  # -1 to 1 → 0 to 1
    quality_score = cluster_data['avg_quality_score']
    trend_score = cluster_data['trend_score']
    
    # Weighted combination
    weights = {
        'size': 0.4,       # Larger = more demand
        'sentiment': 0.2,  # Positive = easier to build
        'quality': 0.3,    # Clear problem statements
        'trend': 0.1       # Growing interest
    }
    
    total_score = (
        weights['size'] * size_score +
        weights['sentiment'] * sentiment_score +
        weights['quality'] * quality_score +
        weights['trend'] * trend_score
    )
    
    return total_score

# Example:
# {idea_count: 25, avg_sentiment: 0.6, avg_quality: 0.8, trend: 0.7}
# → 0.4*(25/50) + 0.2*0.8 + 0.3*0.8 + 0.1*0.7 = 0.67
```

---

## Advanced Techniques

### Incremental Clustering

**Problem:** Re-clustering from scratch is expensive

**Solution:** Approximate cluster membership for new ideas

```python
def assign_to_existing_cluster(
    new_idea_vector,
    cluster_centroids,
    threshold=0.6
):
    """
    Assign new idea to closest cluster if similarity > threshold
    """
    similarities = cosine_similarity(new_idea_vector, cluster_centroids)
    max_sim = similarities.max()
    
    if max_sim >= threshold:
        return similarities.argmax()  # Cluster ID
    else:
        return -1  # Noise/new cluster needed
```

**When to Re-Cluster:**
- Every 100 new ideas
- Weekly scheduled job
- Manual trigger from UI

---

### Handling Imbalanced Clusters

**Problem:** One cluster has 100 ideas, others have 3

**Solutions:**

1. **Split Large Clusters:**
```python
def split_large_cluster(cluster_id, max_size=30):
    ideas = get_cluster_ideas(cluster_id)
    
    if len(ideas) > max_size:
        # Run HDBSCAN on just this cluster
        sub_clusterer = HDBSCAN(min_cluster_size=5)
        sub_labels = sub_clusterer.fit_predict(ideas)
        
        # Create new clusters
        for sub_id in set(sub_labels):
            if sub_id != -1:
                create_new_cluster(ideas[sub_labels == sub_id])
```

2. **Merge Small Clusters:**
```python
def merge_similar_small_clusters(min_size=5, similarity_threshold=0.7):
    small_clusters = get_clusters_with_size_less_than(min_size)
    
    for i, c1 in enumerate(small_clusters):
        for c2 in small_clusters[i+1:]:
            sim = cosine_similarity(c1.centroid, c2.centroid)
            
            if sim >= similarity_threshold:
                merge_clusters(c1, c2)
```

---

### Multi-Language Support (Future)

**Challenge:** Ideas in different languages

**Solution:** Multilingual embeddings

```python
from sentence_transformers import SentenceTransformer

# Use multilingual BERT
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

# Encode texts (works for 50+ languages)
embeddings = model.encode(texts)

# Cluster on embeddings instead of TF-IDF
labels = clusterer.fit_predict(embeddings)
```

---

## Evaluation Metrics

### Internal Metrics (No Ground Truth)

**1. Silhouette Score**
```python
from sklearn.metrics import silhouette_score

# Measures cluster cohesion and separation
score = silhouette_score(tfidf_matrix, labels, metric='cosine')
# Range: -1 to 1 (higher is better)
# > 0.5 = good clustering
```

**2. Davies-Bouldin Index**
```python
from sklearn.metrics import davies_bouldin_score

# Lower is better (more distinct clusters)
score = davies_bouldin_score(tfidf_matrix.toarray(), labels)
```

**3. Cluster Stability**
```python
def measure_stability(data, n_iterations=10):
    """
    Run clustering multiple times with slight perturbations
    Measure how consistent cluster assignments are
    """
    from sklearn.metrics import adjusted_rand_score
    
    base_labels = clusterer.fit_predict(data)
    
    scores = []
    for _ in range(n_iterations):
        # Add small noise
        noisy_data = data + np.random.normal(0, 0.01, data.shape)
        new_labels = clusterer.fit_predict(noisy_data)
        
        # Compare to base
        scores.append(adjusted_rand_score(base_labels, new_labels))
    
    return np.mean(scores)  # Should be > 0.8 for stable clustering
```

### External Metrics (With Manual Labels)

**Adjusted Rand Index (ARI)**
```python
from sklearn.metrics import adjusted_rand_score

# Compare against manual labels
ari = adjusted_rand_score(true_labels, predicted_labels)
# Range: 0 (random) to 1 (perfect)
```

---

## Visualization

### 2D Cluster Plot

```python
import matplotlib.pyplot as plt

def plot_clusters(embedding_2d, labels, cluster_keywords):
    plt.figure(figsize=(12, 8))
    
    # Plot each cluster with different color
    unique_labels = set(labels)
    colors = plt.cm.Spectral(np.linspace(0, 1, len(unique_labels)))
    
    for label, color in zip(unique_labels, colors):
        if label == -1:  # Noise
            color = 'gray'
        
        mask = labels == label
        plt.scatter(
            embedding_2d[mask, 0],
            embedding_2d[mask, 1],
            c=[color],
            label=f'Cluster {label}' if label != -1 else 'Noise',
            alpha=0.6,
            s=50
        )
        
        # Add cluster label at centroid
        if label != -1:
            centroid = embedding_2d[mask].mean(axis=0)
            keywords = cluster_keywords[label][:3]
            label_text = ' + '.join([kw[0] for kw in keywords])
            plt.annotate(
                label_text,
                centroid,
                fontsize=10,
                bbox=dict(boxstyle='round', fc=color, alpha=0.5)
            )
    
    plt.legend()
    plt.title('App Idea Clusters')
    plt.xlabel('UMAP Dimension 1')
    plt.ylabel('UMAP Dimension 2')
    plt.tight_layout()
    plt.savefig('clusters.png', dpi=150)
```

---

## Tuning Guide

### Parameters to Adjust

| Parameter | Effect | When to Increase | When to Decrease |
|-----------|--------|------------------|------------------|
| `min_cluster_size` | Cluster granularity | Too many tiny clusters | Clusters too coarse |
| `min_samples` | Core point strictness | Clusters too loose | Too much noise |
| `max_features` | Vocabulary size | Rich domain language | Generic text |
| `ngram_range` | Phrase capture | Need multi-word phrases | Too sparse |

### Tuning Process

1. **Start with defaults** (min_cluster_size=3, min_samples=2)
2. **Visualize results** (2D plot + sample ideas per cluster)
3. **Check metrics** (Silhouette score, cluster sizes)
4. **Manually inspect** (Do clusters make semantic sense?)
5. **Adjust iteratively**

---

## Performance Optimization

### For 10,000+ Ideas

1. **Use sparse matrices:** TF-IDF is already sparse, keep it that way
2. **Batch processing:** Cluster in chunks, merge later
3. **Approximation:** Use HDBSCAN with `core_dist_n_jobs=-1` for parallelism
4. **Caching:** Store TF-IDF matrix, only recompute for new ideas

```python
# Optimized clustering
clusterer = hdbscan.HDBSCAN(
    min_cluster_size=5,
    min_samples=3,
    metric='cosine',
    core_dist_n_jobs=-1,  # Use all CPU cores
    memory=Memory('./cache')  # Cache computations
)
```

---

## Common Issues & Solutions

### Issue: All ideas in one giant cluster
**Cause:** `min_cluster_size` too low or data too similar  
**Solution:** Increase `min_cluster_size`, add more diverse data sources

### Issue: Everything is noise (label=-1)
**Cause:** `min_cluster_size` too high or data too sparse  
**Solution:** Decrease `min_cluster_size`, improve text preprocessing

### Issue: Duplicate clusters
**Cause:** Keywords too generic, not enough features  
**Solution:** Increase `max_features`, adjust `max_df`

### Issue: Non-semantic clusters
**Cause:** Poor text preprocessing or wrong metric  
**Solution:** Improve preprocessing, ensure `metric='cosine'` for TF-IDF

---

## Future Enhancements

1. **Semantic Embeddings:** Replace TF-IDF with BERT/Sentence-BERT
2. **Hierarchical View:** Show cluster hierarchy (sub-clusters)
3. **Active Learning:** User feedback to refine clusters
4. **Cross-Lingual:** Cluster ideas across languages
5. **Temporal Clustering:** Track how clusters evolve over time

---

**This clustering approach balances simplicity, accuracy, and performance—perfect for an MVP that can scale.** 🔬
