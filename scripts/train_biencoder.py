"""
Contrastive Fine-Tuning Pipeline for Sentence-BERT Bi-Encoder
Uses Native PyTorch with MultipleNegativesRankingLoss (InfoNCE Contrastive Loss)
on curated candidate-opportunity anchor-positive-negative triplets.
Saves fine-tuned model artifacts and generates training convergence curves.
"""
import os
import argparse
import logging
import json
from typing import List, Tuple
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import torch
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from sentence_transformers import SentenceTransformer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_curated_training_triplets() -> List[Tuple[str, str, str]]:
    """
    Generate curated anchor-positive-negative training triplets across diverse tech domains
    including Computer Vision, Deep Learning, NLP, Systems, Cloud, and PM.
    """
    return [
        # Domain 1: Computer Vision & Deep Learning (Target: AIRA Matrix)
        (
            "B.Tech CSAI candidate with hands-on experience in PyTorch, OpenCV, CNNs, image classification, and semantic segmentation for biomedical imaging.",
            "AI Trainee Engineer at AIRA Matrix: Design deep learning models for digital pathology, cell segmentation, image analysis, and real-time inference.",
            "Digital Marketing and Growth Intern: Manage social media campaigns, SEO analytics, content writing, and email newsletters."
        ),
        (
            "Deep learning enthusiast with PyTorch experience, custom dataset augmentations, ResNet/ViT architectures, and transfer learning for pathology scans.",
            "Computer Vision Research Intern: Develop image classification and object detection pipelines using PyTorch, OpenCV, and high-resolution histology tiles.",
            "Financial Accounting Intern: Reconcile bank balances, audit ledger entries, process invoices, and manage Tally ERP data."
        ),
        (
            "Undergraduate researcher skilled in image filtering, contour detection, morphological transformations in OpenCV, and real-time inference optimization.",
            "Trainee AI/Vision Engineer: Build computationally efficient image processing algorithms, OpenCV pipelines, and edge inference modules.",
            "Human Resources Talent Acquisition Intern: Screen candidate profiles, coordinate interview schedules, and draft offer letters."
        ),

        # Domain 2: NLP & Semantic Recommendation (InternMatch Domain)
        (
            "NLP engineer proficient in Sentence-BERT, HuggingFace transformers, cosine similarity ranking, tokenization, and vector search with FAISS.",
            "Machine Learning Engineer Intern: Build semantic search engines, sentence embeddings, and hybrid recommendation algorithms for candidate-job matching.",
            "Supply Chain & Logistics Intern: Monitor warehouse inventory, optimize transport routing, and track purchase orders."
        ),
        (
            "Data scientist with expertise in TF-IDF, lexical retrieval, information extraction, regex PII redaction, and Scikit-learn classification.",
            "AI/NLP Intern: Implement document parsing, entity recognition, resume skill extraction, and explainable ranking systems.",
            "Customer Support Associate: Answer client inquiries, manage ticketing queue, and provide customer onboarding."
        ),
        (
            "Machine learning student who built contrastive learning pipelines with InfoNCE loss, Siamese networks, and LightGBM rerankers for entity resolution.",
            "Applied ML Engineer: Train Siamese bi-encoders with contrastive loss, build embedding indexes, and evaluate ranking NDCG metrics.",
            "Legal Compliance Intern: Review vendor contracts, check statutory documentation, and prepare compliance summaries."
        ),

        # Domain 3: Systems, DSA & C++ Real-Time Performance
        (
            "Competitive programmer (LeetCode Knight, Codeforces Specialist) with strong C++, data structures, memory optimization, and multi-threading.",
            "Systems & Algorithms Software Engineer: Develop low-latency algorithms, optimize computational complexity, and build real-time execution pipelines.",
            "Content Marketing Intern: Write blog posts, coordinate influencer partnerships, and draft product launch press releases."
        ),
        (
            "Computer Science student skilled in C++, Linux systems programming, cache efficiency, and algorithm profiling.",
            "Real-Time Software Engineer: Implement high-throughput C++ algorithms with sub-millisecond execution deadlines.",
            "Event Management Intern: Coordinate venue logistics, manage sponsor relations, and organize campus fest registrations."
        ),

        # Domain 4: Full-Stack & API Architecture
        (
            "Full-stack developer with FastAPI, React, Node.js, WebSockets, and database indexing for scalable real-time applications.",
            "Full-Stack Software Engineer Intern: Design high-performance REST APIs, WebSocket state synchronization, and scalable web backends.",
            "Sales Development Representative: Conduct cold calling, qualify inbound leads, and schedule product demonstrations."
        ),
        (
            "Backend engineer proficient in Flask, PostgreSQL, SQLAlchemy ORM, SQLite caching, and automated testing with pytest.",
            "Backend Engineering Intern: Build robust microservices, database schemas, API authentication, and automated integration test suites.",
            "Graphic Design Intern: Create promotional posters, vector logos, and social media banners using Adobe Photoshop."
        ),

        # Domain 5: Product Management & Analytics
        (
            "Aspiring Product Manager with experience in user research, PRDs, wireframing, A/B testing, and North Star metric analytics.",
            "Associate Product Manager Intern: Conduct user discovery interviews, draft PRDs, define product roadmaps, and track retention metrics.",
            "Civil Engineering Intern: Inspect construction sites, review concrete testing reports, and verify CAD structural drawings."
        ),
        (
            "Product analyst skilled in SQL cohort analysis, user journey mapping, feature prioritization frameworks (RICE), and KPI dashboards.",
            "PM & Data Analyst Intern: Analyze user engagement drop-offs, design experimentation frameworks, and deliver strategic product insights.",
            "Mechanical Maintenance Intern: Monitor hydraulic pump pressure, perform preventative equipment maintenance, and log machine downtime."
        )
    ]


