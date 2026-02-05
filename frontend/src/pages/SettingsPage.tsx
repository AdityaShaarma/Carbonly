import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "react-query";
import { z } from "zod";
import {
  fetchCompany,
  updateCompany,
  updatePreferences,
  deleteCompanyData,
} from "@/api/company";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Label } from "@/components/ui/Label";
import { Select } from "@/components/ui/Select";
import toast from "react-hot-toast";
import { Link } from "react-router-dom";

const companySchema = z.object({
  name: z.string().min(1),
  industry: z.string().optional(),
  employee_count: z.number().int().positive().optional().nullable(),
  hq_location: z.string().optional(),
  reporting_year: z.number().int().positive(),
});

export function SettingsPage() {
  const queryClient = useQueryClient();
  const { data: company, isLoading, error } = useQuery("company", fetchCompany);

  const [name, setName] = useState("");
  const [industry, setIndustry] = useState("");
  const [employeeCount, setEmployeeCount] = useState("");
  const [hqLocation, setHqLocation] = useState("");
  const [reportingYear, setReportingYear] = useState(2025);
  const [emailNotifications, setEmailNotifications] = useState(true);
  const [monthlySummaries, setMonthlySummaries] = useState(true);
  const [unitSystem, setUnitSystem] = useState("metric_tco2e");

  useEffect(() => {
    if (company) {
      setName(company.name);
      setIndustry(company.industry ?? "");
      setEmployeeCount(company.employee_count?.toString() ?? "");
      setHqLocation(company.hq_location ?? "");
      setReportingYear(company.reporting_year);
      setEmailNotifications(company.email_notifications);
      setMonthlySummaries(company.monthly_summary_reports);
      setUnitSystem(company.unit_system);
    }
  }, [company]);

  const updateCompanyMutation = useMutation(
    () =>
      updateCompany({
        name,
        industry: industry || undefined,
        employee_count: employeeCount ? parseInt(employeeCount, 10) : undefined,
        hq_location: hqLocation || undefined,
        reporting_year: reportingYear,
      }),
    {
      onSuccess: () => {
        queryClient.invalidateQueries("company");
        toast.success("Company updated");
      },
      onError: () => toast.error("Update failed"),
    }
  );

  const updatePrefsMutation = useMutation(
    () =>
      updatePreferences({
        email_notifications: emailNotifications,
        monthly_summary_reports: monthlySummaries,
        unit_system: unitSystem,
      }),
    {
      onSuccess: () => {
        queryClient.invalidateQueries("company");
        toast.success("Preferences updated");
      },
      onError: () => toast.error("Update failed"),
    }
  );

  const deleteDataMutation = useMutation(() => deleteCompanyData(true), {
    onSuccess: () => {
      queryClient.invalidateQueries("company");
      toast.success("Data deleted");
    },
    onError: () => toast.error("Delete failed"),
  });

  const handleSaveCompany = (e: React.FormEvent) => {
    e.preventDefault();
    const result = companySchema.safeParse({
      name,
      industry: industry || undefined,
      employee_count: employeeCount ? parseInt(employeeCount, 10) : null,
      hq_location: hqLocation || undefined,
      reporting_year: reportingYear,
    });
    if (!result.success) {
      toast.error(result.error.errors[0].message);
      return;
    }
    updateCompanyMutation.mutate();
  };

  const handleSavePrefs = (e: React.FormEvent) => {
    e.preventDefault();
    updatePrefsMutation.mutate();
  };

  if (error)
    return <p className="text-destructive">Failed to load settings.</p>;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Settings</h1>

      <Card>
        <CardHeader>
          <CardTitle>Company</CardTitle>
          <CardDescription>Profile and reporting year</CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="h-32 animate-pulse rounded bg-muted" />
          ) : (
            <form
              onSubmit={handleSaveCompany}
              className="grid gap-4 sm:grid-cols-2"
            >
              <div>
                <Label>Company name</Label>
                <Input value={name} onChange={(e) => setName(e.target.value)} />
              </div>
              <div>
                <Label>Industry</Label>
                <Input
                  value={industry}
                  onChange={(e) => setIndustry(e.target.value)}
                  placeholder="e.g. SaaS"
                />
              </div>
              <div>
                <Label>Employee count</Label>
                <Input
                  type="number"
                  min={1}
                  value={employeeCount}
                  onChange={(e) => setEmployeeCount(e.target.value)}
                />
              </div>
              <div>
                <Label>HQ location</Label>
                <Input
                  value={hqLocation}
                  onChange={(e) => setHqLocation(e.target.value)}
                />
              </div>
              <div>
                <Label>Reporting year</Label>
                <Input
                  type="number"
                  min={2020}
                  max={2030}
                  value={reportingYear}
                  onChange={(e) =>
                    setReportingYear(parseInt(e.target.value, 10))
                  }
                />
              </div>
              <div className="sm:col-span-2">
                <Button
                  type="submit"
                  isLoading={updateCompanyMutation.isLoading}
                >
                  Save company
                </Button>
              </div>
            </form>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Preferences</CardTitle>
          <CardDescription>Notifications and units</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSavePrefs} className="space-y-4">
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="emailNotif"
                checked={emailNotifications}
                onChange={(e) => setEmailNotifications(e.target.checked)}
                className="rounded border-input"
              />
              <Label htmlFor="emailNotif">Email notifications</Label>
            </div>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="monthlySum"
                checked={monthlySummaries}
                onChange={(e) => setMonthlySummaries(e.target.checked)}
                className="rounded border-input"
              />
              <Label htmlFor="monthlySum">Monthly summary reports</Label>
            </div>
            <div>
              <Label>Unit system</Label>
              <Select
                value={unitSystem}
                onChange={(e) => setUnitSystem(e.target.value)}
                className="w-48"
              >
                <option value="metric_tco2e">Metric (tCO₂e)</option>
              </Select>
            </div>
            <Button type="submit" isLoading={updatePrefsMutation.isLoading}>
              Save preferences
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Methodology</CardTitle>
          <CardDescription>
            Learn how Carbonly calculates emissions
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Link
            to="/methodology"
            className="text-sm text-primary hover:underline"
          >
            View methodology
          </Link>
        </CardContent>
      </Card>

      <Card className="border-destructive/50">
        <CardHeader>
          <CardTitle className="text-destructive">Danger zone</CardTitle>
          <CardDescription>
            Delete all company data (activities, estimates, reports)
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button
            variant="destructive"
            onClick={() => {
              if (window.confirm("Delete all data? This cannot be undone.")) {
                deleteDataMutation.mutate();
              }
            }}
            disabled={deleteDataMutation.isLoading}
          >
            Delete all data
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
