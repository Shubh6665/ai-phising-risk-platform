import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import { AnalysisForm } from "../src/components/AnalysisForm";

describe("AnalysisForm Component", () => {
  it("renders form controls, labels, and accessible placeholders", () => {
    render(
      <AnalysisForm
        onSubmit={vi.fn()}
        isLoading={false}
        onReset={vi.fn()}
        hasResult={false}
      />
    );

    expect(screen.getByRole("button", { name: /Analyze Email/i })).toBeInTheDocument();
    // textarea has aria-label="Email Body Content"
    expect(screen.getByRole("textbox", { name: /Email Body Content/i })).toBeInTheDocument();
  });

  it("prevents submission and displays validation error on empty text", async () => {
    const handleSubmit = vi.fn();
    render(
      <AnalysisForm
        onSubmit={handleSubmit}
        isLoading={false}
        onReset={vi.fn()}
        hasResult={false}
      />
    );

    const submitBtn = screen.getByRole("button", { name: /Analyze Email/i });
    fireEvent.click(submitBtn);

    expect(handleSubmit).not.toHaveBeenCalled();
    expect(
      screen.getByText(/Email body text cannot be empty or whitespace only/i)
    ).toBeInTheDocument();
  });

  it("submits valid email content", async () => {
    const handleSubmit = vi.fn().mockResolvedValue(undefined);
    render(
      <AnalysisForm
        onSubmit={handleSubmit}
        isLoading={false}
        onReset={vi.fn()}
        hasResult={false}
      />
    );

    const bodyInput = screen.getByRole("textbox", { name: /Email Body Content/i });
    const submitBtn = screen.getByRole("button", { name: /Analyze Email/i });

    await userEvent.type(bodyInput, "Please confirm your direct deposit details immediately.");
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(handleSubmit).toHaveBeenCalledTimes(1);
      expect(handleSubmit).toHaveBeenCalledWith(
        expect.objectContaining({ text: "Please confirm your direct deposit details immediately." })
      );
    });
  });

  it("prevents duplicate submissions while loading is true", () => {
    const handleSubmit = vi.fn();
    render(
      <AnalysisForm
        onSubmit={handleSubmit}
        isLoading={true}
        onReset={vi.fn()}
        hasResult={false}
      />
    );

    const submitBtn = screen.getByRole("button", { name: /Analyzing/i });
    expect(submitBtn).toBeDisabled();
    fireEvent.click(submitBtn);
    expect(handleSubmit).not.toHaveBeenCalled();
  });

  it("loads pre-configured phishing sample email", () => {
    render(
      <AnalysisForm
        onSubmit={vi.fn()}
        isLoading={false}
        onReset={vi.fn()}
        hasResult={false}
      />
    );

    const phishingBtn = screen.getByRole("button", { name: /Phishing sample/i });
    fireEvent.click(phishingBtn);

    const bodyInput = screen.getByRole("textbox", { name: /Email Body Content/i }) as HTMLTextAreaElement;
    expect(bodyInput.value).toContain("http://192.168.1.100:8080");
  });

  it("clears inputs and invokes onReset when Clear button is clicked", async () => {
    const handleReset = vi.fn();
    render(
      <AnalysisForm
        onSubmit={vi.fn()}
        isLoading={false}
        onReset={handleReset}
        hasResult={true}
      />
    );

    const bodyInput = screen.getByRole("textbox", { name: /Email Body Content/i });
    await userEvent.type(bodyInput, "Test email body");

    const clearBtn = screen.getByRole("button", { name: /Clear/i });
    fireEvent.click(clearBtn);

    expect(handleReset).toHaveBeenCalledTimes(1);
    expect((bodyInput as HTMLTextAreaElement).value).toBe("");
  });
});