class TripletDataset(Dataset):
    """PyTorch Dataset for Contrastive Learning Triplets."""
    def __init__(self, triplets: List[Tuple[str, str, str]]):
        self.triplets = triplets

    def __len__(self):
        return len(self.triplets)

    def __getitem__(self, idx):
        return self.triplets[idx]


def get_evaluation_pairs() -> Tuple[List[str], List[str], np.ndarray]:
    """Generate evaluation pairs with ground-truth similarity scores (0.0 to 1.0)."""
    sentences1 = [
        "Computer vision engineer with PyTorch and medical image segmentation skills.",
        "Deep learning specialist in image classification and OpenCV algorithms.",
        "NLP researcher with Sentence-BERT, transformer models, and semantic search.",
        "Full-stack engineer building FastAPI backends and React frontends.",
        "Product manager defining user personas, PRDs, and North Star metrics."
    ]
    sentences2 = [
        "AIRA Matrix AI Trainee: Deep learning algorithms for digital pathology images.",
        "Computer Vision Intern: Image processing, contour analysis, and CNN classification.",
        "Machine Learning Engineer: Semantic vector retrieval and hybrid ranking engines.",
        "Backend Developer: Scalable RESTful API architecture and database modeling.",
        "Associate Product Manager: Feature roadmapping, user research, and metric tracking."
    ]
    scores = np.array([0.95, 0.92, 0.90, 0.88, 0.85], dtype=np.float32)
    return sentences1, sentences2, scores


def evaluate_similarity_correlation(model: SentenceTransformer, sentences1: List[str],
                                   sentences2: List[str], target_scores: np.ndarray) -> float:
    """Evaluate Pearson correlation of model cosine similarities against target relevance scores."""
    model.eval()
    with torch.no_grad():
        emb1 = model.encode(sentences1, normalize_embeddings=True, show_progress_bar=False)
        emb2 = model.encode(sentences2, normalize_embeddings=True, show_progress_bar=False)
        sims = np.sum(emb1 * emb2, axis=1)
        # Compute Pearson correlation
        if np.std(sims) == 0 or np.std(target_scores) == 0:
            return 0.5
        corr = float(np.corrcoef(sims, target_scores)[0, 1])
        return corr


