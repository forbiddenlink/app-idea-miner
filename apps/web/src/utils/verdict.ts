/** The API verdicts join two clauses with an em dash; show them with a colon. */
export function formatVerdict(verdict: string): string {
  return verdict.replace(/\s+\u2014\s+/g, ": ");
}
