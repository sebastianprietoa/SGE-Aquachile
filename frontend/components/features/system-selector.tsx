"use client";

import { Select } from "@/components/ui/select";
import type { EnergySystem } from "@/types/api";

export function SystemSelector({
  systems,
  value,
  onChange,
}: {
  systems: EnergySystem[];
  value: number | null;
  onChange: (value: number) => void;
}) {
  return (
    <Select value={value ? String(value) : ""} onChange={(event) => onChange(Number(event.target.value))}>
      {systems.map((system) => (
        <option key={system.id} value={system.id}>
          {system.code} - {system.name}
        </option>
      ))}
    </Select>
  );
}

