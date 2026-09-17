import pytest
from backend.app.schemas.news import RawArticle
from backend.app.services.bias_mitigator import BiasMitigator, BiasAnalysisReport

def test_balanced_source_distribution_and_hhi():
    art1 = RawArticle(title="AI Model A", url="u1", source_name="Reuters", content="Researchers published model benchmarks.")
    art2 = RawArticle(title="AI Model B", url="u2", source_name="Bloomberg", content="Researchers tested model benchmarks.")
    art3 = RawArticle(title="AI Model C", url="u3", source_name="BBC News", content="Technology analysts reviewed benchmarks.")

    report = BiasMitigator.evaluate_bias_and_diversity([art1, art2, art3])

    assert isinstance(report, BiasAnalysisReport)
    assert len(report.source_distribution) == 3
    assert report.source_distribution["Reuters"] == 33.3
    assert report.diversity_rating == "OPTIMAL"
    assert report.warning is None
    assert report.hhi_score < 3500

def test_single_source_dominance_warning():
    # 4 articles from Reuters, 1 from Bloomberg (80% concentration)
    art1 = RawArticle(title="Story 1", url="u1", source_name="Reuters", content="Headline content 1.")
    art2 = RawArticle(title="Story 2", url="u2", source_name="Reuters", content="Headline content 2.")
    art3 = RawArticle(title="Story 3", url="u3", source_name="Reuters", content="Headline content 3.")
    art4 = RawArticle(title="Story 4", url="u4", source_name="Reuters", content="Headline content 4.")
    art5 = RawArticle(title="Story 5", url="u5", source_name="Bloomberg", content="Headline content 5.")

    report = BiasMitigator.evaluate_bias_and_diversity([art1, art2, art3, art4, art5])

    assert report.dominant_source == "Reuters"
    assert report.source_distribution["Reuters"] == 80.0
    assert report.diversity_rating == "CONCENTRATED"
    assert report.warning is not None
    assert "BIAS ALERT" in report.warning
    assert "80%" in report.warning

def test_consensus_and_divergence_extraction():
    art1 = RawArticle(
        title="Nvidia Revenue", url="u1", source_name="Reuters",
        content="Nvidia recorded quarterly revenue of thirty billion dollars with surging enterprise data center demand."
    )
    art2 = RawArticle(
        title="Nvidia Record Earnings", url="u2", source_name="Bloomberg",
        content="Nvidia posted quarterly revenue of thirty billion dollars while gross margins narrowed due to packaging delays."
    )

    consensus, divergence = BiasMitigator.extract_consensus_and_divergence([art1, art2])

    assert len(consensus) > 0
    # Both sources reported $30B revenue
    assert any("Reuters" in c and "Bloomberg" in c for c in consensus)

