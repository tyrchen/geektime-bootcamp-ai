import { Refine } from "@refinedev/core";
import {
  RefineThemes,
  ThemedLayout,
  ThemedSider,
  ThemedTitle,
} from "@refinedev/antd";
import { ConfigProvider, App as AntdApp } from "antd";
import routerProvider, {
  DocumentTitleHandler,
  UnsavedChangesNotifier,
} from "@refinedev/react-router";
import { BrowserRouter, Routes, Route, Outlet } from "react-router-dom";
import { dataProvider } from "./services/dataProvider";
import { DatabaseList } from "./pages/databases/list";
import { DatabaseCreate } from "./pages/databases/create";
import { DatabaseShow } from "./pages/databases/show";
import { QueryExecute } from "./pages/queries/execute";
import "@refinedev/antd/dist/reset.css";

function App() {
  return (
    <BrowserRouter>
      <ConfigProvider theme={RefineThemes.Blue}>
        <AntdApp>
          <Refine
              routerProvider={routerProvider}
              dataProvider={dataProvider}
              resources={[
                {
                  name: "databases",
                  list: "/databases",
                  create: "/databases/create",
                  show: "/databases/show/:id",
                  meta: {
                    label: "Databases",
                  },
                },
              ]}
              options={{
                syncWithLocation: true,
                warnWhenUnsavedChanges: true,
                projectId: "db-query-tool",
              }}
            >
              <Routes>
                <Route
                  element={
                    <ThemedLayout
                      Sider={(props: any) => <ThemedSider {...props} fixed />}
                      Title={({ collapsed }: { collapsed: boolean }) => (
                        <ThemedTitle
                          collapsed={collapsed}
                          text="DB Query Tool"
                        />
                      )}
                    >
                      <Outlet />
                    </ThemedLayout>
                  }
                >
                  <Route index element={<DatabaseList />} />
                  <Route path="/databases">
                    <Route index element={<DatabaseList />} />
                    <Route path="create" element={<DatabaseCreate />} />
                    <Route path="show/:id" element={<DatabaseShow />} />
                  </Route>
                  <Route path="/queries">
                    <Route path="execute/:databaseName" element={<QueryExecute />} />
                  </Route>
                </Route>
              </Routes>
              <UnsavedChangesNotifier />
              <DocumentTitleHandler />
            </Refine>
        </AntdApp>
      </ConfigProvider>
    </BrowserRouter>
  );
}

export default App;
