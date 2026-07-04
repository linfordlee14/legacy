import { highlightSegments } from "./search";

describe("highlightSegments (MVP-018 snippet highlighting)", () => {
  it("highlights query terms case-insensitively", () => {
    const segments = highlightSegments("The Zebra fact everyone may read.", "zebra fact");
    const highlighted = segments.filter((segment) => segment.highlight);
    expect(highlighted.map((segment) => segment.text)).toEqual(["Zebra", "fact"]);
    expect(segments.map((segment) => segment.text).join("")).toBe(
      "The Zebra fact everyone may read.",
    );
  });

  it("ignores short and punctuation-only terms", () => {
    const segments = highlightSegments("a be sea", "a be !!");
    expect(segments).toEqual([{ text: "a be sea", highlight: false }]);
  });

  it("escapes regex metacharacters in terms", () => {
    const segments = highlightSegments("cost is $12 (approx)", "(approx)");
    expect(segments.some((segment) => segment.highlight && segment.text === "approx")).toBe(
      true,
    );
  });
});
