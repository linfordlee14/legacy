import { render, screen } from "@testing-library/react";

import { EnvFooter } from "./EnvFooter";

describe("EnvFooter (DEP-06)", () => {
  it.each(["local", "staging"])("shows the %s environment", (env) => {
    render(<EnvFooter environment={env} />);
    expect(screen.getByTestId("env-footer")).toHaveTextContent(`environment: ${env}`);
  });

  it("renders nothing in production", () => {
    const { container } = render(<EnvFooter environment="production" />);
    expect(container).toBeEmptyDOMElement();
  });

  it("makes a missing value visible instead of hiding it", () => {
    render(<EnvFooter environment={undefined} />);
    expect(screen.getByTestId("env-footer")).toHaveTextContent("environment: unset");
  });
});
