export function Placeholder({ title, lede }: { title: string; lede: string }) {
  return (
    <section className="rs-page-head">
      <h2>{title}</h2>
      <p>{lede}</p>
    </section>
  );
}
