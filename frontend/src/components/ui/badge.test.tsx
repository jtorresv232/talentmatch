import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Badge } from "./badge";

describe("Badge", () => {
  it("renders children", () => {
    render(<Badge>React</Badge>);
    expect(screen.getByText("React")).toBeInTheDocument();
  });

  it("applies success variant class", () => {
    render(<Badge variant="success">Expert</Badge>);
    const el = screen.getByText("Expert");
    expect(el.className).toMatch(/green/);
  });

  it("applies destructive variant class", () => {
    render(<Badge variant="destructive">Missing</Badge>);
    const el = screen.getByText("Missing");
    expect(el.className).toMatch(/destructive/);
  });

  it("applies warning variant class", () => {
    render(<Badge variant="warning">Beginner</Badge>);
    const el = screen.getByText("Beginner");
    expect(el.className).toMatch(/yellow/);
  });

  it("applies additional className", () => {
    render(<Badge className="text-xs">Tag</Badge>);
    expect(screen.getByText("Tag").className).toMatch(/text-xs/);
  });
});
