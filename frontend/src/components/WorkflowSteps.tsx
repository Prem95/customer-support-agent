const PIPELINE = [
  { key: "analyze_intent", label: "Read the message" },
  { key: "retrieve_knowledge", label: "Search knowledge" },
  { key: "generate_recommendations", label: "Draft a reply" },
  { key: "update_summary", label: "Update summary" },
];

interface Props {
  doneStages: string[];
  running: boolean;
}

export function WorkflowSteps({ doneStages, running }: Props) {
  if (!running && doneStages.length === 0) return null;

  const failed = doneStages.includes("handle_failure");
  const nextIndex = PIPELINE.findIndex((step) => !doneStages.includes(step.key));

  return (
    <ul className="steps">
      {PIPELINE.map((step, index) => {
        const done = doneStages.includes(step.key);
        const active = running && !failed && index === nextIndex;
        const skipped = !done && !running && doneStages.length > 0;
        return (
          <li key={step.key} className={done ? "step done" : active ? "step active" : "step"}>
            <span className="step-mark">{done ? "✓" : active ? <i className="spinner" /> : "○"}</span>
            <span>{skipped ? `${step.label} (skipped)` : step.label}</span>
          </li>
        );
      })}
      {failed && (
        <li className="step failed">
          <span className="step-mark">!</span>
          <span>Recovered from an error</span>
        </li>
      )}
    </ul>
  );
}
