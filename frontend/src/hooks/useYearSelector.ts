import { useMemo, useState } from "react";
import { useAuth } from "@/contexts/AuthContext";

const CURRENT_YEAR = new Date().getFullYear();
const YEARS = Array.from({ length: 6 }, (_, i) => CURRENT_YEAR - 2 + i);

export function useYearSelector() {
  const { company } = useAuth();
  const defaultYear = company?.reporting_year ?? CURRENT_YEAR;
  const [year, setYear] = useState(defaultYear);

  const options = useMemo(() => {
    const set = new Set([...YEARS, defaultYear].sort((a, b) => b - a));
    return Array.from(set);
  }, [defaultYear]);

  return { year, setYear, options };
}
