/** Database metadata types. */

export interface ColumnMetadata {
  name: string;
  dataType: string;
  nullable: boolean;
  primaryKey: boolean;
  unique?: boolean;
  defaultValue?: string | null;
  comment?: string | null;
}

export interface TableMetadata {
  name: string;
  type: "table" | "view";
  columns: ColumnMetadata[];
  rowCount?: number | null;
  schemaName?: string;
}

export interface DatabaseMetadata {
  databaseName: string;
  tables: TableMetadata[];
  views: TableMetadata[];
  fetchedAt: string;
  isStale: boolean;
}
