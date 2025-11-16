/** Database metadata tree view component. */

import React from "react";
import { Tree, Tag } from "antd";
import { DatabaseMetadata, TableMetadata } from "../types/metadata";

interface MetadataTreeProps {
  metadata: DatabaseMetadata;
}

export const MetadataTree: React.FC<MetadataTreeProps> = ({ metadata }) => {
  const { tables, views } = metadata;

  const buildTreeData = (items: TableMetadata[], type: "table" | "view") => {
    return items.map((item) => ({
      title: (
        <span>
          {item.name}
          <Tag color={type === "table" ? "blue" : "green"} style={{ marginLeft: 8 }}>
            {type}
          </Tag>
          {item.rowCount !== null && item.rowCount !== undefined && (
            <Tag color="default" style={{ marginLeft: 4 }}>
              {item.rowCount} rows
            </Tag>
          )}
        </span>
      ),
      key: `${type}-${item.name}`,
      children: item.columns.map((col) => ({
        title: (
          <span>
            <strong>{col.name}</strong>
            <Tag color="default" style={{ marginLeft: 8 }}>
              {col.dataType}
            </Tag>
            {col.primaryKey && (
              <Tag color="red" style={{ marginLeft: 4 }}>
                PK
              </Tag>
            )}
            {col.unique && (
              <Tag color="orange" style={{ marginLeft: 4 }}>
                UNIQUE
              </Tag>
            )}
            {!col.nullable && (
              <Tag color="purple" style={{ marginLeft: 4 }}>
                NOT NULL
              </Tag>
            )}
          </span>
        ),
        key: `${type}-${item.name}-${col.name}`,
      })),
    }));
  };

  const treeData = [
    {
      title: "Tables",
      key: "tables",
      children: buildTreeData(tables, "table"),
    },
    {
      title: "Views",
      key: "views",
      children: buildTreeData(views, "view"),
    },
  ];

  return (
    <Tree
      treeData={treeData}
      defaultExpandAll={false}
      showLine={{ showLeafIcon: false }}
    />
  );
};
