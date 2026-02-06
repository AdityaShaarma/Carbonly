import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";

export function AboutMethodologyPage() {
  return (
    <div className="min-h-screen bg-muted/30 p-6">
      <div className="mx-auto max-w-3xl space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Methodology</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 text-sm text-muted-foreground">
            <p className="text-foreground">
              Carbonly reports follow the GHG Protocol Corporate Standard and
              use a transparent activity-data approach: emissions are calculated
              as activity data × emission factors.
            </p>
            <div>
              <p className="font-medium text-foreground">Scopes</p>
              <ul className="mt-2 list-disc space-y-1 pl-5">
                <li>
                  <span className="text-foreground">Scope 1:</span> Direct
                  emissions from owned or controlled sources.
                </li>
                <li>
                  <span className="text-foreground">Scope 2:</span> Indirect
                  emissions from purchased electricity, steam, or heat.
                </li>
                <li>
                  <span className="text-foreground">Scope 3:</span> Other
                  indirect emissions across the value chain. For this MVP we
                  focus on cloud services, commuting, travel, remote work, and
                  purchased services.
                </li>
              </ul>
            </div>
            <div>
              <p className="font-medium text-foreground">Data quality</p>
              <ul className="mt-2 list-disc space-y-1 pl-5">
                <li>
                  <span className="text-foreground">Measured:</span> Data from
                  connected sources.
                </li>
                <li>
                  <span className="text-foreground">Estimated:</span> Modeled
                  values based on benchmarks when direct data is unavailable.
                </li>
                <li>
                  <span className="text-foreground">Manual:</span> Values
                  entered by the company.
                </li>
              </ul>
            </div>
            <div>
              <p className="font-medium text-foreground">Emission factors</p>
              <p className="mt-2">
                Emission factors are sourced from recognized references such as
                EPA and DEFRA datasets, as well as cloud provider sustainability
                disclosures. Factor metadata is stored with each estimate to
                keep calculations auditable.
              </p>
            </div>
            <div>
              <p className="font-medium text-foreground">Confidence scoring</p>
              <p className="mt-2">
                Confidence reflects data quality and completeness. Measured data
                receives higher confidence, while estimates are weighted lower.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
