import { useState } from "react";
import { useMutation, useQueryClient } from "react-query";
import { z } from "zod";
import { createManualActivity, uploadCsv } from "@/api/integrations";
import { updateOnboarding } from "@/api/onboarding";
import { useYearSelector } from "@/hooks/useYearSelector";
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

const schema = z.object({
  scope: z.number().min(1).max(3),
  scope_3_category: z.string().optional(),
  activity_type: z.string().min(1),
  quantity: z.number().positive(),
  unit: z.string().min(1),
  period_start: z.string(),
  period_end: z.string(),
  data_quality: z.enum(["measured", "estimated", "manual"]),
  assumptions: z.string().optional(),
  confidence_score: z.number().min(0).max(100).optional(),
});

export function ManualDataPage() {
  const queryClient = useQueryClient();
  const { year } = useYearSelector();

  const [scope, setScope] = useState(3);
  const [scope3Cat, setScope3Cat] = useState("");
  const [activityType, setActivityType] = useState("");
  const [quantity, setQuantity] = useState("");
  const [unit, setUnit] = useState("");
  const [periodStart, setPeriodStart] = useState(`${year}-01-01`);
  const [periodEnd, setPeriodEnd] = useState(`${year}-12-31`);
  const [dataQuality, setDataQuality] = useState("manual");
  const [assumptions, setAssumptions] = useState("");
  const [confidence, setConfidence] = useState("");

  const create = useMutation(
    () =>
      createManualActivity({
        scope,
        scope_3_category: scope3Cat || undefined,
        activity_type: activityType,
        quantity: parseFloat(quantity),
        unit,
        period_start: periodStart,
        period_end: periodEnd,
        data_quality: dataQuality as "measured" | "estimated" | "manual",
        assumptions: assumptions || undefined,
        confidence_score: confidence ? parseFloat(confidence) : undefined,
      }),
    {
      onSuccess: async () => {
        queryClient.invalidateQueries(["dashboard", year]);
        await updateOnboarding({ add_manual_activity: true });
        queryClient.invalidateQueries("onboarding");
        toast.success("Activity created");
        setQuantity("");
        setActivityType("");
      },
      onError: () => toast.error("Failed to create activity"),
    }
  );

  const [file, setFile] = useState<File | null>(null);
  const [uploadResult, setUploadResult] = useState<{
    inserted: number;
    errors: { row: number; error: string }[];
  } | null>(null);

  const upload = useMutation(
    () => {
      if (!file) throw new Error("No file");
      return uploadCsv(file);
    },
    {
      onSuccess: async (data) => {
        setUploadResult(data);
        queryClient.invalidateQueries(["dashboard", year]);
        if (data.inserted > 0) {
          await updateOnboarding({ upload_csv: true });
          queryClient.invalidateQueries("onboarding");
        }
        if (data.inserted > 0) toast.success(`Inserted ${data.inserted} rows`);
        if (data.errors.length > 0)
          toast.error(`${data.errors.length} row(s) had errors`);
        setFile(null);
      },
      onError: () => toast.error("Upload failed"),
    }
  );

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const result = schema.safeParse({
      scope,
      scope_3_category: scope3Cat || undefined,
      activity_type: activityType,
      quantity: parseFloat(quantity),
      unit,
      period_start: periodStart,
      period_end: periodEnd,
      data_quality: dataQuality,
      assumptions: assumptions || undefined,
      confidence_score: confidence ? parseFloat(confidence) : undefined,
    });
    if (!result.success) {
      toast.error(result.error.errors[0].message);
      return;
    }
    create.mutate();
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Manual Data</h1>

      <Card>
        <CardHeader>
          <CardTitle>Single activity</CardTitle>
          <CardDescription>Add one activity record manually</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="grid gap-4 sm:grid-cols-2">
            <div>
              <Label>Scope</Label>
              <Select
                value={scope}
                onChange={(e) => setScope(Number(e.target.value))}
              >
                <option value={1}>1</option>
                <option value={2}>2</option>
                <option value={3}>3</option>
              </Select>
            </div>
            {scope === 3 && (
              <div>
                <Label>Scope 3 category</Label>
                <Input
                  placeholder="e.g. cloud, travel"
                  value={scope3Cat}
                  onChange={(e) => setScope3Cat(e.target.value)}
                />
              </div>
            )}
            <div>
              <Label>Activity type</Label>
              <Input
                value={activityType}
                onChange={(e) => setActivityType(e.target.value)}
                placeholder="e.g. electricity_kwh"
              />
            </div>
            <div>
              <Label>Quantity</Label>
              <Input
                type="number"
                step="any"
                value={quantity}
                onChange={(e) => setQuantity(e.target.value)}
              />
            </div>
            <div>
              <Label>Unit</Label>
              <Input
                value={unit}
                onChange={(e) => setUnit(e.target.value)}
                placeholder="e.g. kWh"
              />
            </div>
            <div>
              <Label>Period start</Label>
              <Input
                type="date"
                value={periodStart}
                onChange={(e) => setPeriodStart(e.target.value)}
              />
            </div>
            <div>
              <Label>Period end</Label>
              <Input
                type="date"
                value={periodEnd}
                onChange={(e) => setPeriodEnd(e.target.value)}
              />
            </div>
            <div>
              <Label>Data quality</Label>
              <Select
                value={dataQuality}
                onChange={(e) => setDataQuality(e.target.value)}
              >
                <option value="manual">Manual</option>
                <option value="estimated">Estimated</option>
                <option value="measured">Measured</option>
              </Select>
            </div>
            <div>
              <Label>Confidence (0–100)</Label>
              <Input
                type="number"
                min={0}
                max={100}
                value={confidence}
                onChange={(e) => setConfidence(e.target.value)}
                placeholder="Optional"
              />
            </div>
            <div className="sm:col-span-2">
              <Label>Assumptions</Label>
              <Input
                value={assumptions}
                onChange={(e) => setAssumptions(e.target.value)}
                placeholder="Optional"
              />
            </div>
            <div className="sm:col-span-2">
              <Button type="submit" isLoading={create.isLoading}>
                Add activity
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>CSV upload</CardTitle>
          <CardDescription>
            Columns: scope, activity_type, quantity, unit, period_start,
            period_end. Optional: scope_3_category, data_quality, assumptions,
            confidence_score
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap items-center gap-2">
            <input
              type="file"
              accept=".csv"
              onChange={(e) => {
                setFile(e.target.files?.[0] ?? null);
                setUploadResult(null);
              }}
              className="text-sm"
            />
            <Button
              onClick={() => upload.mutate()}
              disabled={!file || upload.isLoading}
              isLoading={upload.isLoading}
            >
              Upload
            </Button>
          </div>
          {uploadResult && (
            <div className="rounded-md border border-border p-3 text-sm">
              <p>Inserted: {uploadResult.inserted}</p>
              {uploadResult.errors.length > 0 && (
                <ul className="mt-2 list-disc pl-4 text-destructive">
                  {uploadResult.errors.slice(0, 10).map((e, i) => (
                    <li key={i}>
                      Row {e.row}: {e.error}
                    </li>
                  ))}
                  {uploadResult.errors.length > 10 && (
                    <li>… and {uploadResult.errors.length - 10} more</li>
                  )}
                </ul>
              )}
            </div>
          )}
          {!uploadResult && (
            <div className="rounded-md border border-border p-3 text-sm text-muted-foreground">
              No manual data uploaded yet. Use the form above or upload a CSV to
              get started.
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
