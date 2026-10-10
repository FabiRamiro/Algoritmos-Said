import fs from 'node:fs/promises';
import {FileBlob,SpreadsheetFile} from '@oai/artifact-tool';
const wb=await SpreadsheetFile.importXlsx(await FileBlob.load('outputs/floyd_positivo/floyd_warshall.xlsx'));
const png=await wb.render({sheetName:'Resultado',range:'A7:AE18',scale:1,format:'png'});
await fs.writeFile('tmp/grafos_20261009/floyd_resultado.png',new Uint8Array(await png.arrayBuffer()));