def train_biencoder(
    base_model_name: str = "all-MiniLM-L6-v2",
    output_dir: str = "instance/fine_tuned_sbert",
    report_dir: str = "reports",
    epochs: int = 3,
    batch_size: int = 4,
    learning_rate: float = 2e-5,
    temperature: float = 0.05
) -> str:
    """
    Execute native PyTorch fine-tuning of SentenceTransformer using InfoNCE Contrastive Loss.
    """
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(report_dir, exist_ok=True)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info("Using device for training: %s", device)

    logger.info("Loading base Sentence-BERT model: %s", base_model_name)
    model = SentenceTransformer(base_model_name)
    model.to(device)
    tokenizer = model.tokenizer

    triplets = get_curated_training_triplets()
    dataset = TripletDataset(triplets)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    val_s1, val_s2, val_scores = get_evaluation_pairs()
    initial_corr = evaluate_similarity_correlation(model, val_s1, val_s2, val_scores)
    logger.info("Pre-training Validation Correlation: %.4f", initial_corr)

    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=0.01)

    epoch_losses = []
    val_corrs = [initial_corr]

    logger.info("Starting PyTorch contrastive training for %d epochs...", epochs)

    scale = 1.0 / temperature  # e.g. 20.0 for temperature=0.05

    for epoch in range(1, epochs + 1):
        model.train()
        batch_losses = []

        for batch_idx, (anchors, positives, negatives) in enumerate(dataloader):
            optimizer.zero_grad()

            # Tokenize batch
            a_inputs = tokenizer(list(anchors), padding=True, truncation=True, return_tensors='pt').to(device)
            p_inputs = tokenizer(list(positives), padding=True, truncation=True, return_tensors='pt').to(device)
            n_inputs = tokenizer(list(negatives), padding=True, truncation=True, return_tensors='pt').to(device)

            # Forward passes
            a_out = model({'input_ids': a_inputs['input_ids'], 'attention_mask': a_inputs['attention_mask']})
            p_out = model({'input_ids': p_inputs['input_ids'], 'attention_mask': p_inputs['attention_mask']})
            n_out = model({'input_ids': n_inputs['input_ids'], 'attention_mask': n_inputs['attention_mask']})

            a_emb = F.normalize(a_out['sentence_embedding'], p=2, dim=1)
            p_emb = F.normalize(p_out['sentence_embedding'], p=2, dim=1)
            n_emb = F.normalize(n_out['sentence_embedding'], p=2, dim=1)

            # InfoNCE Similarity Matrix: Anchor vs Positives + Negatives
            pos_sim = torch.mm(a_emb, p_emb.t()) * scale
            neg_sim = torch.mm(a_emb, n_emb.t()) * scale
            logits = torch.cat([pos_sim, neg_sim], dim=1)

            # Target labels: diagonal indices (anchors match corresponding positive)
            labels = torch.arange(len(anchors), device=device)

            loss = F.cross_entropy(logits, labels)
            loss.backward()

            # Clip gradient norm for stability
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()

            batch_losses.append(loss.item())

        avg_loss = float(np.mean(batch_losses))
        epoch_losses.append(avg_loss)

        curr_corr = evaluate_similarity_correlation(model, val_s1, val_s2, val_scores)
        val_corrs.append(curr_corr)

        logger.info("Epoch %d/%d - Loss: %.4f - Val Correlation: %.4f",
                    epoch, epochs, avg_loss, curr_corr)

    final_corr = val_corrs[-1]
    logger.info("Fine-tuning completed. Final Correlation: %.4f (Improvement: %+.4f)",
                final_corr, final_corr - initial_corr)

    # Save fine-tuned model
    model.save(output_dir)
    logger.info("Fine-tuned model saved to %s", output_dir)

    # Plot convergence curve
    curve_path = os.path.join(report_dir, "training_loss_curve.png")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))

    ax1.plot(range(1, epochs + 1), epoch_losses, marker='s', color='#dc2626', linewidth=2.2, label='InfoNCE Loss')
    ax1.set_title('Training Loss Convergence', fontsize=12, fontweight='bold')
    ax1.set_xlabel('Epoch', fontsize=11)
    ax1.set_ylabel('Cross-Entropy Loss', fontsize=11)
    ax1.grid(True, linestyle='--', alpha=0.5)
    ax1.legend()

    ax2.plot(range(0, epochs + 1), val_corrs, marker='o', color='#2563eb', linewidth=2.2, label='Val Pearson Correlation')
    ax2.set_title('Domain Ranking Correlation', fontsize=12, fontweight='bold')
    ax2.set_xlabel('Epoch', fontsize=11)
    ax2.set_ylabel('Pearson Correlation', fontsize=11)
    ax2.grid(True, linestyle='--', alpha=0.5)
    ax2.legend()

    plt.suptitle('Sentence-BERT Fine-Tuning Convergence (AIRA Matrix Trainee Domain)', fontsize=13, fontweight='bold')
    plt.tight_layout()
    plt.savefig(curve_path, dpi=200)
    plt.close()
    logger.info("Saved convergence plot to %s", curve_path)

    # Save summary JSON
    summary_file = os.path.join(report_dir, "fine_tuning_summary.json")
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump({
            "base_model": base_model_name,
            "architecture": "Sentence-BERT Bi-Encoder (PyTorch)",
            "loss_function": "InfoNCE / MultipleNegativesRankingLoss",
            "device": str(device),
            "epochs": epochs,
            "batch_size": batch_size,
            "learning_rate": learning_rate,
            "temperature": temperature,
            "epoch_losses": epoch_losses,
            "initial_correlation": float(initial_corr),
            "final_correlation": float(final_corr),
            "output_directory": output_dir,
            "curve_plot": curve_path
        }, f, indent=2)

    return output_dir


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Contrastive Fine-Tuning for InternMatch Bi-Encoder")
    parser.add_argument("--epochs", type=int, default=3, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=4, help="Batch size for training")
    parser.add_argument("--lr", type=float, default=2e-5, help="Learning rate")
    parser.add_argument("--output-dir", type=str, default="instance/fine_tuned_sbert", help="Output directory")
    args = parser.parse_args()

    train_biencoder(
        output_dir=args.output_dir,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.lr
    )
