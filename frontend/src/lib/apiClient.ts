import api, { apiClient as existingClient } from "@/services/api";
import { normalizePath } from "./normalizePath";

export const apiClient = existingClient;
export { normalizePath };
export default api;
