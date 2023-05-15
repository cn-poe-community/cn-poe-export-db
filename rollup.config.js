import terser from '@rollup/plugin-terser';

export default [
  {
    input: "src/index.js",
    output: {
      dir:"dist/",
      format: "esm"
    },
  },
  {
    input: "src/index.js",
    output: {
      file: "dist/db.global.js",
      format: "iife",
      name: "CnPoeExportDb"
    },
    plugins: [terser()],
  }
];
