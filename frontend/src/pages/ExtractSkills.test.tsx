import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { extractionApi, positionsApi } from "@/api/client";
import { mockExtractionResult, mockPositions } from "@/test/fixtures";
import ExtractSkills from "./ExtractSkills";

vi.mock("@/api/client");

describe("ExtractSkills", () => {
  beforeEach(() => {
    vi.mocked(positionsApi.list).mockResolvedValue(mockPositions);
    vi.mocked(extractionApi.extract).mockResolvedValue(mockExtractionResult);
  });

  it("renders page heading", () => {
    render(<MemoryRouter><ExtractSkills /></MemoryRouter>);
    expect(screen.getByText("Extract Skills from Job Description")).toBeInTheDocument();
  });

  it("renders JD textarea and extract button", () => {
    render(<MemoryRouter><ExtractSkills /></MemoryRouter>);
    expect(screen.getByPlaceholderText(/Paste the full job description/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Extract Skills/i })).toBeInTheDocument();
  });

  it("extract button is disabled when textarea is empty", () => {
    render(<MemoryRouter><ExtractSkills /></MemoryRouter>);
    expect(screen.getByRole("button", { name: /Extract Skills/i })).toBeDisabled();
  });

  it("calls extractionApi.extract with the JD text on submit", async () => {
    render(<MemoryRouter><ExtractSkills /></MemoryRouter>);
    const textarea = screen.getByPlaceholderText(/Paste the full job description/i);
    await userEvent.type(textarea, "We need a React developer with TypeScript experience.");
    await userEvent.click(screen.getByRole("button", { name: /Extract Skills/i }));

    expect(vi.mocked(extractionApi.extract)).toHaveBeenCalledWith(
      "We need a React developer with TypeScript experience."
    );
  });

  it("shows extracted skills after successful extraction", async () => {
    render(<MemoryRouter><ExtractSkills /></MemoryRouter>);
    await userEvent.type(
      screen.getByPlaceholderText(/Paste the full job description/i),
      "Looking for a senior React developer."
    );
    await userEvent.click(screen.getByRole("button", { name: /Extract Skills/i }));

    expect(await screen.findByText("Extracted Skills (2)")).toBeInTheDocument();
    expect(screen.getByText("React")).toBeInTheDocument();
    expect(screen.getByText("Node.js")).toBeInTheDocument();
  });

  it("shows AI summary after extraction", async () => {
    render(<MemoryRouter><ExtractSkills /></MemoryRouter>);
    await userEvent.type(
      screen.getByPlaceholderText(/Paste the full job description/i),
      "Looking for a senior React developer."
    );
    await userEvent.click(screen.getByRole("button", { name: /Extract Skills/i }));

    expect(await screen.findByText("AI Summary")).toBeInTheDocument();
    expect(screen.getByText(/Full-stack position/i)).toBeInTheDocument();
  });

  it("shows apply-to-position panel after extraction", async () => {
    render(<MemoryRouter><ExtractSkills /></MemoryRouter>);
    await userEvent.type(
      screen.getByPlaceholderText(/Paste the full job description/i),
      "Looking for a senior React developer."
    );
    await userEvent.click(screen.getByRole("button", { name: /Extract Skills/i }));

    expect(await screen.findByText("Apply to Position")).toBeInTheDocument();
    expect(screen.getByText("Senior React Developer — Engineering")).toBeInTheDocument();
  });
});
