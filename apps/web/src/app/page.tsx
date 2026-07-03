import Link from "next/link";

export default function HomePage() {
  return (
    <section>
      <h1>Legacy</h1>
      <p>Your Life. Your Knowledge. Your Impact. Preserved Forever.</p>
      <p>
        <Link href="/dashboard">Enter the workspace</Link>
      </p>
    </section>
  );
}
