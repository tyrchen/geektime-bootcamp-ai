/** Monaco-based SQL editor component. */

import { useRef } from "react";
import Editor, { type Monaco } from "@monaco-editor/react";
import type { editor } from "monaco-editor";

interface SqlEditorProps {
  value: string;
  onChange?: (value: string | undefined) => void;
  height?: string;
  readOnly?: boolean;
}

export const SqlEditor: React.FC<SqlEditorProps> = ({
  value,
  onChange,
  height = "300px",
  readOnly = false,
}) => {
  const editorRef = useRef<editor.IStandaloneCodeEditor | null>(null);
  const monacoRef = useRef<Monaco | null>(null);

  const handleEditorDidMount = (
    editor: editor.IStandaloneCodeEditor,
    monaco: Monaco
  ) => {
    editorRef.current = editor;
    monacoRef.current = monaco;

    // Configure SQL language features
    monaco.languages.setLanguageConfiguration("sql", {
      comments: {
        lineComment: "--",
        blockComment: ["/*", "*/"],
      },
      brackets: [
        ["{", "}"],
        ["[", "]"],
        ["(", ")"],
      ],
      autoClosingPairs: [
        { open: "{", close: "}" },
        { open: "[", close: "]" },
        { open: "(", close: ")" },
        { open: '"', close: '"' },
        { open: "'", close: "'" },
      ],
      surroundingPairs: [
        { open: "{", close: "}" },
        { open: "[", close: "]" },
        { open: "(", close: ")" },
        { open: '"', close: '"' },
        { open: "'", close: "'" },
      ],
    });

    // Add SQL keywords
    monaco.languages.setMonarchTokensProvider("sql", {
      keywords: [
        "SELECT",
        "FROM",
        "WHERE",
        "JOIN",
        "INNER",
        "LEFT",
        "RIGHT",
        "OUTER",
        "ON",
        "AS",
        "AND",
        "OR",
        "NOT",
        "IN",
        "LIKE",
        "BETWEEN",
        "IS",
        "NULL",
        "ORDER",
        "BY",
        "GROUP",
        "HAVING",
        "LIMIT",
        "OFFSET",
        "DISTINCT",
        "COUNT",
        "SUM",
        "AVG",
        "MAX",
        "MIN",
        "CASE",
        "WHEN",
        "THEN",
        "ELSE",
        "END",
      ],
      operators: [
        "=",
        ">",
        "<",
        "!",
        "~",
        "?",
        ":",
        "==",
        "<=",
        ">=",
        "!=",
        "&&",
        "||",
        "++",
        "--",
        "+",
        "-",
        "*",
        "/",
        "&",
        "|",
        "^",
        "%",
        "<<",
        ">>",
        ">>>",
        "+=",
        "-=",
        "*=",
        "/=",
        "&=",
        "|=",
        "^=",
        "%=",
        "<<=",
        ">>=",
        ">>>=",
      ],
      tokenizer: {
        root: [
          [
            /[a-z_$][\w$]*/,
            {
              cases: {
                "@keywords": "keyword",
                "@default": "identifier",
              },
            },
          ],
          [/[ \t\r\n]+/, "white"],
          [/--.*$/, "comment"],
          [/\/\*/, "comment", "@comment"],
          [/[=><!~?&|+\-*\/%^]/, "operator"],
          [/["']/, "string", "@string"],
          [/\d*\.\d+([eE][\-+]?\d+)?/, "number.float"],
          [/0[xX][0-9a-fA-F]+/, "number.hex"],
          [/\d+/, "number"],
        ],
        comment: [
          [/[^/*]+/, "comment"],
          [/\/\*/, "comment", "@push"],
          [/\*\//, "comment", "@pop"],
          [/[/*]/, "comment"],
        ],
        string: [
          [/[^\\"']+/, "string"],
          [/\\./, "string.escape.invalid"],
          [/"'/, "string", "@pop"],
        ],
      },
    });
  };

  return (
    <Editor
      height={height}
      defaultLanguage="sql"
      value={value}
      onChange={onChange}
      theme="vs-dark"
      options={{
        readOnly,
        minimap: { enabled: false },
        scrollBeyondLastLine: false,
        fontSize: 16,
        lineNumbers: "on",
        roundedSelection: false,
        cursorStyle: "line",
        automaticLayout: true,
        tabSize: 2,
        wordWrap: "on",
        lineHeight: 24,
      }}
      onMount={handleEditorDidMount}
    />
  );
};
