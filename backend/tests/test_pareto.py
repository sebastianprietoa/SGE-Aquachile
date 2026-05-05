from __future__ import annotations

from app.repositories.csv_repository import CSVRepository
from app.services.data_backend_service import DataBackendService
from app.utils.seed_csv import seed_csv


def test_csv_repository_parses_comma_decimal_values(tmp_path) -> None:
    base_dir = tmp_path / "csv"
    base_dir.mkdir(parents=True, exist_ok=True)
    (base_dir / "sample.csv").write_text("id,value\n1,\"0,45\"\n", encoding="utf-8")

    repository = CSVRepository(base_dir)
    rows = repository.read_all("sample")

    assert rows[0]["value"] == 0.45


def test_pareto_uses_year_and_normalizes_percentages() -> None:
    seed_csv(reset=True)
    service = DataBackendService()

    rows = service.pareto_energy_use_base_year(1)
    years = sorted({row["year"] for row in rows})
    assert years == [2022, 2024]

    rows_2022 = [row for row in rows if row["year"] == 2022]
    assert round(sum(row["value"] for row in rows_2022), 1) == 53.4
    assert rows_2022[0]["percentage"] == 49.66
    assert rows_2022[-1]["accumulated_percentage"] == 100.0

    rows_2024 = service.pareto_energy_use_base_year(1, year=2024)
    assert rows_2024
    assert all(row["year"] == 2024 for row in rows_2024)
    assert rows_2024[-1]["accumulated_percentage"] == 100.0
