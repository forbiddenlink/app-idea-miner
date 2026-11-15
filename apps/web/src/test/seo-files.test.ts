import { describe, expect, it } from "vitest";
import { existsSync, readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";

const HOST = "https://app-idea-miner.vercel.app";
const here = path.dirname(fileURLToPath(import.meta.url));
const webRoot = path.resolve(here, "../..");
const read = (p: string) => readFileSync(path.resolve(webRoot, p), "utf8");

describe("robots.txt", () => {
  it("exists in public/ and points at the sitemap on the live host", () => {
    expect(existsSync(path.resolve(webRoot, "public/robots.txt"))).toBe(true);
    const robots = read("public/robots.txt");
    expect(robots).toMatch(/^User-agent: \*/m);
    expect(robots).toContain(`Sitemap: ${HOST}/sitemap.xml`);
    expect(robots).toMatch(/^Disallow: \/api\//m);
  });
});

describe("sitemap.xml", () => {
  it("lists the public routes from App.tsx on the live host", () => {
    expect(existsSync(path.resolve(webRoot, "public/sitemap.xml"))).toBe(true);
    const locs = [...read("public/sitemap.xml").matchAll(/<loc>([^<]+)<\/loc>/g)].map(
      (m) => m[1],
    );
    for (const route of ["", "/clusters", "/ideas", "/analytics", "/opportunities"]) {
      expect(locs).toContain(`${HOST}${route}`);
    }
  });

  it("omits login, saved and settings and parameterised pages", () => {
    const xml = read("public/sitemap.xml");
    expect(xml).not.toMatch(/\/(login|saved|settings)</);
    expect(xml).not.toContain(":id");
  });
});

describe("vercel.json", () => {
  const vercel = JSON.parse(readFileSync(path.resolve(webRoot, "../../vercel.json"), "utf8")) as {
    routes: { src?: string }[];
  };
  const staticRoute = vercel.routes.find((r) => r.src?.includes("favicon"));

  it("serves robots.txt and sitemap.xml as static files, not the SPA 404", () => {
    expect(staticRoute).toBeDefined();
    const re = new RegExp(`^${staticRoute?.src}$`);
    expect(re.test("/robots.txt")).toBe(true);
    expect(re.test("/sitemap.xml")).toBe(true);
  });
});
