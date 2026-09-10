import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { candidatesApi, gapAnalysisApi, positionsApi } from "@/api/client";
import { mockCandidates, mockGapAnalysisResult, mockPositions } from "@/test/fixtures";
import GapAnalysis from "./GapAnalysis";

vi.mock("@/api/client");

describe("GapAnalysis", () => {
  beforeEach(() => {
    vi.mocked(candidatesApi.list).mockResolvedValue(mockCandidates);
    vi.mocked(positionsApi.list).mockResolvedValue(mockPositions);
    vi.mocked(gapAnalysisApi.analyze).mockResolvedValue(mockGapAnalysisResult);
  });

  it("renders page heading and description", async () => {
    render(<MemoryRouter><GapAnalysis /></MemoryRouter>);
    expect(await screen.findByText("Gap Analysis")).toBeInTheDocument();
  });

  it("populates candidate and position selectors", async () => {
    render(<MemoryRouter><GapAnalysis /></MemoryRouter>);
    expect(await screen.findByText("Alice Johnson — Senior Frontend Engineer")).toBeInTheDocument();
    expect(screen.getByText("Senior React Developer — Engineering")).toBeInTheDocument();
  });

  it("run button is disabled when no selections made", async () => {
    render(<MemoryRouter><GapAnalysis /></MemoryRouter>);
    await screen.findByText("Alice Johnson — Senior Frontend Engineer");
    expect(screen.getByRole("button", { name: "Run Gap Analysis" })).toBeDisabled();
  });

  it("shows verdict and score after analysis", async () => {
    render(<MemoryRouter><GapAnalysis /></MemoryRouter>);
    await screen.findByText("Alice Johnson — Senior Frontend Engineer");

    await userEvent.selectOptions(screen.getByLabelText(/candidate/i), "c1");
    await userEvent.selectOptions(screen.getByLabelText(/position/i), "p1");
    await userEvent.click(screen.getByRole("button", { name: "Run Gap Analysis" }));

    expect(await screen.findByText("Strong Match")).toBeInTheDocument();
    expect(screen.getByText("82")).toBeInTheDocument();
  });

  it("shows matched skills bucket", async () => {
    render(<MemoryRouter><GapAnalysis /></MemoryRouter>);
    await screen.findByText("Alice Johnson — Senior Frontend Engineer");

    await userEvent.selectOptions(screen.getByLabelText(/candidate/i), "c1");
    await userEvent.selectOptions(screen.getByLabelText(/position/i), "p1");
    await userEvent.click(screen.getByRole("button", { name: "Run Gap Analysis" }));

    expect(await screen.findByText(/Matched/)).toBeInTheDocument();
    expect(screen.getByText(/Missing/)).toBeInTheDocument();
  });

  it("shows AI recommendations", async () => {
    render(<MemoryRouter><GapAnalysis /></MemoryRouter>);
    await screen.findByText("Alice Johnson — Senior Frontend Engineer");

    await userEvent.selectOptions(screen.getByLabelText(/candidate/i), "c1");
    await userEvent.selectOptions(screen.getByLabelText(/position/i), "p1");
    await userEvent.click(screen.getByRole("button", { name: "Run Gap Analysis" }));

    expect(await screen.findByText("Recommendations")).toBeInTheDocument();
    expect(screen.getByText(/system design/i)).toBeInTheDocument();
  });
});
