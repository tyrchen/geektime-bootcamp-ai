/** Database detail page with integrated query interface. */

import { useEffect, useState } from "react";
import { Show, RefreshButton } from "@refinedev/antd";
import { useParams } from "react-router-dom";
import {
  Card,
  Spin,
  Button,
  Input,
  Space,
  Table,
  message,
  Row,
  Col,
  Statistic,
  Typography
} from "antd";
import {
  PlayCircleOutlined,
  SearchOutlined,
  TableOutlined,
  DatabaseOutlined
} from "@ant-design/icons";
import { apiClient } from "../../services/api";
import { DatabaseMetadata, TableMetadata } from "../../types/metadata";
import { MetadataTree } from "../../components/MetadataTree";
import { SqlEditor } from "../../components/SqlEditor";

const { Text } = Typography;

interface QueryResult {
  columns: Array<{ name: string; dataType: string }>;
  rows: Array<Record<string, any>>;
  rowCount: number;
  executionTimeMs: number;
  sql: string;
}

export const DatabaseShow: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [metadata, setMetadata] = useState<DatabaseMetadata | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [searchText, setSearchText] = useState("");
  const [sql, setSql] = useState("SELECT * FROM ");
  const [executing, setExecuting] = useState(false);
  const [queryResult, setQueryResult] = useState<QueryResult | null>(null);

  useEffect(() => {
    loadMetadata(false);
  }, [id]);

  const loadMetadata = async (forceRefresh: boolean) => {
    if (!id) return;

    setLoading(true);
    try {
      const response = await apiClient.get<DatabaseMetadata>(
        `/api/v1/dbs/${id}${forceRefresh ? "?refresh=true" : ""}`
      );
      setMetadata(response.data);
    } catch (error) {
      console.error("Failed to load metadata:", error);
      message.error("Failed to load database metadata");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleRefresh = () => {
    setRefreshing(true);
    loadMetadata(true);
  };

  const handleExecuteQuery = async () => {
    if (!id || !sql.trim()) {
      message.warning("Please enter a SQL query");
      return;
    }

    setExecuting(true);
    try {
      const response = await apiClient.post<QueryResult>(
        `/api/v1/dbs/${id}/query`,
        { sql: sql.trim() }
      );
      setQueryResult(response.data);
      message.success(`Query executed successfully - ${response.data.rowCount} rows in ${response.data.executionTimeMs}ms`);
    } catch (error: any) {
      message.error(error.response?.data?.detail || "Query execution failed");
      setQueryResult(null);
    } finally {
      setExecuting(false);
    }
  };

  const handleTableClick = (table: TableMetadata) => {
    setSql(`SELECT * FROM ${table.schemaName}.${table.name} LIMIT 100`);
  };

  if (loading) {
    return (
      <div style={{ textAlign: "center", padding: "50px" }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!metadata) {
    return <div>Failed to load metadata</div>;
  }

  const tableColumns = queryResult?.columns.map((col) => ({
    title: col.name,
    dataIndex: col.name,
    key: col.name,
    ellipsis: true,
  })) || [];

  return (
    <Show
      title={
        <Space>
          <DatabaseOutlined />
          <Text strong style={{ fontSize: 20 }}>
            {metadata.databaseName.toUpperCase()}
          </Text>
        </Space>
      }
      headerButtons={({ defaultButtons }) => (
        <>
          {defaultButtons}
          <RefreshButton onClick={handleRefresh} loading={refreshing} />
        </>
      )}
    >
      <Row gutter={24} style={{ marginBottom: 24 }}>
        <Col span={8}>
          <Card style={{ textAlign: "center", borderWidth: 2 }}>
            <Statistic
              title="TABLES"
              value={metadata.tables.length}
              prefix={<TableOutlined style={{ fontSize: 24 }} />}
              valueStyle={{ fontSize: 36, fontWeight: 700 }}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card style={{ textAlign: "center", borderWidth: 2 }}>
            <Statistic
              title="VIEWS"
              value={metadata.views.length}
              prefix={<DatabaseOutlined style={{ fontSize: 24 }} />}
              valueStyle={{ fontSize: 36, fontWeight: 700 }}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card style={{ textAlign: "center", borderWidth: 2 }}>
            <Statistic
              title="RESULT ROWS"
              value={queryResult?.rowCount || 0}
              valueStyle={{ fontSize: 36, fontWeight: 700, color: queryResult ? "#16AA98" : "#A1A1A1" }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={24}>
        <Col span={6}>
          <Card
            title="SCHEMA"
            extra={
              <Input
                placeholder="Search..."
                prefix={<SearchOutlined />}
                value={searchText}
                onChange={(e) => setSearchText(e.target.value)}
                allowClear
                size="middle"
                style={{ width: 140 }}
              />
            }
            style={{
              height: "calc(100vh - 340px)",
              borderWidth: 2,
            }}
            bodyStyle={{
              height: "calc(100% - 57px)",
              overflow: "auto",
              padding: "16px"
            }}
          >
            <MetadataTree
              metadata={metadata}
              searchText={searchText}
              onTableClick={handleTableClick}
            />
          </Card>
        </Col>

        <Col span={18}>
          <Space direction="vertical" style={{ width: "100%" }} size={24}>
            <Card
              title={
                <Space>
                  <Text strong style={{ fontSize: 14, textTransform: "uppercase", letterSpacing: "0.04em" }}>
                    SQL EDITOR
                  </Text>
                  {queryResult && (
                    <Text type="secondary" style={{ fontSize: 12, textTransform: "none" }}>
                      • Last executed: {new Date().toLocaleTimeString()}
                    </Text>
                  )}
                </Space>
              }
              extra={
                <Button
                  type="primary"
                  icon={<PlayCircleOutlined />}
                  onClick={handleExecuteQuery}
                  loading={executing}
                  size="large"
                  style={{
                    height: 44,
                    paddingLeft: 24,
                    paddingRight: 24,
                    fontWeight: 700,
                  }}
                >
                  EXECUTE
                </Button>
              }
              style={{ borderWidth: 2 }}
            >
              <SqlEditor
                value={sql}
                onChange={(value) => setSql(value || "")}
                height="240px"
              />
            </Card>

            {queryResult && (
              <Card
                title={
                  <Space>
                    <Text strong style={{ fontSize: 14, textTransform: "uppercase", letterSpacing: "0.04em" }}>
                      RESULTS
                    </Text>
                    <Text type="secondary">
                      • {queryResult.rowCount} rows • {queryResult.executionTimeMs}ms
                    </Text>
                  </Space>
                }
                extra={
                  <Space>
                    <Button size="middle">EXPORT CSV</Button>
                    <Button size="middle">EXPORT JSON</Button>
                  </Space>
                }
                style={{ borderWidth: 2 }}
              >
                <Table
                  columns={tableColumns}
                  dataSource={queryResult.rows}
                  rowKey={(_record, index) => index?.toString() || "0"}
                  pagination={{
                    pageSize: 50,
                    showSizeChanger: true,
                    showTotal: (total) => `Total ${total} rows`,
                    pageSizeOptions: [10, 20, 50, 100],
                  }}
                  scroll={{ x: "max-content", y: 450 }}
                  size="middle"
                  bordered
                />
              </Card>
            )}
          </Space>
        </Col>
      </Row>
    </Show>
  );
};
