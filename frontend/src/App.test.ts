import { mount } from "@vue/test-utils";
import { describe, expect, it, vi } from "vitest";

import App from "./App.vue";

vi.stubGlobal(
  "fetch",
  vi.fn(async () => ({
    ok: true,
    json: async () => []
  }))
);

describe("App", () => {
  it("presents the planning workflow and safety disclaimer", () => {
    const wrapper = mount(App);
    expect(wrapper.text()).toContain("Aircraft envelope");
    expect(wrapper.text()).toContain("Mission route");
    expect(wrapper.text()).toContain("not a certified aviation safety system");
  });
});
