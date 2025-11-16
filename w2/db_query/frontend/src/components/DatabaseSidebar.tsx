/** Custom sidebar for database management. */

import React, { useState, useEffect } from "react";
import {
  Button,
  List,
  Space,
  Typography,
  Input,
  Modal,
  Form,
  message,
  Popconfirm,
} from "antd";
import {
  PlusOutlined,
  DatabaseOutlined,
  DeleteOutlined,
  CheckCircleFilled,
  ExclamationCircleFilled,
} from "@ant-design/icons";
import { apiClient } from "../services/api";

const { Title, Text } = Typography;

interface Database {
  name: string;
  url: string;
  description?: string;
  status: string;
}

interface DatabaseSidebarProps {
  selectedDatabase: string | null;
  onSelectDatabase: (dbName: string) => void;
}

export const DatabaseSidebar: React.FC<DatabaseSidebarProps> = ({
  selectedDatabase,
  onSelectDatabase,
}) => {
  const [databases, setDatabases] = useState<Database[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [form] = Form.useForm();

  useEffect(() => {
    loadDatabases();
  }, []);

  const loadDatabases = async () => {
    setLoading(true);
    try {
      const response = await apiClient.get<Database[]>("/api/v1/dbs");
      setDatabases(response.data);

      // Auto-select first database if none selected
      if (!selectedDatabase && response.data.length > 0) {
        onSelectDatabase(response.data[0]?.name || "");
      }
    } catch (error) {
      message.error("Failed to load databases");
    } finally {
      setLoading(false);
    }
  };

  const handleAddDatabase = async (values: any) => {
    try {
      await apiClient.put(`/api/v1/dbs/${values.name}`, {
        url: values.url,
        description: values.description,
      });
      message.success("Database added successfully");
      setModalOpen(false);
      form.resetFields();
      loadDatabases();
    } catch (error: any) {
      message.error(error.response?.data?.detail || "Failed to add database");
    }
  };

  const handleDeleteDatabase = async (dbName: string) => {
    try {
      await apiClient.delete(`/api/v1/dbs/${dbName}`);
      message.success("Database deleted successfully");
      if (selectedDatabase === dbName) {
        const remaining = databases.filter((db) => db.name !== dbName);
        onSelectDatabase(remaining.length > 0 ? remaining[0]?.name || "" : "");
      }
      loadDatabases();
    } catch (error: any) {
      message.error(error.response?.data?.detail || "Failed to delete database");
    }
  };

  return (
    <div
      style={{
        width: 280,
        height: "100vh",
        background: "#FFFFFF",
        borderRight: "2px solid #000000",
        borderTop: "3px solid #000000",
        display: "flex",
        flexDirection: "column",
        position: "fixed",
        left: 0,
        top: 0,
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: "24px 20px",
          borderBottom: "2px solid #000000",
          background: "#F4EFEA",
        }}
      >
        <Space direction="vertical" size={12} style={{ width: "100%" }}>
          <Space>
            <DatabaseOutlined style={{ fontSize: 24 }} />
            <Title
              level={4}
              style={{
                margin: 0,
                textTransform: "uppercase",
                letterSpacing: "0.04em",
                fontSize: 16,
              }}
            >
              DB QUERY TOOL
            </Title>
          </Space>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setModalOpen(true)}
            block
            style={{
              height: 44,
              fontWeight: 700,
              fontSize: 13,
            }}
          >
            ADD DATABASE
          </Button>
        </Space>
      </div>

      {/* Database List */}
      <div style={{ flex: 1, overflow: "auto", padding: "16px 12px" }}>
        <List
          loading={loading}
          dataSource={databases}
          renderItem={(db) => (
            <List.Item
              style={{
                padding: "12px",
                marginBottom: 8,
                border: "2px solid #000000",
                borderRadius: 2,
                background:
                  selectedDatabase === db.name ? "#EBF9FF" : "#FFFFFF",
                cursor: "pointer",
                transition: "all 120ms ease-in-out",
              }}
              onClick={() => onSelectDatabase(db.name)}
              onMouseEnter={(e) => {
                if (selectedDatabase !== db.name) {
                  e.currentTarget.style.background = "#F8F8F7";
                }
              }}
              onMouseLeave={(e) => {
                if (selectedDatabase !== db.name) {
                  e.currentTarget.style.background = "#FFFFFF";
                }
              }}
            >
              <Space
                direction="vertical"
                size={4}
                style={{ width: "100%", userSelect: "none" }}
              >
                <Space style={{ width: "100%", justifyContent: "space-between" }}>
                  <Space>
                    {db.status === "active" ? (
                      <CheckCircleFilled style={{ color: "#16AA98", fontSize: 14 }} />
                    ) : (
                      <ExclamationCircleFilled style={{ color: "#FF7169", fontSize: 14 }} />
                    )}
                    <Text
                      strong
                      style={{
                        fontSize: 15,
                        textTransform: "uppercase",
                        letterSpacing: "0.02em",
                      }}
                    >
                      {db.name}
                    </Text>
                  </Space>
                  <Popconfirm
                    title="Delete Database"
                    description="Are you sure to delete this database connection?"
                    onConfirm={(e) => {
                      e?.stopPropagation();
                      handleDeleteDatabase(db.name);
                    }}
                    onCancel={(e) => e?.stopPropagation()}
                    okText="Yes"
                    cancelText="No"
                  >
                    <Button
                      type="text"
                      size="small"
                      icon={<DeleteOutlined />}
                      onClick={(e) => e.stopPropagation()}
                      danger
                      style={{ padding: "4px 8px" }}
                    />
                  </Popconfirm>
                </Space>
                {db.description && (
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    {db.description}
                  </Text>
                )}
              </Space>
            </List.Item>
          )}
        />
      </div>

      {/* Add Database Modal */}
      <Modal
        title={
          <Text strong style={{ fontSize: 16, textTransform: "uppercase" }}>
            ADD NEW DATABASE
          </Text>
        }
        open={modalOpen}
        onCancel={() => {
          setModalOpen(false);
          form.resetFields();
        }}
        footer={null}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleAddDatabase}
          style={{ marginTop: 24 }}
        >
          <Form.Item
            label="Database Name"
            name="name"
            rules={[
              { required: true, message: "Please enter database name" },
              {
                pattern: /^[a-zA-Z0-9_-]+$/,
                message: "Only letters, numbers, dash and underscore allowed",
              },
            ]}
          >
            <Input placeholder="e.g., my-database" size="large" />
          </Form.Item>

          <Form.Item
            label="Connection URL"
            name="url"
            rules={[
              { required: true, message: "Please enter connection URL" },
              {
                pattern: /^postgresql:\/\/.+/,
                message: "Must be a valid PostgreSQL URL",
              },
            ]}
          >
            <Input
              placeholder="postgresql://user:password@host:5432/dbname"
              size="large"
            />
          </Form.Item>

          <Form.Item label="Description (optional)" name="description">
            <Input.TextArea
              placeholder="Brief description of this database"
              rows={3}
              maxLength={200}
            />
          </Form.Item>

          <Form.Item style={{ marginBottom: 0 }}>
            <Space style={{ width: "100%", justifyContent: "flex-end" }}>
              <Button onClick={() => setModalOpen(false)}>CANCEL</Button>
              <Button type="primary" htmlType="submit" size="large">
                ADD DATABASE
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};
