import { useEffect, useMemo, useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { getReportYears } from "@/utils/years";

export function useYearSelector() {
  const { company } = useAuth();
  const currentYear = new Date().getFullYear();
  const defaultYear = Math.min(company?.reporting_year ?? currentYear, currentYear);
  const [year, setYear] = useState(defaultYear);

  const options = useMemo(() => {
    const years = getReportYears(currentYear, 9);
    return years.includes(defaultYear)
      ? years
      : [defaultYear, ...years].sort((a, b) => b - a);
  }, [currentYear, defaultYear]);

  useEffect(() => {
    if (!options.includes(year)) {
      setYear(options[0]);
    }
  }, [options, year]);

  return { year, setYear, options };
}
