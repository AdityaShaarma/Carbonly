import { useQuery } from "react-query";
import { fetchMethodology } from "@/api/methodology";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/Card";

export function MethodologyPage() {
  const { data, isLoading, error } = useQuery("methodology", fetchMethodology);

  if (error)
    return <p className="text-destructive">Failed to load methodology.</p>;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Methodology</h1>
      <Card>
        <CardHeader>
          <CardTitle>How we calculate emissions</CardTitle>
          <CardDescription>
            Transparent methodology for credible disclosures
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4 text-sm">
          {isLoading ? (
            <div className="h-28 animate-pulse rounded bg-muted" />
          ) : (
            <>
              <div>
                <p className="font-medium">Measured vs estimated vs manual</p>
                <p className="text-muted-foreground">
                  {data?.measured_vs_estimated}
                </p>
              </div>
              <div>
                <p className="font-medium">Supported scopes</p>
                <ul className="list-disc pl-4 text-muted-foreground">
                  {data?.supported_scopes?.map((s) => (
                    <li key={s}>{s}</li>
                  ))}
                </ul>
              </div>
              <div>
                <p className="font-medium">Emission factor sources</p>
                <p className="text-muted-foreground">{data?.factors_source}</p>
              </div>
              <div>
                <p className="font-medium">Confidence calculation</p>
                <p className="text-muted-foreground">
                  {data?.confidence_calculation}
                </p>
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
