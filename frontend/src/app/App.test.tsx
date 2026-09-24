import { render, screen } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router";
import { describe, expect, it } from "vitest";

import { routes } from "./router";

describe("app at /", () => {
  it("shows the brand header: the Qaracter logo and the product name", () => {
    render(<RouterProvider router={createMemoryRouter(routes, { initialEntries: ["/"] })} />);

    expect(screen.getByRole("img", { name: "Qaracter" })).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { level: 1, name: "Qaracter · Story Maker" }),
    ).toBeInTheDocument();
  });
});
