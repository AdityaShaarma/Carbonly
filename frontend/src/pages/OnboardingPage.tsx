import { OnboardingChecklist } from "@/components/onboarding/OnboardingChecklist";

export function OnboardingPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Get started</h1>
      <OnboardingChecklist />
    </div>
  );
}
