const numberFormatter = new Intl.NumberFormat("en-US", {
  maximumFractionDigits: 2,
});

export function formatNumber(value: number): string {
  return numberFormatter.format(value);
}

export function formatKgToTons(valueKg: number, decimals = 2): string {
  const tons = valueKg / 1000;
  return new Intl.NumberFormat("en-US", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(tons);
}

export function formatKg(valueKg: number): string {
  return `${formatNumber(valueKg)} kg CO₂e`;
}

export function formatEmissions(valueKg: number): string {
  if (valueKg >= 1000) {
    return `${formatKgToTons(valueKg)} tCO₂e`;
  }
  return `${formatNumber(valueKg)} kg CO₂e`;
}
