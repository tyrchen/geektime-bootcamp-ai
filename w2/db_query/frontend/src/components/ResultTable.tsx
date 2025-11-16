/** Query result table component with pagination. */

import React, { useState } from "react";
import { Table, Tag } from "antd";
import { QueryResult } from "../types/query";

interface ResultTableProps {
  result: QueryResult | null;
  loading?: boolean;
}

export const ResultTable: React.FC<ResultTableProps> = ({
  result,
  loading = false,
}) => {
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 50,
  });

  if (!result) {
    return null;
  }

  const columns = result.columns.map((col) => ({
    title: col.name,
    dataIndex: col.name,
    key: col.name,
    render: (value: any) => {
      if (value === null || value === undefined) {
        return <Tag color="default">NULL</Tag>;
      }
      if (typeof value === "boolean") {
        return value ? "✓" : "✗";
      }
      if (value instanceof Date) {
        return value.toLocaleString();
      }
      return String(value);
    },
  }));

  const handleTableChange = (newPagination: any) => {
    setPagination({
      current: newPagination.current,
      pageSize: newPagination.pageSize,
    });
  };

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <Tag color="blue">Rows: {result.rowCount}</Tag>
        <Tag color="green">Execution Time: {result.executionTimeMs}ms</Tag>
      </div>
      <Table
        columns={columns}
        dataSource={result.rows.map((row, index) => ({
          ...row,
          key: index,
        }))}
        loading={loading}
        pagination={{
          current: pagination.current,
          pageSize: pagination.pageSize,
          total: result.rowCount,
          showSizeChanger: true,
          showTotal: (total) => `Total ${total} rows`,
          pageSizeOptions: ["10", "50", "100", "500"],
        }}
        onChange={handleTableChange}
        scroll={{ x: "max-content" }}
      />
    </div>
  );
};
