/** Database metadata tree view component with search and click support. */

import React, { useMemo } from "react";
import { Tree, Tag, Typography } from "antd";
import { DatabaseMetadata, TableMetadata } from "../types/metadata";

const { Text } = Typography;

interface MetadataTreeProps {
  metadata: DatabaseMetadata;
  searchText?: string;
  onTableClick?: (table: TableMetadata) => void;
}

export const MetadataTree: React.FC<MetadataTreeProps> = ({
  metadata,
  searchText = "",
  onTableClick,
}) => {
  const { tables, views } = metadata;

  const filterItems = (items: TableMetadata[]) => {
    if (!searchText) return items;
    const lowerSearch = searchText.toLowerCase();
    return items.filter(
      (item) =>
        item.name.toLowerCase().includes(lowerSearch) ||
        item.columns.some((col) => col.name.toLowerCase().includes(lowerSearch))
    );
  };

  const buildTreeData = (items: TableMetadata[], type: "table" | "view") => {
    const filtered = filterItems(items);
    return filtered.map((item) => ({
      title: (
        <span
          onClick={() => onTableClick?.(item)}
          style={{
            cursor: onTableClick ? "pointer" : "default",
            fontSize: "15px",
            fontWeight: 600,
          }}
        >
          <Text strong style={{ fontSize: "15px" }}>{item.name}</Text>
          <Tag color={type === "table" ? "blue" : "green"} style={{ marginLeft: 8, fontSize: "11px" }}>
            {type}
          </Tag>
          {item.rowCount !== null && item.rowCount !== undefined && (
            <Tag style={{ marginLeft: 4, fontSize: "11px" }}>
              {item.rowCount} rows
            </Tag>
          )}
        </span>
      ),
      key: `${type}-${item.name}`,
      children: item.columns.map((col) => ({
        title: (
          <span style={{ fontSize: "14px" }}>
            <strong>{col.name}</strong>
            <Tag style={{ marginLeft: 8, fontSize: "10px" }}>
              {col.dataType}
            </Tag>
            {col.primaryKey && (
              <Tag color="red" style={{ marginLeft: 4, fontSize: "10px" }}>
                PK
              </Tag>
            )}
            {col.unique && (
              <Tag color="orange" style={{ marginLeft: 4, fontSize: "10px" }}>
                UNIQUE
              </Tag>
            )}
            {!col.nullable && (
              <Tag color="purple" style={{ marginLeft: 4, fontSize: "10px" }}>
                NOT NULL
              </Tag>
            )}
          </span>
        ),
        key: `${type}-${item.name}-${col.name}`,
        isLeaf: true,
      })),
    }));
  };

  const treeData = useMemo(
    () => [
      {
        title: `Tables (${filterItems(tables).length})`,
        key: "tables",
        children: buildTreeData(tables, "table"),
      },
      {
        title: `Views (${filterItems(views).length})`,
        key: "views",
        children: buildTreeData(views, "view"),
      },
    ],
    [tables, views, searchText]
  );

  return (
    <div style={{ height: "100%", overflow: "auto" }}>
      <Tree
        treeData={treeData}
        defaultExpandAll={true}
        showLine={{ showLeafIcon: false }}
        style={{ fontSize: "15px" }}
        className="metadata-tree"
      />
    </div>
  );
};
