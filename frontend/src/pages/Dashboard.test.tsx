import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { candidatesApi, positionsApi } from "@/api/client";
import { mockCandidates, mockPositions } from "@/test/fixtures";
import Dashboard from "./Dashboard";

vi.mock("@/api/client");

describe("Dashboard", () => {
  beforeEach(() => {
    vi.mocked(candidatesApi.list).mockResolvedValue(mockCandidates);
    vi.mocked(positionsApi.list).mockResolvedValue(mockPositions);
  });

  it("shows total candidates count", async () => {
    render(<MemoryRouter><Dashboard /></MemoryRouter>);
    expect(await screen.findByText("Total Candidates")).toBeInTheDocument();
    const cards = screen.getAllByText("2");
    expect(cards.length).toBeGreaterThanOrEqual(1);
  });

  it("renders recent candidate names", async () => {
    render(<MemoryRouter><Dashboard /></MemoryRouter>);
    expect(await screen.findByText("Alice Johnson")).toBeInTheDocument();
    expect(screen.getByText("Bob Martinez")).toBeInTheDocument();
  });

  it("renders open positions quick view", async () => {
    render(<MemoryRouter><Dashboard /></MemoryRouter>);
    expect(await screen.findByText("Senior React Developer")).toBeInTheDocument();
    expect(screen.getByText("Python Backend Engineer")).toBeInTheDocument();
  });
});
