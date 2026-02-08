export function getReportYears(currentYear: number, pastYears = 9): number[] {
  return Array.from({ length: pastYears + 1 }, (_, i) => currentYear - i);
}
