import fs from "node:fs";

const sourcePath = "dist/";
const destinationPath = "../backend/static/";
fs.cp(sourcePath, destinationPath, { recursive: true }, (err) => {
  console.error(err);
});
