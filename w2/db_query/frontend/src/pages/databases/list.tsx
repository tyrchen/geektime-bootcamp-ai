/** Database list page. */

import React from "react";
import { List, useTable, EditButton, ShowButton, DeleteButton } from "@refinedev/antd";
import { Table, Space, Button } from "antd";
import { PlusOutlined } from "@ant-design/icons";
import { useNavigation } from "@refinedev/core";
import { DatabaseConnection } from "../../types/database";

export const DatabaseList: React.FC = () => {
  const { tableProps } = useTable<DatabaseConnection>({
    resource: "databases",
  });

  const { create } = useNavigation();

  return (
    <List
      headerButtons={({ defaultButtons }) => (
        <>
          {defaultButtons}
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => create("databases")}
          >
            Add Database
          </Button>
        </>
      )}
    >
      <Table {...tableProps} rowKey="name">
        <Table.Column dataIndex="name" title="Name" />
        <Table.Column dataIndex="url" title="URL" ellipsis />
        <Table.Column dataIndex="description" title="Description" />
        <Table.Column
          dataIndex="status"
          title="Status"
          render={(value: string) => (
            <span
              style={{
                color:
                  value === "active"
                    ? "green"
                    : value === "error"
                    ? "red"
                    : "gray",
              }}
            >
              {value}
            </span>
          )}
        />
        <Table.Column
          title="Actions"
          dataIndex="actions"
          render={(_, record: DatabaseConnection) => (
            <Space>
              <ShowButton hideText size="small" recordItemId={record.name} resource="databases" />
              <EditButton hideText size="small" recordItemId={record.name} resource="databases" />
              <DeleteButton hideText size="small" recordItemId={record.name} resource="databases" />
            </Space>
          )}
        />
      </Table>
    </List>
  );
};
