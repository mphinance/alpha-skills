"""Tests for thesis_ingest.py — adapter conversion and registration."""

import json
from pathlib import Path

import pytest
import thesis_ingest
import thesis_store

# -- Helpers -------------------------------------------------------------------


def _write_json(tmp_path: Path, data, filename="input.json"):
    path = tmp_path / filename
    path.write_text(json.dumps(data))
    return str(path)


# -- Tests: kanchi adapter -----------------------------------------------------


def test_ingest_kanchi(tmp_path: Path):
    """kanchi JSON → thesis with dividend_income, entry.target_price populated."""
    state_dir = tmp_path / "theses"
    record = {
        "ticker": "JNJ",
        "buy_target_price": 148.50,
        "current_yield_pct": 3.2,
        "signal": "BUY",
        "grade": "A",
    }
    input_file = _write_json(tmp_path, {"candidates": [record]})

    ids = thesis_ingest.ingest("kanchi-dividend-sop", input_file, str(state_dir))
    assert len(ids) == 1

    thesis = thesis_store.get(state_dir, ids[0])
    assert thesis["ticker"] == "JNJ"
    assert thesis["thesis_type"] == "dividend_income"
    assert thesis["entry"]["target_price"] == 148.50
    assert thesis["origin"]["skill"] == "kanchi-dividend-sop"
    assert thesis["origin"]["raw_provenance"]["current_yield_pct"] == 3.2


# -- Tests: earnings adapter ---------------------------------------------------


def test_ingest_earnings(tmp_path: Path):
    """earnings JSON → grade in raw_provenance, screening_grade canonical."""
    state_dir = tmp_path / "theses"
    record = {
        "symbol": "NVDA",
        "grade": "A",
        "composite_score": 92.5,
        "gap_pct": 8.3,
        "sector": "Technology",
    }
    input_file = _write_json(tmp_path, {"results": [record]})

    ids = thesis_ingest.ingest("earnings-trade-analyzer", input_file, str(state_dir))
    assert len(ids) == 1

    thesis = thesis_store.get(state_dir, ids[0])
    assert thesis["ticker"] == "NVDA"
    assert thesis["thesis_type"] == "earnings_drift"
    assert thesis["origin"]["screening_grade"] == "A"
    assert thesis["origin"]["screening_score"] == 92.5
    assert thesis["origin"]["raw_provenance"]["gap_pct"] == 8.3
    assert thesis["market_context"]["sector"] == "Technology"


# -- Tests: vcp adapter --------------------------------------------------------


def test_ingest_vcp(tmp_path: Path):
    """vcp JSON → pivot_breakout type."""
    state_dir = tmp_path / "theses"
    record = {
        "symbol": "PLTR",
        "distance_from_pivot_pct": 2.3,
        "entry_ready": True,
        "composite_score": 78.0,
    }
    input_file = _write_json(tmp_path, {"results": [record]})

    ids = thesis_ingest.ingest("vcp-screener", input_file, str(state_dir))
    assert len(ids) == 1

    thesis = thesis_store.get(state_dir, ids[0])
    assert thesis["ticker"] == "PLTR"
    assert thesis["thesis_type"] == "pivot_breakout"
    assert thesis["origin"]["raw_provenance"]["entry_ready"] is True


# -- Tests: pead adapter -------------------------------------------------------


def test_ingest_pead(tmp_path: Path):
    """pead JSON → entry_price and stop_loss mapped."""
    state_dir = tmp_path / "theses"
    record = {
        "symbol": "CRWD",
        "entry_price": 380.00,
        "stop_loss": 355.00,
        "status": "SIGNAL_READY",
        "grade": "B",
    }
    input_file = _write_json(tmp_path, {"results": [record]})

    ids = thesis_ingest.ingest("pead-screener", input_file, str(state_dir))
    assert len(ids) == 1

    thesis = thesis_store.get(state_dir, ids[0])
    assert thesis["entry"]["target_price"] == 380.00
    assert thesis["exit"]["stop_loss"] == 355.00


# -- Tests: canslim adapter ----------------------------------------------------


def test_ingest_canslim(tmp_path: Path):
    """canslim JSON → growth_momentum type."""
    state_dir = tmp_path / "theses"
    record = {
        "symbol": "META",
        "rating": "A",
        "composite_score": 85.0,
    }
    input_file = _write_json(tmp_path, [record])

    ids = thesis_ingest.ingest("canslim-screener", input_file, str(state_dir))
    assert len(ids) == 1

    thesis = thesis_store.get(state_dir, ids[0])
    assert thesis["thesis_type"] == "growth_momentum"
    assert thesis["origin"]["screening_grade"] == "A"


# -- Tests: raw_provenance preserved -------------------------------------------


def test_all_adapters_preserve_raw_provenance(tmp_path: Path):
    """All adapters should preserve original data in raw_provenance."""
    state_dir = tmp_path / "theses"
    record = {
        "symbol": "TEST",
        "grade": "B",
        "composite_score": 70.0,
        "custom_field": "custom_value",
    }
    input_file = _write_json(tmp_path, {"results": [record]})

    ids = thesis_ingest.ingest("earnings-trade-analyzer", input_file, str(state_dir))
    thesis = thesis_store.get(state_dir, ids[0])
    assert thesis["origin"]["raw_provenance"]["custom_field"] == "custom_value"


# -- Tests: error handling -----------------------------------------------------


