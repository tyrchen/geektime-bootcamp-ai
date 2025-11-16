/** Database create/edit form page. */

import React from "react";
import { Create, useForm } from "@refinedev/antd";
import { Form, Input } from "antd";
import { DatabaseConnectionInput } from "../../types/database";

export const DatabaseCreate: React.FC = () => {
  const { formProps, saveButtonProps } = useForm<DatabaseConnectionInput & { name: string }>({
    resource: "databases",
    action: "create",
  });

  return (
    <Create
      saveButtonProps={saveButtonProps}
      title="Add Database"
    >
      <Form {...formProps} layout="vertical">
        <Form.Item
          label="Name"
          name="name"
          rules={[
            { required: true, message: "Please enter database name" },
            {
              pattern: /^[a-zA-Z0-9-_]+$/,
              message: "Name must contain only alphanumeric characters, hyphens, and underscores",
            },
          ]}
        >
          <Input placeholder="my-database" />
        </Form.Item>
        <Form.Item
          label="Connection URL"
          name="url"
          rules={[
            { required: true, message: "Please enter connection URL" },
            {
              pattern: /^postgresql:\/\//,
              message: "URL must start with postgresql://",
            },
          ]}
        >
          <Input placeholder="postgresql://user:password@host:port/database" />
        </Form.Item>
        <Form.Item label="Description" name="description">
          <Input.TextArea rows={3} placeholder="Optional description" />
        </Form.Item>
      </Form>
    </Create>
  );
};
