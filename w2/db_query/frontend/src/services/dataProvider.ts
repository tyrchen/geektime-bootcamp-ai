/** Refine data provider for database query tool. */

import { DataProvider } from "@refinedev/core";
import { apiClient } from "./api";
import { DatabaseConnection, DatabaseConnectionInput } from "../types/database";

export const dataProvider: DataProvider = {
  getList: async ({ resource }) => {
    if (resource === "databases") {
      const response = await apiClient.get<DatabaseConnection[]>(
        "/api/v1/dbs"
      );
      return {
        data: response.data as any,
        total: response.data.length,
      };
    }

    throw new Error(`Unknown resource: ${resource}`);
  },

  getOne: async ({ resource, id }) => {
    if (resource === "databases") {
      const response = await apiClient.get(`/api/v1/dbs/${id}`);
      return {
        data: response.data as any,
      };
    }

    throw new Error(`Unknown resource: ${resource}`);
  },

  create: async ({ resource, variables }) => {
    if (resource === "databases") {
      const input = variables as DatabaseConnectionInput & { name: string };
      if (!input.name) {
        throw new Error("Database name is required");
      }
      const response = await apiClient.put<DatabaseConnection>(
        `/api/v1/dbs/${input.name}`,
        {
          url: input.url,
          description: input.description,
        }
      );
      return {
        data: response.data as any,
      };
    }

    throw new Error(`Unknown resource: ${resource}`);
  },

  update: async ({ resource, id, variables }) => {
    if (resource === "databases") {
      const input = variables as DatabaseConnectionInput;
      const response = await apiClient.put<DatabaseConnection>(
        `/api/v1/dbs/${id}`,
        {
          url: input.url,
          description: input.description,
        }
      );
      return {
        data: response.data as any,
      };
    }

    throw new Error(`Unknown resource: ${resource}`);
  },

  deleteOne: async ({ resource, id }) => {
    if (resource === "databases") {
      await apiClient.delete(`/api/v1/dbs/${id}`);
      return {
        data: { id } as any,
      };
    }

    throw new Error(`Unknown resource: ${resource}`);
  },

  getApiUrl: () => {
    return apiClient.defaults.baseURL || "";
  },
};
