/** Database connection types. */

export interface DatabaseConnection {
  name: string;
  url: string;
  description?: string | null;
  createdAt: string;
  updatedAt: string;
  lastConnectedAt?: string | null;
  status: "active" | "inactive" | "error";
}

export interface DatabaseConnectionInput {
  url: string;
  description?: string | null;
}
