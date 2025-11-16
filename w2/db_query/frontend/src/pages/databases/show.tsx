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

const { Title, Text } = Typography;

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
      title={`Query - ${metadata.databaseName}`}
      headerButtons={({ defaultButtons }) => (
        <>
          {defaultButtons}
          <RefreshButton onClick={handleRefresh} loading={refreshing} />
        </>
      )}
    >
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={8}>
          <Statistic
            title="Tables"
            value={metadata.tables.length}
            prefix={<TableOutlined />}
          />
        </Col>
        <Col span={8}>
          <Statistic
            title="Views"
            value={metadata.views.length}
            prefix={<DatabaseOutlined />}
          />
        </Col>
        <Col span={8}>
          <Statistic
            title="Total Rows"
            value={queryResult?.rowCount || 0}
          />
        </Col>
      </Row>

      <Row gutter={16}>
        <Col span={6}>
          <Card
            title="Database Schema"
            extra={
              <Input
                placeholder="Search tables..."
                prefix={<SearchOutlined />}
                value={searchText}
                onChange={(e) => setSearchText(e.target.value)}
                allowClear
                size="small"
              />
            }
            style={{ height: "calc(100vh - 280px)", overflow: "auto" }}
          >
            <MetadataTree
              metadata={metadata}
              searchText={searchText}
              onTableClick={handleTableClick}
            />
          </Card>
        </Col>

        <Col span={18}>
          <Space direction="vertical" style={{ width: "100%" }} size="middle">
            <Card
              title={
                <Space>
                  <Text>SQL Editor</Text>
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    Query executed at {queryResult ? new Date().toLocaleTimeString() : "-"}
                  </Text>
                </Space>
              }
              extra={
                <Button
                  type="primary"
                  icon={<PlayCircleOutlined />}
                  onClick={handleExecuteQuery}
                  loading={executing}
                >
                  Execute Query
                </Button>
              }
            >
              <SqlEditor
                value={sql}
                onChange={(value) => setSql(value || "")}
                height="200px"
              />
            </Card>

            {queryResult && (
              <Card
                title={
                  <Space>
                    <Text>Query Results</Text>
                    <Text type="secondary">
                      {queryResult.rowCount} rows in {queryResult.executionTimeMs}ms
                    </Text>
                  </Space>
                }
                extra={
                  <Space>
                    <Button size="small">Export CSV</Button>
                    <Button size="small">Export JSON</Button>
                  </Space>
                }
              >
                <Table
                  columns={tableColumns}
                  dataSource={queryResult.rows}
                  rowKey={(record, index) => index?.toString() || "0"}
                  pagination={{
                    pageSize: 50,
                    showSizeChanger: true,
                    showTotal: (total) => `Total ${total} rows`,
                  }}
                  scroll={{ x: "max-content", y: 400 }}
                  size="small"
                />
              </Card>
            )}
          </Space>
        </Col>
      </Row>
    </Show>
  );
};
