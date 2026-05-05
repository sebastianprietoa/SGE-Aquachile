from __future__ import annotations

import csv
import json
import re
import threading
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable


_INT_PATTERN = re.compile(r"^-?\d+$")
_FLOAT_PATTERN = re.compile(r"^-?\d+\.\d+(?:[eE][-+]?\d+)?$")
_COMMA_FLOAT_PATTERN = re.compile(r"^-?\d+,\d+(?:[eE][-+]?\d+)?$")


class CSVRepository:
    def __init__(self, base_dir: Path | str) -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()

    def _path(self, table_name: str) -> Path:
        return self.base_dir / f"{table_name}.csv"

    def _ensure_file(self, table_name: str) -> Path:
        path = self._path(table_name)
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.touch()
        return path

    @staticmethod
    def _parse_value(value: str) -> Any:
        if value is None:
            return None
        text = value.strip()
        if text == "":
            return None
        lowered = text.lower()
        if lowered == "true":
            return True
        if lowered == "false":
            return False
        if text.startswith("{") or text.startswith("["):
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return text
        if _INT_PATTERN.match(text):
            try:
                return int(text)
            except ValueError:
                return text
        if _FLOAT_PATTERN.match(text):
            try:
                return float(text)
            except ValueError:
                return text
        if _COMMA_FLOAT_PATTERN.match(text):
            try:
                return float(text.replace(",", "."))
            except ValueError:
                return text
        try:
            if len(text) == 10 and text[4] == "-" and text[7] == "-":
                return date.fromisoformat(text)
            if len(text) >= 16 and "T" in text:
                return datetime.fromisoformat(text)
        except ValueError:
            return text
        return text

    @classmethod
    def _parse_row(cls, row: dict[str, str]) -> dict[str, Any]:
        return {key: cls._parse_value(value) for key, value in row.items()}

    @staticmethod
    def _stringify_value(value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False)
        return str(value)

    def _read_raw_rows(self, table_name: str) -> tuple[list[str], list[dict[str, str]]]:
        path = self._ensure_file(table_name)
        with self._lock, path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            headers = list(reader.fieldnames or [])
            rows = [dict(row) for row in reader]
        return headers, rows

    def read_all(self, table_name: str) -> list[dict[str, Any]]:
        _, rows = self._read_raw_rows(table_name)
        return [self._parse_row(row) for row in rows]

    def write_all(self, table_name: str, rows: Iterable[dict[str, Any]]) -> None:
        rows_list = [dict(row) for row in rows]
        headers: list[str] = []
        if rows_list:
            for row in rows_list:
                for key in row.keys():
                    if key not in headers:
                        headers.append(key)
        else:
            headers, _ = self._read_raw_rows(table_name)

        path = self._ensure_file(table_name)
        with self._lock, path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=headers)
            writer.writeheader()
            for row in rows_list:
                writer.writerow({key: self._stringify_value(row.get(key)) for key in headers})

    def get_by_id(self, table_name: str, record_id: int | str) -> dict[str, Any] | None:
        record_id_text = str(record_id)
        for row in self.read_all(table_name):
            if str(row.get("id")) == record_id_text:
                return row
        return None

    def filter(self, table_name: str, **filters: Any) -> list[dict[str, Any]]:
        def _matches(row: dict[str, Any]) -> bool:
            for key, expected in filters.items():
                if expected is None:
                    continue
                actual = row.get(key)
                if isinstance(expected, (list, tuple, set, frozenset)):
                    if actual not in expected:
                        return False
                elif actual != expected:
                    return False
            return True

        return [row for row in self.read_all(table_name) if _matches(row)]

    def _next_id(self, rows: list[dict[str, Any]]) -> int:
        current = [int(row["id"]) for row in rows if row.get("id") is not None]
        return (max(current) if current else 0) + 1

    def create(self, table_name: str, data: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            rows = self.read_all(table_name)
            record = dict(data)
            record.setdefault("id", self._next_id(rows))
            rows.append(record)
            self.write_all(table_name, rows)
            return record

    def update(self, table_name: str, record_id: int | str, data: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            rows = self.read_all(table_name)
            updated: dict[str, Any] | None = None
            for index, row in enumerate(rows):
                if str(row.get("id")) != str(record_id):
                    continue
                rows[index] = {**row, **data, "id": row.get("id")}
                updated = rows[index]
                break
            if updated is None:
                raise KeyError(f"{table_name}:{record_id} not found")
            self.write_all(table_name, rows)
            return updated

    def soft_delete(self, table_name: str, record_id: int | str) -> dict[str, Any]:
        with self._lock:
            rows = self.read_all(table_name)
            updated: dict[str, Any] | None = None
            for index, row in enumerate(rows):
                if str(row.get("id")) != str(record_id):
                    continue
                replacement = dict(row)
                if "active" in replacement:
                    replacement["active"] = False
                elif "status" in replacement:
                    replacement["status"] = "deleted"
                rows[index] = replacement
                updated = replacement
                break
            if updated is None:
                raise KeyError(f"{table_name}:{record_id} not found")
            self.write_all(table_name, rows)
            return updated
