import { describe, expect, it } from "vitest";
import { inferTaskType, parseCsv } from "./api";

describe("inferTaskType", () => {
  it("detects playlist, channel, and video URLs", () => {
    expect(inferTaskType("https://www.youtube.com/playlist?list=abc123")).toBe("playlist");
    expect(inferTaskType("https://www.youtube.com/@ytgrid")).toBe("channel");
    expect(inferTaskType("https://www.youtube.com/watch?v=abc123")).toBe("video");
  });
});

describe("parseCsv", () => {
  it("parses task CSV rows with loops aliases and inferred task types", () => {
    const rows = parseCsv(
      [
        "session_id,url,speed,loops,task_type",
        "alpha,https://www.youtube.com/watch?v=abc123,1.25,3,",
        "beta,https://www.youtube.com/playlist?list=list123,1,2,playlist",
      ].join("\n"),
    );

    expect(rows).toEqual([
      {
        session_id: "alpha",
        url: "https://www.youtube.com/watch?v=abc123",
        speed: 1.25,
        loop_count: 3,
        task_type: "video",
      },
      {
        session_id: "beta",
        url: "https://www.youtube.com/playlist?list=list123",
        speed: 1,
        loop_count: 2,
        task_type: "playlist",
      },
    ]);
  });

  it("keeps commas inside quoted CSV fields", () => {
    const rows = parseCsv('session_id,url,speed,loops\nquoted,"https://www.youtube.com/watch?v=a,b",1,1');

    expect(rows[0]).toMatchObject({
      session_id: "quoted",
      url: "https://www.youtube.com/watch?v=a,b",
      task_type: "video",
    });
  });

  it("rejects missing URLs, invalid speeds, and invalid task types", () => {
    expect(() => parseCsv("session_id,url\nbad,")).toThrow("CSV row 2 is missing url");
    expect(() => parseCsv("url,speed\nhttps://www.youtube.com/watch?v=abc,fast")).toThrow(
      "CSV row 2 has invalid speed",
    );
    expect(() => parseCsv("url,task_type\nhttps://www.youtube.com/watch?v=abc,live")).toThrow(
      "CSV row 2 has invalid task_type",
    );
  });
});