def test_unknown_source_raises(tmp_path: Path):
    """Unknown --source should raise ValueError."""
    input_file = _write_json(tmp_path, [{"ticker": "AAPL"}])
    with pytest.raises(ValueError, match="Unknown source"):
        thesis_ingest.ingest("nonexistent-skill", input_file, str(tmp_path))


def test_missing_required_fields_raises(tmp_path: Path):
    """Missing required fields should raise validation error."""
    state_dir = tmp_path / "theses"
    record = {"not_a_ticker": "AAPL"}  # missing 'ticker' or 'symbol'
    input_file = _write_json(tmp_path, {"results": [record]})

    # Should log error but not raise (continues to next record)
    ids = thesis_ingest.ingest("earnings-trade-analyzer", input_file, str(state_dir))
    assert len(ids) == 0


# -- Tests: edge adapter -------------------------------------------------------


def test_edge_research_only_skipped(tmp_path: Path):
    """edge ticket with research_only=True → skip with warning."""
    state_dir = tmp_path / "theses"
    record = {
        "id": "ticket_001",
        "ticker": "SPY",
        "hypothesis_type": "breakout",
        "research_only": True,
    }
    input_file = _write_json(tmp_path, record)

    ids = thesis_ingest.ingest("edge-candidate-agent", input_file, str(state_dir))
    assert len(ids) == 0


def test_edge_market_basket_skipped(tmp_path: Path):
    """edge ticket with MARKET_BASKET → skip with warning."""
    state_dir = tmp_path / "theses"
    record = {
        "id": "ticket_002",
        "universe": "MARKET_BASKET",
        "hypothesis_type": "momentum",
    }
    input_file = _write_json(tmp_path, record)

    ids = thesis_ingest.ingest("edge-candidate-agent", input_file, str(state_dir))
    assert len(ids) == 0


# -- Tests: fix verification ---------------------------------------------------


def test_ingest_kanchi_rows_key(tmp_path: Path):
    """kanchi build_entry_signals.py uses 'rows' key, not 'candidates'."""
    state_dir = tmp_path / "theses"
    record = {"ticker": "PG", "buy_target_price": 165.00}
    input_file = _write_json(tmp_path, {"rows": [record]})

    ids = thesis_ingest.ingest("kanchi-dividend-sop", input_file, str(state_dir))
    assert len(ids) == 1
    thesis = thesis_store.get(state_dir, ids[0])
    assert thesis["ticker"] == "PG"
    assert thesis["entry"]["target_price"] == 165.00


def test_edge_ticket_top_level_entry_exit(tmp_path: Path):
    """edge ticket uses top-level entry/exit, not signals.entry."""
    state_dir = tmp_path / "theses"
    record = {
        "id": "edge_vcp_v1",
        "ticker": "AMZN",
        "hypothesis_type": "breakout",
        "entry_family": "pivot_breakout",
        "mechanism_tag": "behavior",
        "entry": {"conditions": ["breakout above pivot", "volume > 1.5x avg"]},
        "exit": {"stop_loss_pct": 0.07, "take_profit_rr": 2.0, "time_stop_days": 20},
    }
    input_file = _write_json(tmp_path, record)

    ids = thesis_ingest.ingest("edge-candidate-agent", input_file, str(state_dir))
    assert len(ids) == 1
    thesis = thesis_store.get(state_dir, ids[0])
    assert thesis["entry"]["conditions"] == ["breakout above pivot", "volume > 1.5x avg"]
    assert thesis["exit"]["stop_loss_pct"] == 0.07
    assert thesis["exit"]["take_profit_rr"] == 2.0
    assert thesis["exit"]["time_stop_days"] == 20


# -- Tests: source date propagation --------------------------------------------


def test_ingest_propagates_as_of_date(tmp_path: Path):
    """as_of from report metadata should become thesis_id date and created_at."""
    state_dir = tmp_path / "theses"
    data = {
        "as_of": "2026-02-20",
        "generated_at": "2026-02-20T10:00:00Z",
        "rows": [{"ticker": "KO", "buy_target_price": 60.00}],
    }
    input_file = _write_json(tmp_path, data)

    ids = thesis_ingest.ingest("kanchi-dividend-sop", input_file, str(state_dir))
    assert len(ids) == 1
    assert "_20260220_" in ids[0]
    thesis = thesis_store.get(state_dir, ids[0])
    assert thesis["created_at"].startswith("2026-02-20")


def test_ingest_uses_generated_at_as_fallback(tmp_path: Path):
    """generated_at should be used if as_of is absent."""
    state_dir = tmp_path / "theses"
    data = {
        "generated_at": "2026-01-10T08:30:00Z",
        "results": [{"symbol": "GOOG", "grade": "B", "composite_score": 72.0}],
    }
    input_file = _write_json(tmp_path, data)

    ids = thesis_ingest.ingest("earnings-trade-analyzer", input_file, str(state_dir))
    assert "_20260110_" in ids[0]


# -- Tests: duplicate handling -------------------------------------------------


def test_duplicate_ingest_is_idempotent(tmp_path: Path):
    """Same input ingested twice should return the same thesis_id (idempotent)."""
    state_dir = tmp_path / "theses"
    record = {"symbol": "AAPL", "grade": "A", "composite_score": 90.0}
    input_file = _write_json(tmp_path, {"results": [record]})

    ids1 = thesis_ingest.ingest("earnings-trade-analyzer", input_file, str(state_dir))
    ids2 = thesis_ingest.ingest("earnings-trade-analyzer", input_file, str(state_dir))

    assert ids1[0] == ids2[0]
