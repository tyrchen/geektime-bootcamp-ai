/** Database detail page showing metadata. */

import { useEffect, useState } from "react";
import { Show, RefreshButton } from "@refinedev/antd";
import { useParams, useNavigate } from "react-router-dom";
import { Card, Spin, Button, Tag, Space } from "antd";
import { PlayCircleOutlined } from "@ant-design/icons";
import { apiClient } from "../../services/api";
import { DatabaseMetadata } from "../../types/metadata";
import { MetadataTree } from "../../components/MetadataTree";

export const DatabaseShow: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [metadata, setMetadata] = useState<DatabaseMetadata | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

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
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleRefresh = () => {
    setRefreshing(true);
    loadMetadata(true);
  };

  const handleExecuteQuery = () => {
    if (id) {
      navigate(`/queries/execute/${id}`);
    }
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

  return (
    <Show
      headerButtons={({ defaultButtons }) => (
        <>
          {defaultButtons}
          <Button
            type="primary"
            icon={<PlayCircleOutlined />}
            onClick={handleExecuteQuery}
          >
            Execute Query
          </Button>
          <RefreshButton onClick={handleRefresh} loading={refreshing} />
        </>
      )}
    >
      <Card title="Database Metadata" style={{ marginBottom: 16 }}>
        <Space direction="vertical" style={{ width: "100%" }}>
          <div>
            <strong>Database:</strong> {metadata.databaseName}
          </div>
          <div>
            <strong>Fetched At:</strong> {new Date(metadata.fetchedAt).toLocaleString()}
            {metadata.isStale && (
              <Tag color="orange" style={{ marginLeft: 8 }}>
                Stale
              </Tag>
            )}
          </div>
          <div>
            <strong>Tables:</strong> {metadata.tables.length} |{" "}
            <strong>Views:</strong> {metadata.views.length}
          </div>
        </Space>
      </Card>

      <Card title="Schema">
        <MetadataTree metadata={metadata} />
      </Card>
    </Show>
  );
};
