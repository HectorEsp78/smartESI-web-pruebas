interface SectionHeadingProps {
  title: string;
  subtitle: string;
}

export function SectionHeading({ title, subtitle }: SectionHeadingProps) {
  return (
    <div className="mb-5 border-l-4 border-accent pl-4">
      <h2 className="font-heading text-2xl font-extrabold uppercase tracking-[0.08em] text-accent">
        {title}
      </h2>
      <p className="mt-1 text-sm text-muted-foreground">{subtitle}</p>
    </div>
  );
}
